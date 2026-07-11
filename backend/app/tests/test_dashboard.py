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


async def _create_task(
    client: AsyncClient, headers: dict[str, str], *, due_at: str | None = None
) -> dict:
    body: dict = {"title": "Follow up"}
    if due_at is not None:
        body["due_at"] = due_at
    response = await client.post("/api/v1/tasks", headers=headers, json=body)
    assert response.status_code == 201
    return response.json()


async def _create_appointment(client: AsyncClient, headers: dict[str, str], *, start_at: datetime) -> dict:
    end_at = start_at + timedelta(hours=1)
    response = await client.post(
        "/api/v1/appointments",
        headers=headers,
        json={"title": "Client call", "start_at": start_at.isoformat(), "end_at": end_at.isoformat()},
    )
    assert response.status_code == 201
    return response.json()


async def _create_conversation_with_pending_approval(client: AsyncClient, headers: dict[str, str]) -> dict:
    call_response = await client.post(
        "/api/v1/calls/text",
        headers=headers,
        json={
            "title": "Dashboard Source Call",
            "transcript_text": "Let's follow up and schedule a meeting.",
        },
    )
    assert call_response.status_code == 201
    conversation = call_response.json()["conversation"]

    analysis_response = await client.post(
        f"/api/v1/ai/analysis/conversations/{conversation['id']}",
        headers=headers,
    )
    assert analysis_response.status_code == 201
    return conversation


async def test_dashboard_aggregates_open_overdue_upcoming_recent_and_pending(client: AsyncClient):
    headers = await _auth_headers(client, "dashboard-aggregate@example.com")
    future_due = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
    past_due = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()

    open_task = await _create_task(client, headers, due_at=future_due)
    overdue_task = await _create_task(client, headers, due_at=past_due)
    appointment = await _create_appointment(
        client, headers, start_at=datetime.now(timezone.utc) + timedelta(days=2)
    )
    conversation = await _create_conversation_with_pending_approval(client, headers)

    response = await client.get("/api/v1/dashboard", headers=headers)
    assert response.status_code == 200
    body = response.json()

    open_task_ids = {item["id"] for item in body["open_tasks"]}
    assert {open_task["id"], overdue_task["id"]} <= open_task_ids

    overdue_task_ids = {item["id"] for item in body["overdue_tasks"]}
    assert overdue_task_ids == {overdue_task["id"]}

    upcoming_appointment_ids = {item["id"] for item in body["upcoming_appointments"]}
    assert appointment["id"] in upcoming_appointment_ids

    recent_conversation_ids = {item["id"] for item in body["recent_conversations"]}
    assert conversation["id"] in recent_conversation_ids

    assert len(body["pending_ai_approvals"]) >= 1
    assert {approval["source_id"] for approval in body["pending_ai_approvals"]} == {conversation["id"]}

    summary = body["summary"]
    assert summary["open_tasks_count"] == len(body["open_tasks"])
    assert summary["overdue_tasks_count"] == 1
    assert summary["upcoming_appointments_count"] == len(body["upcoming_appointments"])
    assert summary["pending_ai_approvals_count"] == len(body["pending_ai_approvals"])


async def test_completed_and_cancelled_tasks_excluded_from_open_tasks(client: AsyncClient):
    headers = await _auth_headers(client, "dashboard-task-exclusion@example.com")
    completed_task = await _create_task(client, headers)
    cancelled_task = await _create_task(client, headers)

    await client.post(f"/api/v1/tasks/{completed_task['id']}/complete", headers=headers)
    await client.delete(f"/api/v1/tasks/{cancelled_task['id']}", headers=headers)

    response = await client.get("/api/v1/dashboard", headers=headers)
    open_task_ids = {item["id"] for item in response.json()["open_tasks"]}
    assert completed_task["id"] not in open_task_ids
    assert cancelled_task["id"] not in open_task_ids


async def test_cancelled_and_past_appointments_excluded_from_upcoming(client: AsyncClient):
    headers = await _auth_headers(client, "dashboard-appointment-exclusion@example.com")
    cancelled_appointment = await _create_appointment(
        client, headers, start_at=datetime.now(timezone.utc) + timedelta(days=1)
    )
    await client.post(f"/api/v1/appointments/{cancelled_appointment['id']}/cancel", headers=headers)

    past_appointment = await _create_appointment(
        client, headers, start_at=datetime.now(timezone.utc) - timedelta(days=1)
    )

    response = await client.get("/api/v1/dashboard", headers=headers)
    upcoming_ids = {item["id"] for item in response.json()["upcoming_appointments"]}
    assert cancelled_appointment["id"] not in upcoming_ids
    assert past_appointment["id"] not in upcoming_ids


async def test_dashboard_requires_authentication(client: AsyncClient):
    response = await client.get("/api/v1/dashboard")
    assert response.status_code == 401


async def test_dashboard_is_tenant_scoped(client: AsyncClient):
    first_headers = await _auth_headers(client, "dashboard-tenant-one@example.com")
    second_headers = await _auth_headers(client, "dashboard-tenant-two@example.com")

    first_task = await _create_task(client, first_headers)
    await _create_task(client, second_headers)

    response = await client.get("/api/v1/dashboard", headers=first_headers)
    open_task_ids = {item["id"] for item in response.json()["open_tasks"]}
    assert open_task_ids == {first_task["id"]}
