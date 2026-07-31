from httpx import AsyncClient


async def _register(client: AsyncClient, email: str = "user@example.com") -> dict:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "SuperSecret123", "display_name": "Test User"},
    )
    assert response.status_code == 201
    return response.json()


async def test_export_my_data_includes_account_and_profile(client: AsyncClient):
    tokens = await _register(client, email="export@example.com")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    response = await client.get("/api/v1/users/me/export", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["account"]["email"] == "export@example.com"
    assert body["profile"]["full_name"] == "Test User"
    assert body["organization"]["role"] == "owner"
    assert body["security"]["totp_enabled"] is False
    assert len(body["active_sessions"]) == 1


async def test_delete_account_requires_correct_password(client: AsyncClient):
    tokens = await _register(client, email="wrongpassdelete@example.com")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    response = await client.request(
        "DELETE", "/api/v1/users/me", headers=headers, json={"password": "wrong-password"}
    )
    assert response.status_code == 401

    still_works = await client.get("/api/v1/users/me", headers=headers)
    assert still_works.status_code == 200


async def test_delete_account_soft_deletes_and_revokes_sessions(client: AsyncClient):
    tokens = await _register(client, email="delete@example.com")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    response = await client.request(
        "DELETE", "/api/v1/users/me", headers=headers, json={"password": "SuperSecret123"}
    )
    assert response.status_code == 204

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "delete@example.com", "password": "SuperSecret123"},
    )
    assert login_response.status_code == 401

    refresh_response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert refresh_response.status_code == 401


async def test_sole_owner_can_delete_but_owner_with_other_members_is_blocked(client: AsyncClient):
    owner_tokens = await _register(client, email="soleowner@example.com")
    owner_headers = {"Authorization": f"Bearer {owner_tokens['access_token']}"}

    invite_response = await client.post(
        "/api/v1/organizations/members/invite",
        headers=owner_headers,
        json={"email": "invitee@example.com", "role": "member"},
    )
    assert invite_response.status_code == 201

    blocked_response = await client.request(
        "DELETE", "/api/v1/users/me", headers=owner_headers, json={"password": "SuperSecret123"}
    )
    assert blocked_response.status_code == 409
