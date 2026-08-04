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


async def _create_lead_form(client: AsyncClient, headers: dict[str, str]) -> dict:
    response = await client.post("/api/v1/lead-forms", headers=headers)
    assert response.status_code == 201
    return response.json()


async def test_lead_form_create_get_and_duplicate_conflict(client: AsyncClient):
    headers = await _auth_headers(client, "lead-form-crud@example.com")

    created = await _create_lead_form(client, headers)
    assert created["is_active"] is True
    assert created["public_token"]
    assert created["public_url"].endswith(f"/lead-form/{created['public_token']}")

    get_response = await client.get("/api/v1/lead-forms/me", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["id"] == created["id"]

    duplicate_response = await client.post("/api/v1/lead-forms", headers=headers)
    assert duplicate_response.status_code == 409


async def test_lead_form_toggle_active_and_rotate_token(client: AsyncClient):
    headers = await _auth_headers(client, "lead-form-toggle@example.com")
    created = await _create_lead_form(client, headers)

    update_response = await client.patch(
        f"/api/v1/lead-forms/{created['id']}", headers=headers, json={"is_active": False}
    )
    assert update_response.status_code == 200
    assert update_response.json()["is_active"] is False

    rotate_response = await client.post(
        f"/api/v1/lead-forms/{created['id']}/rotate-token", headers=headers
    )
    assert rotate_response.status_code == 200
    assert rotate_response.json()["public_token"] != created["public_token"]


async def test_viewer_cannot_manage_lead_form(client: AsyncClient, db_session: AsyncSession):
    headers = await _auth_headers(client, "lead-form-viewer@example.com")
    me_response = await client.get("/api/v1/users/me", headers=headers)
    user_id = me_response.json()["id"]

    await db_session.execute(
        update(OrganizationMember).where(OrganizationMember.user_id == user_id).values(role="viewer")
    )
    await db_session.flush()

    create_response = await client.post("/api/v1/lead-forms", headers=headers)
    assert create_response.status_code == 403


async def test_public_get_reports_organization_name_and_active_state(client: AsyncClient):
    headers = await _auth_headers(client, "lead-form-public-get@example.com")
    created = await _create_lead_form(client, headers)

    public_response = await client.get(f"/api/v1/lead-forms/public/{created['public_token']}")
    assert public_response.status_code == 200
    body = public_response.json()
    assert body["is_active"] is True
    assert body["organization_name"]


async def test_public_get_unknown_token_is_404(client: AsyncClient):
    response = await client.get("/api/v1/lead-forms/public/does-not-exist")
    assert response.status_code == 404


async def test_public_submit_creates_contact_and_deal(client: AsyncClient):
    headers = await _auth_headers(client, "lead-form-submit@example.com")
    created = await _create_lead_form(client, headers)

    submit_response = await client.post(
        f"/api/v1/lead-forms/public/{created['public_token']}/submit",
        json={
            "full_name": "Ada Lovelace",
            "email": "ada@example.com",
            "message": "Fiyat teklifi almak istiyorum.",
        },
    )
    assert submit_response.status_code == 204

    contacts_response = await client.get("/api/v1/contacts", headers=headers)
    contacts = contacts_response.json()["items"]
    assert any(c["full_name"] == "Ada Lovelace" and c["email"] == "ada@example.com" for c in contacts)

    deals_response = await client.get("/api/v1/deals", headers=headers)
    deals = deals_response.json()
    assert any(d["source_type"] == "web_form" and d["stage"] == "lead" for d in deals)


async def test_public_submit_dedups_by_email(client: AsyncClient):
    headers = await _auth_headers(client, "lead-form-dedup@example.com")
    created = await _create_lead_form(client, headers)

    for _ in range(2):
        response = await client.post(
            f"/api/v1/lead-forms/public/{created['public_token']}/submit",
            json={"full_name": "Grace Hopper", "email": "grace@example.com"},
        )
        assert response.status_code == 204

    contacts_response = await client.get("/api/v1/contacts", headers=headers)
    contacts = [c for c in contacts_response.json()["items"] if c["email"] == "grace@example.com"]
    assert len(contacts) == 1

    deals_response = await client.get("/api/v1/deals", headers=headers)
    deals = [d for d in deals_response.json() if d["source_type"] == "web_form"]
    assert len(deals) == 2  # dedup applies to the Contact, not to logging each visit as a fresh deal


async def test_public_submit_honeypot_creates_nothing(client: AsyncClient):
    headers = await _auth_headers(client, "lead-form-honeypot@example.com")
    created = await _create_lead_form(client, headers)

    response = await client.post(
        f"/api/v1/lead-forms/public/{created['public_token']}/submit",
        json={"full_name": "Bot", "email": "bot@example.com", "website": "http://spam.example"},
    )
    assert response.status_code == 204

    contacts_response = await client.get("/api/v1/contacts", headers=headers)
    contacts = contacts_response.json()["items"]
    assert not any(c["email"] == "bot@example.com" for c in contacts)


async def test_public_submit_requires_email_or_phone(client: AsyncClient):
    headers = await _auth_headers(client, "lead-form-missing-contact@example.com")
    created = await _create_lead_form(client, headers)

    response = await client.post(
        f"/api/v1/lead-forms/public/{created['public_token']}/submit",
        json={"full_name": "No Contact Info"},
    )
    assert response.status_code == 422


async def test_public_submit_on_inactive_form_is_404(client: AsyncClient):
    headers = await _auth_headers(client, "lead-form-inactive@example.com")
    created = await _create_lead_form(client, headers)
    await client.patch(f"/api/v1/lead-forms/{created['id']}", headers=headers, json={"is_active": False})

    response = await client.post(
        f"/api/v1/lead-forms/public/{created['public_token']}/submit",
        json={"full_name": "Too Late", "email": "toolate@example.com"},
    )
    assert response.status_code == 404


async def test_public_submit_is_rate_limited_per_ip(client: AsyncClient):
    headers = await _auth_headers(client, "lead-form-rate-limit@example.com")
    created = await _create_lead_form(client, headers)

    for i in range(5):
        response = await client.post(
            f"/api/v1/lead-forms/public/{created['public_token']}/submit",
            json={"full_name": f"Visitor {i}", "email": f"visitor{i}@example.com"},
        )
        assert response.status_code == 204

    limited_response = await client.post(
        f"/api/v1/lead-forms/public/{created['public_token']}/submit",
        json={"full_name": "One Too Many", "email": "onetoomany@example.com"},
    )
    assert limited_response.status_code == 429
