from httpx import AsyncClient


async def _register(client: AsyncClient, email: str) -> dict:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "SuperSecret123", "display_name": "Test User"},
    )
    assert response.status_code == 201
    return response.json()


async def test_anonymous_client_error_report_is_accepted(client: AsyncClient):
    response = await client.post(
        "/api/v1/client-errors",
        json={"message": "TypeError: boom", "stack": "at x (app.js:1:1)", "url": "https://example.com/giris"},
    )
    assert response.status_code == 204


async def test_authenticated_client_error_report_attaches_user(client: AsyncClient):
    tokens = await _register(client, email="reporter@example.com")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    report_response = await client.post(
        "/api/v1/client-errors",
        headers=headers,
        json={"message": "ReferenceError: x is not defined", "context": "app-error-boundary"},
    )
    assert report_response.status_code == 204

    list_response = await client.get("/api/v1/client-errors", headers=headers)
    assert list_response.status_code == 200
    messages = [item["message"] for item in list_response.json()]
    assert "ReferenceError: x is not defined" in messages
    matching = next(item for item in list_response.json() if item["message"] == "ReferenceError: x is not defined")
    assert matching["user_id"] is not None
    assert matching["context"] == "app-error-boundary"


async def test_listing_client_errors_requires_authentication(client: AsyncClient):
    response = await client.get("/api/v1/client-errors")
    assert response.status_code == 401


async def test_client_error_report_rejects_empty_message(client: AsyncClient):
    response = await client.post("/api/v1/client-errors", json={"message": ""})
    assert response.status_code == 422
