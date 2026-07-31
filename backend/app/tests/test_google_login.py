from urllib.parse import parse_qs, urlparse

from httpx import AsyncClient


async def _start_google_login(client: AsyncClient) -> dict:
    response = await client.get("/api/v1/auth/google/login")
    assert response.status_code == 200
    return response.json()


def _query(location: str) -> dict[str, str]:
    parsed = urlparse(location)
    return {k: v[0] for k, v in parse_qs(parsed.query).items()}


async def _login_with_mock_google(client: AsyncClient) -> dict:
    start = await _start_google_login(client)
    state = _query(start["authorize_url"])["state"]

    callback = await client.get(
        "/api/v1/auth/google/callback", params={"code": "mock-code", "state": state}
    )
    assert callback.status_code in {302, 307}
    login_code = _query(callback.headers["location"])["login_code"]

    exchange = await client.post("/api/v1/auth/google/exchange", json={"login_code": login_code})
    assert exchange.status_code == 200
    return exchange.json()


async def test_google_login_start_returns_authorize_url_with_login_scope(client: AsyncClient):
    start = await _start_google_login(client)
    assert "authorize_url" in start
    assert "accounts.google.com" in start["authorize_url"]
    assert "openid" in start["authorize_url"]
    assert "email" in start["authorize_url"]
    assert "profile" in start["authorize_url"]


async def test_google_login_callback_rejects_invalid_state(client: AsyncClient):
    response = await client.get(
        "/api/v1/auth/google/callback", params={"code": "mock-code", "state": "bogus-state"}
    )
    assert response.status_code in {302, 307}
    assert _query(response.headers["location"]).get("google_error") == "1"


async def test_google_login_callback_rejects_state_replay(client: AsyncClient):
    start = await _start_google_login(client)
    state = _query(start["authorize_url"])["state"]

    first = await client.get(
        "/api/v1/auth/google/callback", params={"code": "mock-code", "state": state}
    )
    assert first.status_code in {302, 307}

    replay = await client.get(
        "/api/v1/auth/google/callback", params={"code": "mock-code", "state": state}
    )
    assert replay.status_code in {302, 307}
    assert _query(replay.headers["location"]).get("google_error") == "1"


async def test_google_login_creates_new_account_and_exchange_yields_tokens(client: AsyncClient):
    tokens = await _login_with_mock_google(client)
    assert tokens["access_token"]
    assert tokens["mfa_required"] is False

    me = await client.get(
        "/api/v1/users/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert me.status_code == 200
    assert me.json()["is_email_verified"] is True


async def test_google_login_exchange_code_is_single_use(client: AsyncClient):
    start = await _start_google_login(client)
    state = _query(start["authorize_url"])["state"]
    callback = await client.get(
        "/api/v1/auth/google/callback", params={"code": "mock-code", "state": state}
    )
    login_code = _query(callback.headers["location"])["login_code"]

    first = await client.post("/api/v1/auth/google/exchange", json={"login_code": login_code})
    assert first.status_code == 200

    replay = await client.post("/api/v1/auth/google/exchange", json={"login_code": login_code})
    assert replay.status_code == 401


async def test_two_google_logins_create_distinct_accounts(client: AsyncClient):
    first_tokens = await _login_with_mock_google(client)
    second_tokens = await _login_with_mock_google(client)

    first_me = await client.get(
        "/api/v1/users/me", headers={"Authorization": f"Bearer {first_tokens['access_token']}"}
    )
    second_me = await client.get(
        "/api/v1/users/me", headers={"Authorization": f"Bearer {second_tokens['access_token']}"}
    )
    assert first_me.json()["id"] != second_me.json()["id"]
