import uuid
from datetime import datetime, timedelta, timezone

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.notifications.models import Notification


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
    client: AsyncClient, headers: dict[str, str], *, due_at: str | None = None, description: str | None = None
) -> dict:
    body: dict = {"title": "Follow up"}
    if due_at is not None:
        body["due_at"] = due_at
    if description is not None:
        body["description"] = description
    response = await client.post("/api/v1/tasks", headers=headers, json=body)
    assert response.status_code == 201
    return response.json()


async def _create_appointment(client: AsyncClient, headers: dict[str, str]) -> dict:
    start_at = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    end_at = (datetime.now(timezone.utc) + timedelta(days=1, hours=1)).isoformat()
    response = await client.post(
        "/api/v1/appointments",
        headers=headers,
        json={"title": "Client call", "start_at": start_at, "end_at": end_at},
    )
    assert response.status_code == 201
    return response.json()


async def test_task_reminder_via_offset_minutes(client: AsyncClient):
    headers = await _auth_headers(client, "reminder-task-offset@example.com")
    due_at = datetime.now(timezone.utc) + timedelta(days=1)
    task = await _create_task(client, headers, due_at=due_at.isoformat())

    response = await client.post(
        f"/api/v1/tasks/{task['id']}/reminders",
        headers=headers,
        json={"offset_minutes": 60},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["source_type"] == "task"
    assert body["source_id"] == task["id"]
    assert body["channel"] == "in_app"
    assert body["status"] == "pending"

    scheduled_at = datetime.fromisoformat(body["scheduled_at"])
    assert abs((scheduled_at - (due_at - timedelta(minutes=60))).total_seconds()) < 1


async def test_task_reminder_without_due_at_requires_offset_to_fail(client: AsyncClient):
    headers = await _auth_headers(client, "reminder-task-no-due@example.com")
    task = await _create_task(client, headers)

    response = await client.post(
        f"/api/v1/tasks/{task['id']}/reminders",
        headers=headers,
        json={"offset_minutes": 15},
    )
    assert response.status_code == 422


async def test_appointment_reminder_via_explicit_remind_at(client: AsyncClient):
    headers = await _auth_headers(client, "reminder-appointment-explicit@example.com")
    appointment = await _create_appointment(client, headers)
    remind_at = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()

    response = await client.post(
        f"/api/v1/appointments/{appointment['id']}/reminders",
        headers=headers,
        json={"remind_at": remind_at},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["source_type"] == "appointment"
    assert body["notification_type"] == "appointment_reminder"


async def test_duplicate_reminder_is_rejected(client: AsyncClient):
    headers = await _auth_headers(client, "reminder-duplicate@example.com")
    appointment = await _create_appointment(client, headers)
    remind_at = (datetime.now(timezone.utc) + timedelta(hours=3)).isoformat()

    first = await client.post(
        f"/api/v1/appointments/{appointment['id']}/reminders",
        headers=headers,
        json={"remind_at": remind_at},
    )
    assert first.status_code == 201

    duplicate = await client.post(
        f"/api/v1/appointments/{appointment['id']}/reminders",
        headers=headers,
        json={"remind_at": remind_at},
    )
    assert duplicate.status_code == 409


async def test_list_and_mark_notification_read(client: AsyncClient):
    headers = await _auth_headers(client, "reminder-list-read@example.com")
    appointment = await _create_appointment(client, headers)
    remind_at = (datetime.now(timezone.utc) + timedelta(hours=4)).isoformat()

    create_response = await client.post(
        f"/api/v1/appointments/{appointment['id']}/reminders",
        headers=headers,
        json={"remind_at": remind_at},
    )
    notification_id = create_response.json()["id"]

    list_response = await client.get("/api/v1/notifications", headers=headers)
    assert list_response.status_code == 200
    assert any(item["id"] == notification_id for item in list_response.json())

    read_response = await client.patch(
        f"/api/v1/notifications/{notification_id}/read", headers=headers
    )
    assert read_response.status_code == 200
    assert read_response.json()["status"] == "read"


async def test_process_due_sends_in_app_notification(client: AsyncClient):
    headers = await _auth_headers(client, "reminder-process-due@example.com")
    task = await _create_task(client, headers)
    past_remind_at = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()

    create_response = await client.post(
        f"/api/v1/tasks/{task['id']}/reminders",
        headers=headers,
        json={"remind_at": past_remind_at},
    )
    notification_id = create_response.json()["id"]

    process_response = await client.post("/api/v1/notifications/process-due", headers=headers)
    assert process_response.status_code == 200
    summary = process_response.json()
    assert summary["processed"] == 1
    assert summary["sent"] == 1

    list_response = await client.get("/api/v1/notifications", headers=headers)
    processed = next(item for item in list_response.json() if item["id"] == notification_id)
    assert processed["status"] == "sent"
    assert processed["sent_at"] is not None

    idempotent_response = await client.post("/api/v1/notifications/process-due", headers=headers)
    assert idempotent_response.json() == {
        "processed": 0,
        "sent": 0,
        "failed": 0,
        "dead_lettered": 0,
    }


async def test_process_due_retries_then_dead_letters_failing_email(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_headers(client, "reminder-retry-dlq@example.com")
    task = await _create_task(client, headers, description="[mock-fail] cannot reach provider")
    past_remind_at = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()

    create_response = await client.post(
        f"/api/v1/tasks/{task['id']}/reminders",
        headers=headers,
        json={"remind_at": past_remind_at, "channel": "email"},
    )
    notification_id = uuid.UUID(create_response.json()["id"])

    first_attempt = await client.post("/api/v1/notifications/process-due", headers=headers)
    assert first_attempt.json()["failed"] == 1
    assert first_attempt.json()["dead_lettered"] == 0

    result = await db_session.execute(select(Notification).where(Notification.id == notification_id))
    notification = result.scalar_one()
    assert notification.attempts == 1
    assert notification.status == "pending"

    # Simulate that enough time has passed for the backed-off retry to become due again.
    notification.attempts = 2
    notification.scheduled_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    await db_session.flush()

    final_attempt = await client.post("/api/v1/notifications/process-due", headers=headers)
    assert final_attempt.json()["dead_lettered"] == 1

    result = await db_session.execute(select(Notification).where(Notification.id == notification_id))
    notification = result.scalar_one()
    assert notification.status == "dead_letter"
    assert notification.attempts == 3


async def test_process_due_is_tenant_scoped(client: AsyncClient):
    first_headers = await _auth_headers(client, "reminder-tenant-one@example.com")
    second_headers = await _auth_headers(client, "reminder-tenant-two@example.com")

    first_task = await _create_task(client, first_headers)
    second_task = await _create_task(client, second_headers)
    past_remind_at = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()

    await client.post(
        f"/api/v1/tasks/{first_task['id']}/reminders",
        headers=first_headers,
        json={"remind_at": past_remind_at},
    )
    second_create = await client.post(
        f"/api/v1/tasks/{second_task['id']}/reminders",
        headers=second_headers,
        json={"remind_at": past_remind_at},
    )
    second_notification_id = second_create.json()["id"]

    process_response = await client.post("/api/v1/notifications/process-due", headers=first_headers)
    assert process_response.json()["sent"] == 1

    second_list = await client.get("/api/v1/notifications", headers=second_headers)
    second_notification = next(
        item for item in second_list.json() if item["id"] == second_notification_id
    )
    assert second_notification["status"] == "pending"
