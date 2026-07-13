from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.organizations.models import OrganizationMember


async def _register(client: AsyncClient, email: str) -> dict:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "SuperSecret123", "display_name": "Test User"},
    )
    assert response.status_code == 201
    return response.json()


async def _auth_headers(client: AsyncClient, email: str) -> dict[str, str]:
    tokens = await _register(client, email=email)
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def _send_chat_message(client: AsyncClient, headers: dict[str, str], message: str):
    return await client.post("/api/v1/ai/chat", headers=headers, json={"message": message})


async def _create_call_conversation(client: AsyncClient, headers: dict[str, str], text: str) -> str:
    response = await client.post(
        "/api/v1/calls/text",
        headers=headers,
        json={"title": "Billing Test Conversation", "transcript_text": text},
    )
    assert response.status_code == 201
    return response.json()["conversation"]["id"]


async def test_new_tenant_gets_free_plan_and_quota_is_enforced(client: AsyncClient):
    headers = await _auth_headers(client, "billing-quota@example.com")

    subscription = await client.get("/api/v1/billing/subscription", headers=headers)
    assert subscription.status_code == 200
    body = subscription.json()
    assert body["plan"]["code"] == "free"

    usage = await client.get("/api/v1/billing/usage", headers=headers)
    assert usage.status_code == 200
    assert usage.json()["limit_value"] == 5
    assert usage.json()["used"] == 0

    for index in range(5):
        response = await _send_chat_message(client, headers, f"Question number {index}")
        assert response.status_code == 201

    blocked = await _send_chat_message(client, headers, "One too many")
    assert blocked.status_code == 429
    assert blocked.json()["error_code"] == "quota_exceeded"

    usage_after = await client.get("/api/v1/billing/usage", headers=headers)
    assert usage_after.json()["used"] == 5
    assert usage_after.json()["remaining"] == 0


async def test_conversation_analysis_shares_the_same_ai_quota(client: AsyncClient):
    headers = await _auth_headers(client, "billing-shared-quota@example.com")

    for index in range(5):
        response = await _send_chat_message(client, headers, f"Chat message {index}")
        assert response.status_code == 201

    conversation_id = await _create_call_conversation(
        client, headers, "This call should be blocked by the shared quota."
    )
    analysis_response = await client.post(
        f"/api/v1/ai/analysis/conversations/{conversation_id}", headers=headers
    )
    assert analysis_response.status_code == 429
    assert analysis_response.json()["error_code"] == "quota_exceeded"


async def test_plan_switch_raises_limit_and_allows_more_usage(client: AsyncClient):
    headers = await _auth_headers(client, "billing-plan-switch@example.com")

    plans_response = await client.get("/api/v1/billing/plans", headers=headers)
    assert plans_response.status_code == 200
    plan_codes = {plan["code"] for plan in plans_response.json()}
    assert plan_codes == {"free", "pro", "enterprise"}

    for index in range(5):
        response = await _send_chat_message(client, headers, f"Chat message {index}")
        assert response.status_code == 201

    blocked = await _send_chat_message(client, headers, "Blocked before switching plans")
    assert blocked.status_code == 429

    switch_response = await client.patch(
        "/api/v1/billing/subscription", headers=headers, json={"plan_code": "pro"}
    )
    assert switch_response.status_code == 200
    assert switch_response.json()["plan"]["code"] == "pro"

    subscription_response = await client.get("/api/v1/billing/subscription", headers=headers)
    assert subscription_response.json()["plan"]["code"] == "pro"

    usage_response = await client.get("/api/v1/billing/usage", headers=headers)
    assert usage_response.json()["limit_value"] == 50
    assert usage_response.json()["used"] == 5

    allowed = await _send_chat_message(client, headers, "Now allowed under the Pro plan")
    assert allowed.status_code == 201


async def test_plans_expose_price_and_billing_period_as_payment_skeleton(client: AsyncClient):
    headers = await _auth_headers(client, "billing-payment-skeleton@example.com")

    response = await client.get("/api/v1/billing/plans", headers=headers)
    assert response.status_code == 200
    for plan in response.json():
        assert "price" in plan
        assert "billing_period" in plan
        assert isinstance(plan["price"], (int, float))


async def test_billing_usage_is_tenant_scoped(client: AsyncClient):
    first_headers = await _auth_headers(client, "billing-tenant-one@example.com")
    second_headers = await _auth_headers(client, "billing-tenant-two@example.com")

    for index in range(3):
        response = await _send_chat_message(client, first_headers, f"Tenant one message {index}")
        assert response.status_code == 201

    first_usage = await client.get("/api/v1/billing/usage", headers=first_headers)
    second_usage = await client.get("/api/v1/billing/usage", headers=second_headers)

    assert first_usage.json()["used"] == 3
    assert second_usage.json()["used"] == 0


async def test_viewer_can_read_billing_but_not_switch_plan(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_headers(client, "billing-viewer@example.com")
    me_response = await client.get("/api/v1/users/me", headers=headers)
    user_id = me_response.json()["id"]

    await db_session.execute(
        update(OrganizationMember).where(OrganizationMember.user_id == user_id).values(role="viewer")
    )
    await db_session.flush()

    read_response = await client.get("/api/v1/billing/subscription", headers=headers)
    assert read_response.status_code == 200

    switch_response = await client.patch(
        "/api/v1/billing/subscription", headers=headers, json={"plan_code": "pro"}
    )
    assert switch_response.status_code == 403
