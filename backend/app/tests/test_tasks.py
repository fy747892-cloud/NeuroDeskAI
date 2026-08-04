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


async def _create_ai_task_approval(client: AsyncClient, headers: dict[str, str]) -> str:
    call_response = await client.post(
        "/api/v1/calls/text",
        headers=headers,
        json={
            "title": "Task Approval Source",
            "transcript_text": "Please follow up and prepare the proposal.",
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
    task_approval = next(
        approval for approval in approvals_response.json() if approval["action_type"] == "task"
    )
    approve_response = await client.post(
        f"/api/v1/ai/approvals/{task_approval['id']}/approve",
        headers=headers,
        json={
            "approved_payload": {
                "title": "Prepare proposal",
                "description": "AI suggestion reviewed by user.",
                "priority": "high",
                "due_at": "2026-07-20T09:00:00+03:00",
            }
        },
    )
    assert approve_response.status_code == 200
    return task_approval["id"]


async def test_task_crud_complete_and_soft_delete(client: AsyncClient):
    headers = await _auth_headers(client, "task-crud@example.com")
    due_at = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()

    create_response = await client.post(
        "/api/v1/tasks",
        headers=headers,
        json={
            "title": "Call customer",
            "description": "Confirm next steps.",
            "priority": "high",
            "due_at": due_at,
        },
    )
    assert create_response.status_code == 201
    task = create_response.json()
    assert task["title"] == "Call customer"
    assert task["status"] == "pending"
    assert task["source_type"] == "manual"

    list_response = await client.get("/api/v1/tasks", headers=headers)
    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == task["id"]

    update_response = await client.patch(
        f"/api/v1/tasks/{task['id']}",
        headers=headers,
        json={"status": "in_progress", "priority": "medium"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "in_progress"
    assert update_response.json()["priority"] == "medium"

    complete_response = await client.post(f"/api/v1/tasks/{task['id']}/complete", headers=headers)
    assert complete_response.status_code == 200
    assert complete_response.json()["status"] == "completed"

    delete_response = await client.delete(f"/api/v1/tasks/{task['id']}", headers=headers)
    assert delete_response.status_code == 204

    get_response = await client.get(f"/api/v1/tasks/{task['id']}", headers=headers)
    assert get_response.status_code == 404


async def test_overdue_tasks_only_returns_open_past_due_tasks(client: AsyncClient):
    headers = await _auth_headers(client, "task-overdue@example.com")
    past_due = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    future_due = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()

    overdue_response = await client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"title": "Past due", "due_at": past_due},
    )
    assert overdue_response.status_code == 201
    future_response = await client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"title": "Future due", "due_at": future_due},
    )
    assert future_response.status_code == 201

    response = await client.get("/api/v1/tasks/overdue", headers=headers)
    assert response.status_code == 200
    assert [task["title"] for task in response.json()] == ["Past due"]


async def test_task_is_tenant_scoped(client: AsyncClient):
    first_headers = await _auth_headers(client, "task-tenant-one@example.com")
    second_headers = await _auth_headers(client, "task-tenant-two@example.com")
    create_response = await client.post(
        "/api/v1/tasks",
        headers=first_headers,
        json={"title": "Tenant one task"},
    )
    task_id = create_response.json()["id"]

    cross_tenant_response = await client.get(f"/api/v1/tasks/{task_id}", headers=second_headers)
    assert cross_tenant_response.status_code == 404


async def test_task_can_be_created_from_approved_ai_action(client: AsyncClient):
    headers = await _auth_headers(client, "task-ai-approval@example.com")
    approval_id = await _create_ai_task_approval(client, headers)

    response = await client.post(
        "/api/v1/tasks/from-approval",
        headers=headers,
        json={"approval_id": approval_id},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Prepare proposal"
    assert body["priority"] == "high"
    assert body["source_type"] == "ai_action_approval"
    assert body["ai_action_approval_id"] == approval_id

    # Materializing the same approval twice is idempotent (prevents duplicate
    # tasks from a double-click/retry) — it returns the same task, not an error.
    duplicate_response = await client.post(
        "/api/v1/tasks/from-approval",
        headers=headers,
        json={"approval_id": approval_id},
    )
    assert duplicate_response.status_code == 201
    assert duplicate_response.json()["id"] == body["id"]


async def test_unapproved_ai_action_cannot_create_task(client: AsyncClient):
    headers = await _auth_headers(client, "task-ai-unapproved@example.com")
    call_response = await client.post(
        "/api/v1/calls/text",
        headers=headers,
        json={"title": "Unapproved Source", "transcript_text": "Follow up later."},
    )
    conversation_id = call_response.json()["conversation"]["id"]
    await client.post(f"/api/v1/ai/analysis/conversations/{conversation_id}", headers=headers)
    approvals_response = await client.get(
        "/api/v1/ai/approvals?status_filter=pending",
        headers=headers,
    )
    approval_id = next(
        approval["id"] for approval in approvals_response.json() if approval["action_type"] == "task"
    )

    response = await client.post(
        "/api/v1/tasks/from-approval",
        headers=headers,
        json={"approval_id": approval_id},
    )
    assert response.status_code == 422
