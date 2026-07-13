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