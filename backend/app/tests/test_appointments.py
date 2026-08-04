from datetime import datetime, timedelta, timezone

from httpx import AsyncClient


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


async def _create_ai_appointment_approval(client: AsyncClient, headers: dict[str, str]) -> str:
    call_response = await client.post(
        "/api/v1/calls/text",
        headers=headers,
        json={
            "title": "Appointment Approval Source",
            "transcript_text": "Let's schedule a follow-up meeting next week.",
        },
    )
    assert call_response.status_code == 201
    conversation_id = call_response.json()["conversation"]["id"]

    analysis_response = await client.post(
        f"/api/v1/ai/analysis/conversations/{conversation_id}",
        headers=headers,
    )
    assert analysis_response.status_code == 201

    approvals_response = await client.get(
        "/api/v1/ai/approvals?status_filter=pending",
        headers=headers,
    )
    appointment_approval = next(
        approval
        for approval in approvals_response.json()
        if approval["action_type"] == "appointment"
    )
    approve_response = await client.post(
        f"/api/v1/ai/approvals/{appointment_approval['id']}/approve",
        headers=headers,
        json={
            "approved_payload": {
                "title": "Follow-up meeting",
                "proposed_datetime": "2026-07-20T09:00:00+03:00",
            }
        },
    )
    assert approve_response.status_code == 200
    return appointment_approval["id"]


async def test_appointment_crud_cancel_and_soft_delete(client: AsyncClient):
    headers = await _auth_headers(client, "appointment-crud@example.com")
    start_at = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    end_at = (datetime.now(timezone.utc) + timedelta(days=1, hours=1)).isoformat()

    create_response = await client.post(
        "/api/v1/appointments",
        headers=headers,
        json={
            "title": "Client call",
            "location": "Zoom",
            "start_at": start_at,
            "end_at": end_at,
        },
    )
    assert create_response.status_code == 201
    appointment = create_response.json()
    assert appointment["title"] == "Client call"
    assert appointment["status"] == "confirmed"
    assert appointment["source_type"] == "manual"

    list_response = await client.get("/api/v1/appointments", headers=headers)
    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == appointment["id"]

    update_response = await client.patch(
        f"/api/v1/appointments/{appointment['id']}",
        headers=headers,
        json={"location": "Office"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["location"] == "Office"

    cancel_response = await client.post(
        f"/api/v1/appointments/{appointment['id']}/cancel", headers=headers
    )
    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] == "cancelled"

    delete_response = await client.delete(
        f"/api/v1/appointments/{appointment['id']}", headers=headers
    )
    assert delete_response.status_code == 204

    get_response = await client.get(f"/api/v1/appointments/{appointment['id']}", headers=headers)
    assert get_response.status_code == 404


async def test_appointment_timezone_is_normalized_to_utc(client: AsyncClient):
    headers = await _auth_headers(client, "appointment-timezone@example.com")

    create_response = await client.post(
        "/api/v1/appointments",
        headers=headers,
        json={
            "title": "Istanbul meeting",
            "start_at": "2026-08-01T12:00:00+03:00",
            "end_at": "2026-08-01T13:00:00+03:00",
            "timezone": "Europe/Istanbul",
        },
    )
    assert create_response.status_code == 201
    body = create_response.json()
    assert body["timezone"] == "Europe/Istanbul"

    returned_start = datetime.fromisoformat(body["start_at"])
    assert returned_start.astimezone(timezone.utc).hour == 9


async def test_appointment_list_filters_by_date_range(client: AsyncClient):
    headers = await _auth_headers(client, "appointment-calendar-view@example.com")
    near_start = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    near_end = (datetime.now(timezone.utc) + timedelta(days=2, hours=1)).isoformat()
    far_start = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    far_end = (datetime.now(timezone.utc) + timedelta(days=30, hours=1)).isoformat()

    await client.post(
        "/api/v1/appointments",
        headers=headers,
        json={"title": "Near", "start_at": near_start, "end_at": near_end},
    )
    await client.post(
        "/api/v1/appointments",
        headers=headers,
        json={"title": "Far", "start_at": far_start, "end_at": far_end},
    )

    window_start = datetime.now(timezone.utc).isoformat()
    window_end = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    response = await client.get(
        "/api/v1/appointments",
        params={"start_date": window_start, "end_date": window_end},
        headers=headers,
    )
    assert response.status_code == 200
    titles = [item["title"] for item in response.json()]
    assert titles == ["Near"]


async def test_overlapping_appointment_is_blocked_and_force_overrides(client: AsyncClient):
    headers = await _auth_headers(client, "appointment-conflict@example.com")
    start_at = datetime.now(timezone.utc) + timedelta(days=3)
    end_at = start_at + timedelta(hours=1)

    first_response = await client.post(
        "/api/v1/appointments",
        headers=headers,
        json={
            "title": "First",
            "start_at": start_at.isoformat(),
            "end_at": end_at.isoformat(),
        },
    )
    assert first_response.status_code == 201

    overlap_start = start_at + timedelta(minutes=30)
    overlap_end = overlap_start + timedelta(hours=1)
    conflicting_response = await client.post(
        "/api/v1/appointments",
        headers=headers,
        json={
            "title": "Overlapping",
            "start_at": overlap_start.isoformat(),
            "end_at": overlap_end.isoformat(),
        },
    )
    assert conflicting_response.status_code == 409

    forced_response = await client.post(
        "/api/v1/appointments",
        headers=headers,
        json={
            "title": "Overlapping but forced",
            "start_at": overlap_start.isoformat(),
            "end_at": overlap_end.isoformat(),
            "force": True,
        },
    )
    assert forced_response.status_code == 201


async def test_conflict_check_endpoint_reports_overlap(client: AsyncClient):
    headers = await _auth_headers(client, "appointment-check-conflicts@example.com")
    start_at = datetime.now(timezone.utc) + timedelta(days=4)
    end_at = start_at + timedelta(hours=1)

    await client.post(
        "/api/v1/appointments",
        headers=headers,
        json={"title": "Existing", "start_at": start_at.isoformat(), "end_at": end_at.isoformat()},
    )

    response = await client.post(
        "/api/v1/appointments/check-conflicts",
        headers=headers,
        json={"start_at": start_at.isoformat(), "end_at": end_at.isoformat()},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["has_conflicts"] is True
    assert len(body["conflicts"]) == 1


async def test_appointment_can_be_created_from_approved_ai_action(client: AsyncClient):
    headers = await _auth_headers(client, "appointment-ai-approval@example.com")
    approval_id = await _create_ai_appointment_approval(client, headers)

    response = await client.post(
        "/api/v1/appointments/from-approval",
        headers=headers,
        json={"approval_id": approval_id},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Follow-up meeting"
    assert body["source_type"] == "ai_action_approval"
    assert body["ai_action_approval_id"] == approval_id

    # Materializing the same approval twice is idempotent (prevents duplicate
    # appointments from a double-click/retry) — it returns the same appointment,
    # not an error.
    duplicate_response = await client.post(
        "/api/v1/appointments/from-approval",
        headers=headers,
        json={"approval_id": approval_id},
    )
    assert duplicate_response.status_code == 201
    assert duplicate_response.json()["id"] == body["id"]


async def test_unapproved_ai_action_cannot_create_appointment(client: AsyncClient):
    headers = await _auth_headers(client, "appointment-ai-unapproved@example.com")
    call_response = await client.post(
        "/api/v1/calls/text",
        headers=headers,
        json={"title": "Unapproved Source", "transcript_text": "Let's meet sometime soon."},
    )
    conversation_id = call_response.json()["conversation"]["id"]
    await client.post(f"/api/v1/ai/analysis/conversations/{conversation_id}", headers=headers)
    approvals_response = await client.get(
        "/api/v1/ai/approvals?status_filter=pending",
        headers=headers,
    )
    approval_id = next(
        approval["id"]
        for approval in approvals_response.json()
        if approval["action_type"] == "appointment"
    )

    response = await client.post(
        "/api/v1/appointments/from-approval",
        headers=headers,
        json={"approval_id": approval_id},
    )
    assert response.status_code == 422


async def test_appointment_is_tenant_scoped(client: AsyncClient):
    first_headers = await _auth_headers(client, "appointment-tenant-one@example.com")
    second_headers = await _auth_headers(client, "appointment-tenant-two@example.com")
    start_at = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    end_at = (datetime.now(timezone.utc) + timedelta(days=1, hours=1)).isoformat()

    create_response = await client.post(
        "/api/v1/appointments",
        headers=first_headers,
        json={"title": "Tenant one appointment", "start_at": start_at, "end_at": end_at},
    )
    appointment_id = create_response.json()["id"]

    cross_tenant_response = await client.get(
        f"/api/v1/appointments/{appointment_id}", headers=second_headers
    )
    assert cross_tenant_response.status_code == 404
