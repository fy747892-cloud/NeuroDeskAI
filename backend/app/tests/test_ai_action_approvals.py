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


async def _create_analysis(client: AsyncClient, headers: dict[str, str]) -> dict:
    call_response = await client.post(
        "/api/v1/calls/text",
        headers=headers,
        json={
            "title": "Approval Candidate Conversation",
            "transcript_text": "Schedule a follow-up and confirm the next step.",
        },
    )
    assert call_response.status_code == 201
    conversation_id = call_response.json()["conversation"]["id"]

    response = await client.post(
        f"/api/v1/ai/analysis/conversations/{conversation_id}",
        headers=headers,
    )
    assert response.status_code == 201
    assert response.json()["status"] == "completed"
    return response.json()


async def test_ai_analysis_creates_pending_action_approvals(client: AsyncClient):
    headers = await _auth_headers(client, "approval-list@example.com")
    await _create_analysis(client, headers)

    response = await client.get("/api/v1/ai/approvals?status_filter=pending", headers=headers)
    assert response.status_code == 200
    approvals = response.json()
    assert {approval["action_type"] for approval in approvals} == {"task", "appointment"}
    assert {approval["status"] for approval in approvals} == {"pending"}
    assert all(approval["source_type"] == "conversation" for approval in approvals)
    assert all(approval["confidence_score"] is not None for approval in approvals)


async def test_ai_action_approval_can_be_approved_with_edited_payload(client: AsyncClient):
    headers = await _auth_headers(client, "approval-approve@example.com")
    await _create_analysis(client, headers)
    approvals_response = await client.get("/api/v1/ai/approvals?status_filter=pending", headers=headers)
    task_approval = next(
        approval for approval in approvals_response.json() if approval["action_type"] == "task"
    )

    edited_payload = {
        "title": "Edited follow-up task",
        "description": "Human reviewed and clarified the task.",
        "confidence": 0.72,
    }
    approve_response = await client.post(
        f"/api/v1/ai/approvals/{task_approval['id']}/approve",
        headers=headers,
        json={"approved_payload": edited_payload},
    )
    assert approve_response.status_code == 200
    body = approve_response.json()
    assert body["status"] == "approved"
    assert body["approved_payload"] == edited_payload
    assert body["decided_by"] is not None
    assert body["decided_at"] is not None

    second_approve = await client.post(
        f"/api/v1/ai/approvals/{task_approval['id']}/approve",
        headers=headers,
        json={},
    )
    assert second_approve.status_code == 422


async def test_ai_action_approval_can_be_rejected_without_applying_action(client: AsyncClient):
    headers = await _auth_headers(client, "approval-reject@example.com")
    await _create_analysis(client, headers)
    approvals_response = await client.get("/api/v1/ai/approvals?status_filter=pending", headers=headers)
    appointment_approval = next(
        approval for approval in approvals_response.json() if approval["action_type"] == "appointment"
    )

    reject_response = await client.post(
        f"/api/v1/ai/approvals/{appointment_approval['id']}/reject",
        headers=headers,
    )
    assert reject_response.status_code == 200
    body = reject_response.json()
    assert body["status"] == "rejected"
    assert body["approved_payload"] is None


async def test_ai_action_approvals_are_tenant_scoped(client: AsyncClient):
    first_headers = await _auth_headers(client, "approval-tenant-one@example.com")
    second_headers = await _auth_headers(client, "approval-tenant-two@example.com")
    await _create_analysis(client, first_headers)
    approvals_response = await client.get(
        "/api/v1/ai/approvals?status_filter=pending",
        headers=first_headers,
    )
    approval_id = approvals_response.json()[0]["id"]

    cross_tenant_get = await client.get(
        f"/api/v1/ai/approvals/{approval_id}",
        headers=second_headers,
    )
    assert cross_tenant_get.status_code == 404

    cross_tenant_approve = await client.post(
        f"/api/v1/ai/approvals/{approval_id}/approve",
        headers=second_headers,
        json={},
    )
    assert cross_tenant_approve.status_code == 404
