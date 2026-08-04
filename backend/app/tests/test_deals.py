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


async def _create_contact(client: AsyncClient, headers: dict[str, str]) -> dict:
    response = await client.post(
        "/api/v1/contacts", headers=headers, json={"full_name": "Ada Lovelace"}
    )
    assert response.status_code == 201
    return response.json()


async def _create_deal(client: AsyncClient, headers: dict[str, str], **overrides) -> dict:
    body = {"title": "Deal", "value": 1000, "currency": "TRY", "stage": "lead"}
    body.update(overrides)
    response = await client.post("/api/v1/deals", headers=headers, json=body)
    assert response.status_code == 201
    return response.json()


async def test_pipeline_report_groups_by_stage_currency_and_month(client: AsyncClient):
    headers = await _auth_headers(client, "deal-pipeline-report@example.com")

    await _create_deal(client, headers, title="Lead A", value=1000, currency="TRY", stage="lead")
    await _create_deal(client, headers, title="Lead B", value=500, currency="TRY", stage="lead")
    await _create_deal(
        client,
        headers,
        title="Negotiation USD",
        value=200,
        currency="USD",
        stage="negotiation",
        expected_close_date="2026-09-15T00:00:00Z",
    )
    await _create_deal(
        client,
        headers,
        title="Won deal",
        value=999,
        currency="TRY",
        stage="won",
        expected_close_date="2026-09-20T00:00:00Z",
    )

    response = await client.get("/api/v1/deals/pipeline-report", headers=headers)
    assert response.status_code == 200
    body = response.json()

    assert set(body["open_stages"]) == {"lead", "proposal_sent", "negotiation", "invoiced"}

    lead_try = next(
        row for row in body["by_stage"] if row["stage"] == "lead" and row["currency"] == "TRY"
    )
    assert lead_try["total_value"] == 1500
    assert lead_try["deal_count"] == 2

    negotiation_usd = next(
        row for row in body["by_stage"] if row["stage"] == "negotiation" and row["currency"] == "USD"
    )
    assert negotiation_usd["total_value"] == 200
    assert negotiation_usd["deal_count"] == 1

    # "won" is a terminal stage, not in open_stages, so it must not appear in the
    # expected-close-month forecast even though it has an expected_close_date.
    assert all(row["currency"] != "TRY" or row["total_value"] != 999 for row in body["by_expected_month"])

    september_usd = next(row for row in body["by_expected_month"] if row["month"] == "2026-09")
    assert september_usd["currency"] == "USD"
    assert september_usd["total_value"] == 200


async def test_deal_crud_and_soft_delete(client: AsyncClient):
    headers = await _auth_headers(client, "deal-crud@example.com")
    contact = await _create_contact(client, headers)

    create_response = await client.post(
        "/api/v1/deals",
        headers=headers,
        json={
            "title": "Annual license renewal",
            "value": 5000,
            "currency": "USD",
            "stage": "proposal_sent",
            "contact_id": contact["id"],
        },
    )
    assert create_response.status_code == 201
    deal = create_response.json()
    assert deal["title"] == "Annual license renewal"
    assert deal["stage"] == "proposal_sent"
    assert deal["currency"] == "USD"
    assert deal["contact_id"] == contact["id"]
    assert deal["source_type"] == "manual"

    list_response = await client.get("/api/v1/deals", headers=headers)
    assert list_response.status_code == 200
    assert deal["id"] in {item["id"] for item in list_response.json()}

    stage_filter_response = await client.get(
        "/api/v1/deals", headers=headers, params={"stage": "proposal_sent"}
    )
    assert [d["id"] for d in stage_filter_response.json()] == [deal["id"]]

    update_response = await client.patch(
        f"/api/v1/deals/{deal['id']}", headers=headers, json={"stage": "won", "value": 5500}
    )
    assert update_response.status_code == 200
    assert update_response.json()["stage"] == "won"
    assert update_response.json()["value"] == 5500

    delete_response = await client.delete(f"/api/v1/deals/{deal['id']}", headers=headers)
    assert delete_response.status_code == 204

    get_response = await client.get(f"/api/v1/deals/{deal['id']}", headers=headers)
    assert get_response.status_code == 404


async def test_deal_rejects_invalid_stage(client: AsyncClient):
    headers = await _auth_headers(client, "deal-invalid-stage@example.com")
    response = await client.post(
        "/api/v1/deals", headers=headers, json={"title": "Bad stage deal", "stage": "not-a-stage"}
    )
    assert response.status_code == 422


async def test_deal_rejects_nonexistent_contact(client: AsyncClient):
    headers = await _auth_headers(client, "deal-bad-contact@example.com")
    response = await client.post(
        "/api/v1/deals",
        headers=headers,
        json={"title": "Orphan deal", "contact_id": "11111111-1111-1111-1111-111111111111"},
    )
    assert response.status_code == 404


async def test_deal_is_tenant_scoped(client: AsyncClient):
    first_headers = await _auth_headers(client, "deal-tenant-one@example.com")
    second_headers = await _auth_headers(client, "deal-tenant-two@example.com")
    create_response = await client.post(
        "/api/v1/deals", headers=first_headers, json={"title": "Tenant one deal"}
    )
    deal_id = create_response.json()["id"]

    cross_tenant_response = await client.get(f"/api/v1/deals/{deal_id}", headers=second_headers)
    assert cross_tenant_response.status_code == 404


async def test_viewer_cannot_create_deal(client: AsyncClient, db_session: AsyncSession):
    headers = await _auth_headers(client, "deal-viewer@example.com")
    me_response = await client.get("/api/v1/users/me", headers=headers)
    user_id = me_response.json()["id"]

    await db_session.execute(
        update(OrganizationMember).where(OrganizationMember.user_id == user_id).values(role="viewer")
    )
    await db_session.flush()

    read_response = await client.get("/api/v1/deals", headers=headers)
    assert read_response.status_code == 200

    create_response = await client.post(
        "/api/v1/deals", headers=headers, json={"title": "Viewer attempted deal"}
    )
    assert create_response.status_code == 403


async def test_line_item_crud_syncs_deal_value(client: AsyncClient):
    headers = await _auth_headers(client, "deal-line-items@example.com")
    deal = await _create_deal(client, headers, title="Deal with items", value=None)

    create_response = await client.post(
        f"/api/v1/deals/{deal['id']}/line-items",
        headers=headers,
        json={"product_name": "Lisans", "quantity": 2, "unit_price": 100},
    )
    assert create_response.status_code == 201
    item = create_response.json()
    assert item["line_total"] == 200

    second_response = await client.post(
        f"/api/v1/deals/{deal['id']}/line-items",
        headers=headers,
        json={"product_name": "Kurulum", "quantity": 1, "unit_price": 50},
    )
    assert second_response.status_code == 201

    deal_after_create = await client.get(f"/api/v1/deals/{deal['id']}", headers=headers)
    assert deal_after_create.json()["value"] == 250

    list_response = await client.get(f"/api/v1/deals/{deal['id']}/line-items", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 2

    update_response = await client.patch(
        f"/api/v1/deals/{deal['id']}/line-items/{item['id']}",
        headers=headers,
        json={"quantity": 3},
    )
    assert update_response.status_code == 200
    assert update_response.json()["line_total"] == 300

    deal_after_update = await client.get(f"/api/v1/deals/{deal['id']}", headers=headers)
    assert deal_after_update.json()["value"] == 350

    delete_response = await client.delete(
        f"/api/v1/deals/{deal['id']}/line-items/{item['id']}", headers=headers
    )
    assert delete_response.status_code == 204

    deal_after_delete = await client.get(f"/api/v1/deals/{deal['id']}", headers=headers)
    assert deal_after_delete.json()["value"] == 50

    remaining_items = await client.get(f"/api/v1/deals/{deal['id']}/line-items", headers=headers)
    assert len(remaining_items.json()) == 1


async def test_viewer_cannot_create_line_item(client: AsyncClient, db_session: AsyncSession):
    headers = await _auth_headers(client, "deal-line-item-viewer@example.com")
    deal = await _create_deal(client, headers, title="Viewer line item deal")
    me_response = await client.get("/api/v1/users/me", headers=headers)
    user_id = me_response.json()["id"]

    await db_session.execute(
        update(OrganizationMember).where(OrganizationMember.user_id == user_id).values(role="viewer")
    )
    await db_session.flush()

    create_response = await client.post(
        f"/api/v1/deals/{deal['id']}/line-items",
        headers=headers,
        json={"product_name": "Blocked", "quantity": 1, "unit_price": 10},
    )
    assert create_response.status_code == 403


async def test_line_item_not_found_returns_404(client: AsyncClient):
    headers = await _auth_headers(client, "deal-line-item-404@example.com")
    deal = await _create_deal(client, headers, title="Deal without items")

    response = await client.patch(
        f"/api/v1/deals/{deal['id']}/line-items/11111111-1111-1111-1111-111111111111",
        headers=headers,
        json={"quantity": 2},
    )
    assert response.status_code == 404