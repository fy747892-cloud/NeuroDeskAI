from datetime import datetime, timedelta, timezone

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


async def _create_task(
    client: AsyncClient, headers: dict[str, str], *, title: str, due_at: str | None = None
) -> dict:
    response = await client.post(
        "/api/v1/tasks", headers=headers, json={"title": title, "due_at": due_at}
    )
    assert response.status_code == 201
    return response.json()


async def _complete_task(client: AsyncClient, headers: dict[str, str], task_id: str) -> None:
    response = await client.post(f"/api/v1/tasks/{task_id}/complete", headers=headers)
    assert response.status_code == 200


async def _create_appointment(
    client: AsyncClient, headers: dict[str, str], *, title: str, day_offset: int = 1
) -> dict:
    start_at = (datetime.now(timezone.utc) + timedelta(days=day_offset)).isoformat()
    end_at = (datetime.now(timezone.utc) + timedelta(days=day_offset, hours=1)).isoformat()
    response = await client.post(
        "/api/v1/appointments",
        headers=headers,
        json={"title": title, "start_at": start_at, "end_at": end_at},
    )
    assert response.status_code == 201
    return response.json()


async def _complete_appointment(
    client: AsyncClient, headers: dict[str, str], appointment_id: str
) -> None:
    response = await client.patch(
        f"/api/v1/appointments/{appointment_id}", headers=headers, json={"status": "completed"}
    )
    assert response.status_code == 200


async def _create_and_analyze_conversation(client: AsyncClient, headers: dict[str, str]) -> None:
    call_response = await client.post(
        "/api/v1/calls/text",
        headers=headers,
        json={
            "title": "Analytics Test Conversation",
            "transcript_text": "Customer wants a follow-up appointment next week.",
        },
    )
    assert call_response.status_code == 201
    conversation_id = call_response.json()["conversation"]["id"]

    analysis_response = await client.post(
        f"/api/v1/ai/analysis/conversations/{conversation_id}", headers=headers
    )
    assert analysis_response.status_code == 201


async def _send_chat_message(client: AsyncClient, headers: dict[str, str], message: str) -> None:
    response = await client.post("/api/v1/ai/chat", headers=headers, json={"message": message})
    assert response.status_code == 201


async def _aggregate_today(client: AsyncClient, headers: dict[str, str]) -> dict:
    response = await client.post("/api/v1/analytics/aggregate", headers=headers, json={})
    assert response.status_code == 200
    return response.json()


async def test_metric_accuracy_across_tasks_calls_appointments_ai(client: AsyncClient):
    headers = await _auth_headers(client, "analytics-accuracy@example.com")

    task_a = await _create_task(client, headers, title="Task A")
    task_b = await _create_task(client, headers, title="Task B")
    await _create_task(client, headers, title="Task C")
    await _complete_task(client, headers, task_a["id"])
    await _complete_task(client, headers, task_b["id"])

    overdue_due_at = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    await _create_task(client, headers, title="Overdue Task", due_at=overdue_due_at)

    appointment_a = await _create_appointment(client, headers, title="Appointment A", day_offset=1)
    await _create_appointment(client, headers, title="Appointment B", day_offset=2)
    await _complete_appointment(client, headers, appointment_a["id"])

    await _create_and_analyze_conversation(client, headers)
    await _send_chat_message(client, headers, "What tasks are open?")

    await _aggregate_today(client, headers)

    task_metrics = await client.get("/api/v1/analytics/tasks", headers=headers)
    assert task_metrics.status_code == 200
    today_task_metric = task_metrics.json()[-1]
    assert today_task_metric["created_count"] == 4
    assert today_task_metric["completed_count"] == 2
    assert today_task_metric["overdue_count"] == 1

    call_metrics = await client.get("/api/v1/analytics/calls", headers=headers)
    today_call_metric = call_metrics.json()[-1]
    assert today_call_metric["call_count"] == 1
    assert today_call_metric["analyzed_count"] == 1

    appointment_metrics = await client.get("/api/v1/analytics/appointments", headers=headers)
    today_appointment_metric = appointment_metrics.json()[-1]
    assert today_appointment_metric["completed_count"] == 1

    ai_metrics = await client.get("/api/v1/analytics/ai", headers=headers)
    today_ai_metric = ai_metrics.json()[-1]
    # 1 conversation analysis + 2 for the chat message (intent-detection pass,
    # then answer generation — see AiChatService.send_message) = 3 requests.
    assert today_ai_metric["request_count"] == 3
    assert today_ai_metric["cost_amount"] > 0
    assert today_ai_metric["avg_latency_ms"] >= 0


async def test_ai_cost_logging_reflected_in_overview(client: AsyncClient):
    headers = await _auth_headers(client, "analytics-ai-cost@example.com")

    await _send_chat_message(client, headers, "Summarize my recent activity please.")
    await _create_and_analyze_conversation(client, headers)

    await _aggregate_today(client, headers)

    overview = await client.get("/api/v1/analytics/overview", headers=headers)
    assert overview.status_code == 200
    body = overview.json()
    # 1 conversation analysis + 2 for the chat message (intent-detection pass,
    # then answer generation — see AiChatService.send_message) = 3 requests.
    assert body["ai_requests"] == 3
    assert body["ai_cost_amount"] > 0


async def test_analytics_are_tenant_scoped(client: AsyncClient):
    first_headers = await _auth_headers(client, "analytics-tenant-one@example.com")
    second_headers = await _auth_headers(client, "analytics-tenant-two@example.com")

    await _create_task(client, first_headers, title="Tenant one task")
    await _create_task(client, second_headers, title="Tenant two task A")
    await _create_task(client, second_headers, title="Tenant two task B")

    await _aggregate_today(client, first_headers)
    await _aggregate_today(client, second_headers)

    first_metrics = await client.get("/api/v1/analytics/tasks", headers=first_headers)
    second_metrics = await client.get("/api/v1/analytics/tasks", headers=second_headers)

    assert first_metrics.json()[-1]["created_count"] == 1
    assert second_metrics.json()[-1]["created_count"] == 2


async def test_moderate_volume_task_metrics_stay_accurate(client: AsyncClient):
    headers = await _auth_headers(client, "analytics-volume@example.com")

    created_tasks = []
    for index in range(20):
        task = await _create_task(client, headers, title=f"Bulk task {index}")
        created_tasks.append(task)

    for task in created_tasks[:12]:
        await _complete_task(client, headers, task["id"])

    await _aggregate_today(client, headers)

    task_metrics = await client.get("/api/v1/analytics/tasks", headers=headers)
    today_metric = task_metrics.json()[-1]
    assert today_metric["created_count"] == 20
    assert today_metric["completed_count"] == 12


async def test_aggregate_is_idempotent(client: AsyncClient):
    headers = await _auth_headers(client, "analytics-idempotent@example.com")
    await _create_task(client, headers, title="Idempotency task")

    await _aggregate_today(client, headers)
    first_metrics = await client.get("/api/v1/analytics/tasks", headers=headers)
    first_count = len(first_metrics.json())
    first_created_count = first_metrics.json()[-1]["created_count"]

    await _aggregate_today(client, headers)
    second_metrics = await client.get("/api/v1/analytics/tasks", headers=headers)
    second_count = len(second_metrics.json())
    second_created_count = second_metrics.json()[-1]["created_count"]

    assert second_count == first_count
    assert second_created_count == first_created_count == 1


async def test_viewer_can_read_but_not_trigger_aggregate(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_headers(client, "analytics-viewer@example.com")
    me_response = await client.get("/api/v1/users/me", headers=headers)
    user_id = me_response.json()["id"]

    await db_session.execute(
        update(OrganizationMember).where(OrganizationMember.user_id == user_id).values(role="viewer")
    )
    await db_session.flush()

    read_response = await client.get("/api/v1/analytics/overview", headers=headers)
    assert read_response.status_code == 200

    aggregate_response = await client.post(
        "/api/v1/analytics/aggregate", headers=headers, json={}
    )
    assert aggregate_response.status_code == 403
