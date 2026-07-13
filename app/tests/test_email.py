from httpx import AsyncClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import decrypt_token
from app.modules.email.models import EmailToken
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


async def _start_connect(
    client: AsyncClient, headers: dict[str, str], provider: str = "gmail"
) -> dict:
    response = await client.post(f"/api/v1/email/{provider}/connect", headers=headers)
    assert response.status_code == 200
    return response.json()


async def _complete_connect(
    client: AsyncClient, state: str, code: str = "mock-code", provider: str = "gmail"
) -> dict:
    response = await client.get(
        f"/api/v1/email/{provider}/callback", params={"code": code, "state": state}
    )
    assert response.status_code == 200
    return response.json()


async def _connect(client: AsyncClient, headers: dict[str, str], provider: str = "gmail") -> dict:
    start = await _start_connect(client, headers, provider=provider)
    return await _complete_connect(client, start["state"], provider=provider)


async def test_connect_returns_minimal_scope_authorize_url_and_state(client: AsyncClient):
    headers = await _auth_headers(client, "email-connect@example.com")
    start = await _start_connect(client, headers)

    assert "gmail.readonly" in start["authorize_url"]
    assert "gmail.send" not in start["authorize_url"]
    assert "gmail.modify" not in start["authorize_url"]
    assert start["state"]


async def test_callback_with_invalid_state_is_rejected(client: AsyncClient):
    response = await client.get(
        "/api/v1/email/gmail/callback", params={"code": "mock-code", "state": "bogus-state"}
    )
    assert response.status_code == 401


async def test_callback_state_is_single_use(client: AsyncClient):
    headers = await _auth_headers(client, "email-state-replay@example.com")
    start = await _start_connect(client, headers)

    first = await client.get(
        "/api/v1/email/gmail/callback", params={"code": "mock-code", "state": start["state"]}
    )
    assert first.status_code == 200

    replay = await client.get(
        "/api/v1/email/gmail/callback", params={"code": "mock-code", "state": start["state"]}
    )
    assert replay.status_code == 401


async def test_callback_success_encrypts_tokens_at_rest(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_headers(client, "email-encryption@example.com")
    account = await _connect(client, headers)

    result = await db_session.execute(
        select(EmailToken).where(EmailToken.email_account_id == account["id"])
    )
    token_row = result.scalar_one()
    assert token_row.refresh_token_encrypted is not None

    assert not token_row.access_token_encrypted.startswith("mock-access-")
    assert not token_row.refresh_token_encrypted.startswith("mock-refresh-")

    assert decrypt_token(token_row.access_token_encrypted).startswith("mock-access-")
    assert decrypt_token(token_row.refresh_token_encrypted).startswith("mock-refresh-")


async def test_connect_records_consent(client: AsyncClient):
    headers = await _auth_headers(client, "email-consent@example.com")
    account = await _connect(client, headers)

    assert account["status"] == "connected"
    assert account["consent_granted_at"] is not None
    assert account["consent_scope"] == "https://www.googleapis.com/auth/gmail.readonly"


async def test_revoke_stops_further_sync_and_deletes_tokens(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_headers(client, "email-revoke@example.com")
    account = await _connect(client, headers)

    revoke_response = await client.post(
        f"/api/v1/email/accounts/{account['id']}/revoke", headers=headers
    )
    assert revoke_response.status_code == 200
    assert revoke_response.json()["status"] == "revoked"

    sync_response = await client.post(
        f"/api/v1/email/accounts/{account['id']}/sync", headers=headers
    )
    assert sync_response.status_code == 422

    result = await db_session.execute(
        select(EmailToken).where(EmailToken.email_account_id == account["id"])
    )
    assert result.scalar_one_or_none() is None


async def test_sync_dedups_messages_on_repeat_calls(client: AsyncClient):
    headers = await _auth_headers(client, "email-sync-dedup@example.com")
    account = await _connect(client, headers)

    first_sync = await client.post(
        f"/api/v1/email/accounts/{account['id']}/sync", headers=headers
    )
    assert first_sync.status_code == 200
    assert first_sync.json()["created"] > 0
    assert first_sync.json()["skipped"] == 0

    second_sync = await client.post(
        f"/api/v1/email/accounts/{account['id']}/sync", headers=headers
    )
    assert second_sync.status_code == 200
    assert second_sync.json()["created"] == 0
    assert second_sync.json()["skipped"] == first_sync.json()["fetched"]

    messages_response = await client.get(
        f"/api/v1/email/accounts/{account['id']}/messages", headers=headers
    )
    assert messages_response.status_code == 200
    assert len(messages_response.json()) == first_sync.json()["fetched"]


async def test_sync_populates_message_body(client: AsyncClient):
    headers = await _auth_headers(client, "email-body@example.com")
    account = await _connect(client, headers)

    sync_response = await client.post(
        f"/api/v1/email/accounts/{account['id']}/sync", headers=headers
    )
    assert sync_response.status_code == 200

    messages_response = await client.get(
        f"/api/v1/email/accounts/{account['id']}/messages", headers=headers
    )
    assert messages_response.status_code == 200
    messages = messages_response.json()
    assert messages
    for message in messages:
        assert message["body"]
        assert len(message["body"]) > len(message["snippet"])


async def test_sync_is_rate_limited(client: AsyncClient):
    headers = await _auth_headers(client, "email-rate-limit@example.com")
    account = await _connect(client, headers)

    for _ in range(5):
        response = await client.post(
            f"/api/v1/email/accounts/{account['id']}/sync", headers=headers
        )
        assert response.status_code == 200

    limited_response = await client.post(
        f"/api/v1/email/accounts/{account['id']}/sync", headers=headers
    )
    assert limited_response.status_code == 429


async def test_email_accounts_are_tenant_scoped(client: AsyncClient):
    first_headers = await _auth_headers(client, "email-tenant-one@example.com")
    second_headers = await _auth_headers(client, "email-tenant-two@example.com")

    first_account = await _connect(client, first_headers)
    await _connect(client, second_headers)

    list_response = await client.get("/api/v1/email/accounts", headers=first_headers)
    assert list_response.status_code == 200
    account_ids = {item["id"] for item in list_response.json()}
    assert account_ids == {first_account["id"]}


async def test_viewer_cannot_start_gmail_connect(client: AsyncClient, db_session: AsyncSession):
    headers = await _auth_headers(client, "email-viewer@example.com")
    me_response = await client.get("/api/v1/users/me", headers=headers)
    user_id = me_response.json()["id"]

    await db_session.execute(
        update(OrganizationMember)
        .where(OrganizationMember.user_id == user_id)
        .values(role="viewer")
    )
    await db_session.flush()

    response = await client.post("/api/v1/email/gmail/connect", headers=headers)
    assert response.status_code == 403


async def test_outlook_connect_returns_minimal_graph_scope_authorize_url(client: AsyncClient):
    headers = await _auth_headers(client, "email-outlook-connect@example.com")
    start = await _start_connect(client, headers, provider="outlook")

    assert "graph.microsoft.com" in start["authorize_url"]
    assert "Mail.Read" in start["authorize_url"]
    assert "offline_access" in start["authorize_url"]
    assert "Mail.Send" not in start["authorize_url"]


async def test_outlook_full_connect_sync_and_messages_flow(client: AsyncClient):
    headers = await _auth_headers(client, "email-outlook-flow@example.com")
    account = await _connect(client, headers, provider="outlook")

    assert account["provider"] == "outlook"
    assert account["status"] == "connected"
    assert account["consent_scope"] == "https://graph.microsoft.com/Mail.Read offline_access"

    sync_response = await client.post(
        f"/api/v1/email/accounts/{account['id']}/sync", headers=headers
    )
    assert sync_response.status_code == 200
    assert sync_response.json()["created"] > 0

    messages_response = await client.get(
        f"/api/v1/email/accounts/{account['id']}/messages", headers=headers
    )
    assert messages_response.status_code == 200
    assert messages_response.json()[0]["subject"].startswith("Mock Outlook subject")


async def test_gmail_callback_rejects_mock_fail_code(client: AsyncClient):
    headers = await _auth_headers(client, "email-gmail-mockfail@example.com")
    start = await _start_connect(client, headers, provider="gmail")

    response = await client.get(
        "/api/v1/email/gmail/callback",
        params={"code": "[mock-fail]", "state": start["state"]},
    )
    assert response.status_code >= 400


async def test_outlook_callback_rejects_mock_fail_code(client: AsyncClient):
    headers = await _auth_headers(client, "email-outlook-mockfail@example.com")
    start = await _start_connect(client, headers, provider="outlook")

    response = await client.get(
        "/api/v1/email/outlook/callback",
        params={"code": "[mock-fail]", "state": start["state"]},
    )
    assert response.status_code >= 400


async def test_refresh_token_rotates_encrypted_tokens(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_headers(client, "email-refresh@example.com")
    account = await _connect(client, headers, provider="outlook")

    result = await db_session.execute(
        select(EmailToken).where(EmailToken.email_account_id == account["id"])
    )
    original_access = result.scalar_one().access_token_encrypted

    refresh_response = await client.post(
        f"/api/v1/email/accounts/{account['id']}/refresh-token", headers=headers
    )
    assert refresh_response.status_code == 200

    result = await db_session.execute(
        select(EmailToken).where(EmailToken.email_account_id == account["id"])
    )
    refreshed_row = result.scalar_one()
    assert refreshed_row.access_token_encrypted != original_access
    assert decrypt_token(refreshed_row.access_token_encrypted).startswith(
        "mock-graph-access-refreshed-"
    )


async def test_refresh_token_requires_connected_account(client: AsyncClient):
    headers = await _auth_headers(client, "email-refresh-revoked@example.com")
    account = await _connect(client, headers, provider="gmail")

    await client.post(f"/api/v1/email/accounts/{account['id']}/revoke", headers=headers)

    response = await client.post(
        f"/api/v1/email/accounts/{account['id']}/refresh-token", headers=headers
    )
    assert response.status_code == 422


async def test_email_sync_rate_limits_are_isolated_per_provider(client: AsyncClient):
    headers = await _auth_headers(client, "email-rate-per-provider@example.com")
    gmail_account = await _connect(client, headers, provider="gmail")
    outlook_account = await _connect(client, headers, provider="outlook")

    for _ in range(5):
        response = await client.post(
            f"/api/v1/email/accounts/{gmail_account['id']}/sync", headers=headers
        )
        assert response.status_code == 200

    exhausted_response = await client.post(
        f"/api/v1/email/accounts/{gmail_account['id']}/sync", headers=headers
    )
    assert exhausted_response.status_code == 429

    outlook_response = await client.post(
        f"/api/v1/email/accounts/{outlook_account['id']}/sync", headers=headers
    )
    assert outlook_response.status_code == 200
