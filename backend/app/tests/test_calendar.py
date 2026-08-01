from httpx import AsyncClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import decrypt_token
from app.modules.appointments.models import Appointment
from app.modules.calendar.models import CalendarToken
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


async def _start_connect(client: AsyncClient, headers: dict[str, str]) -> dict:
    response = await client.post("/api/v1/calendar/google/connect", headers=headers)
    assert response.status_code == 200
    return response.json()


async def _complete_connect(client: AsyncClient, state: str, code: str = "mock-code") -> dict:
    response = await client.get(
        "/api/v1/calendar/google/callback", params={"code": code, "state": state}
    )
    assert response.status_code == 200
    return response.json()


async def _connect(client: AsyncClient, headers: dict[str, str]) -> dict:
    start = await _start_connect(client, headers)
    return await _complete_connect(client, start["state"])


async def test_connect_returns_calendar_scope_authorize_url_and_state(client: AsyncClient):
    headers = await _auth_headers(client, "calendar-connect@example.com")
    start = await _start_connect(client, headers)

    assert "calendar.readonly" in start["authorize_url"]
    assert start["state"]


async def test_callback_with_invalid_state_is_rejected(client: AsyncClient):
    response = await client.get(
        "/api/v1/calendar/google/callback", params={"code": "mock-code", "state": "bogus-state"}
    )
    assert response.status_code == 401


async def test_callback_state_is_single_use(client: AsyncClient):
    headers = await _auth_headers(client, "calendar-state-replay@example.com")
    start = await _start_connect(client, headers)

    first = await client.get(
        "/api/v1/calendar/google/callback", params={"code": "mock-code", "state": start["state"]}
    )
    assert first.status_code == 200

    replay = await client.get(
        "/api/v1/calendar/google/callback", params={"code": "mock-code", "state": start["state"]}
    )
    assert replay.status_code == 401


async def test_callback_success_encrypts_tokens_at_rest(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_headers(client, "calendar-encryption@example.com")
    account = await _connect(client, headers)

    result = await db_session.execute(
        select(CalendarToken).where(CalendarToken.calendar_account_id == account["id"])
    )
    token_row = result.scalar_one()
    assert token_row.refresh_token_encrypted is not None

    assert not token_row.access_token_encrypted.startswith("mock-access-")
    assert not token_row.refresh_token_encrypted.startswith("mock-refresh-")

    assert decrypt_token(token_row.access_token_encrypted).startswith("mock-access-")
    assert decrypt_token(token_row.refresh_token_encrypted).startswith("mock-refresh-")


async def test_connect_records_consent(client: AsyncClient):
    headers = await _auth_headers(client, "calendar-consent@example.com")
    account = await _connect(client, headers)

    assert account["status"] == "connected"
    assert account["connected_at"] is not None
    assert "calendar.readonly" in account["consent_scope"]


async def test_revoke_stops_further_sync_and_deletes_tokens(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_headers(client, "calendar-revoke@example.com")
    account = await _connect(client, headers)

    revoke_response = await client.post(
        f"/api/v1/calendar/accounts/{account['id']}/revoke", headers=headers
    )
    assert revoke_response.status_code == 200
    assert revoke_response.json()["status"] == "revoked"

    sync_response = await client.post(
        f"/api/v1/calendar/accounts/{account['id']}/sync", headers=headers
    )
    assert sync_response.status_code == 422

    result = await db_session.execute(
        select(CalendarToken).where(CalendarToken.calendar_account_id == account["id"])
    )
    assert result.scalar_one_or_none() is None


async def test_sync_creates_appointments_from_google_calendar_source(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_headers(client, "calendar-sync-appointments@example.com")
    account = await _connect(client, headers)

    sync_response = await client.post(
        f"/api/v1/calendar/accounts/{account['id']}/sync", headers=headers
    )
    assert sync_response.status_code == 200
    assert sync_response.json()["created"] > 0
    assert sync_response.json()["skipped"] == 0

    result = await db_session.execute(
        select(Appointment).where(Appointment.source_type == "google_calendar")
    )
    appointments = result.scalars().all()
    assert len(appointments) == sync_response.json()["created"]
    assert all(appointment.external_event_id is not None for appointment in appointments)


async def test_sync_dedups_events_on_repeat_calls(client: AsyncClient):
    headers = await _auth_headers(client, "calendar-sync-dedup@example.com")
    account = await _connect(client, headers)

    first_sync = await client.post(
        f"/api/v1/calendar/accounts/{account['id']}/sync", headers=headers
    )
    assert first_sync.status_code == 200
    assert first_sync.json()["created"] > 0

    second_sync = await client.post(
        f"/api/v1/calendar/accounts/{account['id']}/sync", headers=headers
    )
    assert second_sync.status_code == 200
    assert second_sync.json()["created"] == 0
    assert second_sync.json()["skipped"] == first_sync.json()["fetched"]


async def test_calendar_accounts_are_tenant_scoped(client: AsyncClient):
    first_headers = await _auth_headers(client, "calendar-tenant-one@example.com")
    second_headers = await _auth_headers(client, "calendar-tenant-two@example.com")

    first_account = await _connect(client, first_headers)
    await _connect(client, second_headers)

    list_response = await client.get("/api/v1/calendar/accounts", headers=first_headers)
    assert list_response.status_code == 200
    account_ids = {item["id"] for item in list_response.json()}
    assert account_ids == {first_account["id"]}


async def test_viewer_cannot_start_google_calendar_connect(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_headers(client, "calendar-viewer@example.com")
    me_response = await client.get("/api/v1/users/me", headers=headers)
    user_id = me_response.json()["id"]

    await db_session.execute(
        update(OrganizationMember)
        .where(OrganizationMember.user_id == user_id)
        .values(role="viewer")
    )
    await db_session.flush()

    response = await client.post("/api/v1/calendar/google/connect", headers=headers)
    assert response.status_code == 403


async def test_google_calendar_callback_rejects_mock_fail_code(client: AsyncClient):
    headers = await _auth_headers(client, "calendar-mockfail@example.com")
    start = await _start_connect(client, headers)

    response = await client.get(
        "/api/v1/calendar/google/callback",
        params={"code": "[mock-fail]", "state": start["state"]},
    )
    assert response.status_code >= 400
