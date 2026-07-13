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


async def _create_call_conversation(client: AsyncClient, headers: dict[str, str], text: str) -> str:
    response = await client.post(
        "/api/v1/calls/text",
        headers=headers,
        json={"title": "AI Candidate Conversation", "transcript_text": text},
    )
    assert response.status_code == 201
    return response.json()["conversation"]["id"]


async def test_request_conversation_analysis_returns_mock_results(client: AsyncClient):
    headers = await _auth_headers(client, "ai-success@example.com")
    conversation_id = await _create_call_conversation(
        client,
        headers,
        "Customer wants a follow-up appointment and a clear next step.",
    )

    response = await client.post(
        f"/api/v1/ai/analysis/conversations/{conversation_id}",
        headers=headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "completed"
    assert body["attempts"] == 1
    result_types = {result["result_type"] for result in body["results"]}
    assert result_types == {
        "conversation_summary",
        "task_extraction",
        "appointment_extraction",
        "deal_extraction",
    }
    summary = next(result for result in body["results"] if result["result_type"] == "conversation_summary")
    assert "summary_text" in summary["result_payload"]
    assert summary["model_config"]["provider"] == "mock"

    job_response = await client.get(f"/api/v1/ai/analysis/jobs/{body['id']}", headers=headers)
    assert job_response.status_code == 200
    assert job_response.json()["status"] == "completed"

    list_response = await client.get("/api/v1/ai/analysis/jobs", headers=headers)
    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == body["id"]


async def test_ai_analysis_job_is_tenant_scoped(client: AsyncClient):
    first_headers = await _auth_headers(client, "ai-tenant-one@example.com")
    second_headers = await _auth_headers(client, "ai-tenant-two@example.com")
    conversation_id = await _create_call_conversation(
        client,
        first_headers,
        "Tenant one transcript.",
    )
    job_response = await client.post(
        f"/api/v1/ai/analysis/conversations/{conversation_id}",
        headers=first_headers,
    )
    assert job_response.status_code == 201
    job_id = job_response.json()["id"]

    cross_tenant_response = await client.get(
        f"/api/v1/ai/analysis/jobs/{job_id}",
        headers=second_headers,
    )
    assert cross_tenant_response.status_code == 404


async def test_ai_analysis_fails_without_transcript(client: AsyncClient):
    headers = await _auth_headers(client, "ai-no-transcript@example.com")
    conversation_response = await client.post(
        "/api/v1/conversations",
        headers=headers,
        json={"title": "No Transcript"},
    )
    assert conversation_response.status_code == 201
    conversation_id = conversation_response.json()["id"]

    response = await client.post(
        f"/api/v1/ai/analysis/conversations/{conversation_id}",
        headers=headers,
    )
    assert response.status_code == 201
    assert response.json()["status"] == "failed"
    assert "no transcript" in response.json()["error_message"].lower()


async def test_failed_ai_analysis_job_can_be_retried(client: AsyncClient):
    headers = await _auth_headers(client, "ai-retry@example.com")
    conversation_id = await _create_call_conversation(
        client,
        headers,
        "This transcript intentionally contains [mock-fail].",
    )
    response = await client.post(
        f"/api/v1/ai/analysis/conversations/{conversation_id}",
        headers=headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "failed"
    assert body["attempts"] == 1

    retry_response = await client.post(
        f"/api/v1/ai/analysis/jobs/{body['id']}/retry",
        headers=headers,
    )
    assert retry_response.status_code == 200
    assert retry_response.json()["status"] == "failed"
    assert retry_response.json()["attempts"] == 2


async def test_deal_suggestion_can_be_approved_and_materialized(client: AsyncClient):
    headers = await _auth_headers(client, "ai-deal@example.com")
    conversation_id = await _create_call_conversation(
        client, headers, "We discussed a new pricing opportunity for the client."
    )

    analysis_response = await client.post(
        f"/api/v1/ai/analysis/conversations/{conversation_id}", headers=headers
    )
    assert analysis_response.status_code == 201
    body = analysis_response.json()
    deal_result = next(r for r in body["results"] if r["result_type"] == "deal_extraction")
    assert deal_result["result_payload"]["items"]

    approvals_response = await client.get("/api/v1/ai/approvals", headers=headers)
    assert approvals_response.status_code == 200
    deal_approval = next(
        a for a in approvals_response.json() if a["action_type"] == "deal"
    )
    assert deal_approval["status"] == "pending"

    approve_response = await client.post(
        f"/api/v1/ai/approvals/{deal_approval['id']}/approve", headers=headers, json={}
    )
    assert approve_response.status_code == 200
    assert approve_response.json()["status"] == "approved"

    create_response = await client.post(
        "/api/v1/deals/from-approval",
        headers=headers,
        json={"approval_id": deal_approval["id"]},
    )
    assert create_response.status_code == 201
    deal = create_response.json()
    assert deal["source_type"] == "ai_action_approval"
    assert deal["ai_action_approval_id"] == deal_approval["id"]

    duplicate_response = await client.post(
        "/api/v1/deals/from-approval",
        headers=headers,
        json={"approval_id": deal_approval["id"]},
    )
    assert duplicate_response.status_code == 409
