from httpx import AsyncClient


async def _auth_headers(client: AsyncClient, email: str) -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "SuperSecret123", "display_name": "Test User"},
    )
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


async def test_submit_feedback_requires_auth(client: AsyncClient):
    response = await client.post(
        "/api/v1/feedback", json={"category": "bug", "message": "Something broke."}
    )
    assert response.status_code == 401


async def test_submit_feedback_succeeds(client: AsyncClient):
    headers = await _auth_headers(client, "feedback@example.com")
    response = await client.post(
        "/api/v1/feedback",
        headers=headers,
        json={"category": "idea", "message": "Would love dark mode charts.", "page_url": "/analitik"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["category"] == "idea"
    assert body["message"] == "Would love dark mode charts."
    assert body["page_url"] == "/analitik"


async def test_submit_feedback_rejects_unknown_category(client: AsyncClient):
    headers = await _auth_headers(client, "feedback-bad-category@example.com")
    response = await client.post(
        "/api/v1/feedback",
        headers=headers,
        json={"category": "not-a-real-category", "message": "hi"},
    )
    assert response.status_code == 422


async def test_feedback_submission_is_rate_limited(client: AsyncClient):
    headers = await _auth_headers(client, "feedback-ratelimit@example.com")
    for _ in range(5):
        response = await client.post(
            "/api/v1/feedback", headers=headers, json={"category": "other", "message": "spam?"}
        )
        assert response.status_code == 201

    blocked = await client.post(
        "/api/v1/feedback", headers=headers, json={"category": "other", "message": "one more"}
    )
    assert blocked.status_code == 429
