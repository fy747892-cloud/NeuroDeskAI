import pyotp
from httpx import AsyncClient


async def _register(client: AsyncClient, email: str = "user@example.com") -> dict:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "SuperSecret123", "display_name": "Test User"},
    )
    assert response.status_code == 201
    return response.json()


async def test_register_success(client: AsyncClient):
    body = await _register(client)
    assert "access_token" in body
    assert "refresh_token" in body


async def test_register_duplicate_email_conflicts(client: AsyncClient):
    await _register(client, email="dupe@example.com")
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "dupe@example.com", "password": "SuperSecret123", "display_name": "Dupe"},
    )
    assert response.status_code == 409


async def test_register_rejects_short_password(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "short@example.com", "password": "short", "display_name": "Short"},
    )
    assert response.status_code == 422


async def test_login_success(client: AsyncClient):
    await _register(client, email="login@example.com")
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "SuperSecret123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


async def test_login_wrong_password_fails(client: AsyncClient):
    await _register(client, email="wrongpass@example.com")
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "wrongpass@example.com", "password": "incorrect"},
    )
    assert response.status_code == 401


async def test_login_rate_limit(client: AsyncClient):
    for _ in range(5):
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "ratelimited@example.com", "password": "incorrect"},
        )
        assert response.status_code == 401

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "ratelimited@example.com", "password": "incorrect"},
    )
    assert response.status_code == 429


async def test_protected_route_requires_token(client: AsyncClient):
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401


async def test_protected_route_with_valid_token(client: AsyncClient):
    tokens = await _register(client, email="me@example.com")
    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"
    assert response.json()["profile"]["full_name"] == "Test User"


async def test_update_profile_writes_current_user_profile(client: AsyncClient):
    tokens = await _register(client, email="profile@example.com")
    response = await client.patch(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        json={"full_name": "Updated User", "title": "Founder"},
    )
    assert response.status_code == 200
    assert response.json()["profile"]["full_name"] == "Updated User"
    assert response.json()["profile"]["title"] == "Founder"


async def test_current_organization_and_members_use_owner_membership(client: AsyncClient):
    tokens = await _register(client, email="org@example.com")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    org_response = await client.get("/api/v1/organizations/current", headers=headers)
    assert org_response.status_code == 200
    assert org_response.json()["name"] == "Test User"

    members_response = await client.get("/api/v1/organizations/members", headers=headers)
    assert members_response.status_code == 200
    assert members_response.json()[0]["role"] == "owner"


async def test_owner_can_update_current_organization(client: AsyncClient):
    tokens = await _register(client, email="orgupdate@example.com")
    response = await client.patch(
        "/api/v1/organizations/current",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        json={"name": "Updated Workspace"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Workspace"


async def test_owner_can_create_new_active_organization(client: AsyncClient):
    tokens = await _register(client, email="orgcreate@example.com")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    create_response = await client.post(
        "/api/v1/organizations",
        headers=headers,
        json={"name": "Second Workspace"},
    )
    assert create_response.status_code == 201
    created_org_id = create_response.json()["id"]
    assert create_response.json()["name"] == "Second Workspace"

    current_response = await client.get("/api/v1/organizations/current", headers=headers)
    assert current_response.status_code == 200
    assert current_response.json()["id"] == created_org_id

    members_response = await client.get("/api/v1/organizations/members", headers=headers)
    assert members_response.status_code == 200
    assert members_response.json()[0]["role"] == "owner"


async def test_owner_can_read_tenant_scoped_audit_logs(client: AsyncClient):
    first_tokens = await _register(client, email="audit-one@example.com")
    second_tokens = await _register(client, email="audit-two@example.com")

    first_headers = {"Authorization": f"Bearer {first_tokens['access_token']}"}
    second_headers = {"Authorization": f"Bearer {second_tokens['access_token']}"}

    first_update = await client.patch(
        "/api/v1/organizations/current",
        headers=first_headers,
        json={"name": "First Workspace"},
    )
    assert first_update.status_code == 200
    first_org_id = first_update.json()["id"]

    second_update = await client.patch(
        "/api/v1/organizations/current",
        headers=second_headers,
        json={"name": "Second Workspace"},
    )
    assert second_update.status_code == 200
    second_org_id = second_update.json()["id"]

    audit_response = await client.get("/api/v1/audit-logs", headers=first_headers)
    assert audit_response.status_code == 200
    logs = audit_response.json()
    assert any(log["entity_id"] == first_org_id for log in logs)
    assert all(log["entity_id"] != second_org_id for log in logs)


async def test_owner_cannot_change_own_organization_role(client: AsyncClient):
    tokens = await _register(client, email="selfrole@example.com")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    members_response = await client.get("/api/v1/organizations/members", headers=headers)
    assert members_response.status_code == 200
    member_id = members_response.json()[0]["id"]

    role_response = await client.patch(
        f"/api/v1/organizations/members/{member_id}/role",
        headers=headers,
        json={"role": "viewer"},
    )
    assert role_response.status_code == 403


async def test_refresh_rotation_and_reuse_detection(client: AsyncClient):
    tokens = await _register(client, email="refresh@example.com")
    old_refresh_token = tokens["refresh_token"]

    refreshed = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": old_refresh_token}
    )
    assert refreshed.status_code == 200
    new_refresh_token = refreshed.json()["refresh_token"]
    assert new_refresh_token != old_refresh_token

    reuse_response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": old_refresh_token}
    )
    assert reuse_response.status_code == 401

    # Reuse detection revokes all sessions, so even the rotated token is now dead.
    followup_response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": new_refresh_token}
    )
    assert followup_response.status_code == 401


async def test_logout_invalidates_refresh_token(client: AsyncClient):
    tokens = await _register(client, email="logout@example.com")

    logout_response = await client.post(
        "/api/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]}
    )
    assert logout_response.status_code == 204

    refresh_response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert refresh_response.status_code == 401


async def test_logout_all_revokes_every_session(client: AsyncClient):
    tokens = await _register(client, email="logoutall@example.com")

    second_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "logoutall@example.com", "password": "SuperSecret123"},
    )
    assert second_login.status_code == 200
    second_refresh_token = second_login.json()["refresh_token"]

    logout_all_response = await client.post(
        "/api/v1/auth/logout-all",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert logout_all_response.status_code == 204

    refresh_response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": second_refresh_token}
    )
    assert refresh_response.status_code == 401


async def test_list_sessions_shows_each_login(client: AsyncClient):
    tokens = await _register(client, email="sessions@example.com")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    await client.post(
        "/api/v1/auth/login",
        json={"email": "sessions@example.com", "password": "SuperSecret123"},
    )

    response = await client.get("/api/v1/auth/sessions", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 2


async def test_revoke_single_session_only_kills_that_device(client: AsyncClient):
    tokens = await _register(client, email="revokeone@example.com")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    sessions_before = await client.get("/api/v1/auth/sessions", headers=headers)
    original_session_ids = {s["id"] for s in sessions_before.json()}

    second_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "revokeone@example.com", "password": "SuperSecret123"},
    )
    second_refresh_token = second_login.json()["refresh_token"]

    sessions_response = await client.get("/api/v1/auth/sessions", headers=headers)
    sessions = sessions_response.json()
    assert len(sessions) == 2

    new_session_id = next(s["id"] for s in sessions if s["id"] not in original_session_ids)
    revoke_response = await client.delete(
        f"/api/v1/auth/sessions/{new_session_id}", headers=headers
    )
    assert revoke_response.status_code == 204

    # Check the untouched session first: attempting the revoked token below
    # trips reuse-detection, which (by design, see
    # test_refresh_rotation_and_reuse_detection) revokes every session for
    # the user as a compromise response — checking it after would always
    # fail regardless of whether single-session revoke was correctly scoped.
    still_alive_refresh_response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert still_alive_refresh_response.status_code == 200

    revoked_refresh_response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": second_refresh_token}
    )
    assert revoked_refresh_response.status_code == 401


async def test_cannot_revoke_another_users_session(client: AsyncClient):
    tokens_a = await _register(client, email="sessionowner@example.com")
    tokens_b = await _register(client, email="sessionintruder@example.com")

    sessions_response = await client.get(
        "/api/v1/auth/sessions", headers={"Authorization": f"Bearer {tokens_a['access_token']}"}
    )
    session_id = sessions_response.json()[0]["id"]

    revoke_response = await client.delete(
        f"/api/v1/auth/sessions/{session_id}",
        headers={"Authorization": f"Bearer {tokens_b['access_token']}"},
    )
    assert revoke_response.status_code == 403


async def _enable_totp(client: AsyncClient, email: str) -> tuple[dict, str, list[str]]:
    tokens = await _register(client, email=email)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    setup_response = await client.post("/api/v1/auth/2fa/setup", headers=headers)
    assert setup_response.status_code == 200
    secret = setup_response.json()["secret"]

    code = pyotp.TOTP(secret).now()
    verify_response = await client.post(
        "/api/v1/auth/2fa/verify", headers=headers, json={"code": code}
    )
    assert verify_response.status_code == 200
    recovery_codes = verify_response.json()["recovery_codes"]
    assert len(recovery_codes) == 8

    return tokens, secret, recovery_codes


async def test_totp_setup_and_verify_enables_2fa(client: AsyncClient):
    tokens = await _register(client, email="totpsetup@example.com")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    status_before = await client.get("/api/v1/auth/2fa/status", headers=headers)
    assert status_before.json()["enabled"] is False

    setup_response = await client.post("/api/v1/auth/2fa/setup", headers=headers)
    assert setup_response.status_code == 200
    secret = setup_response.json()["secret"]

    valid_code = pyotp.TOTP(secret).now()
    verify_response = await client.post(
        "/api/v1/auth/2fa/verify", headers=headers, json={"code": valid_code}
    )
    assert verify_response.status_code == 200
    assert len(verify_response.json()["recovery_codes"]) == 8

    status_after = await client.get("/api/v1/auth/2fa/status", headers=headers)
    assert status_after.json()["enabled"] is True


async def test_login_requires_totp_code_once_2fa_enabled(client: AsyncClient):
    _, secret, _ = await _enable_totp(client, "totplogin@example.com")

    password_only = await client.post(
        "/api/v1/auth/login",
        json={"email": "totplogin@example.com", "password": "SuperSecret123"},
    )
    assert password_only.status_code == 200
    assert password_only.json()["mfa_required"] is True
    assert password_only.json()["access_token"] is None

    wrong_code = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "totplogin@example.com",
            "password": "SuperSecret123",
            "totp_code": "000000",
        },
    )
    assert wrong_code.status_code == 401

    valid_code = pyotp.TOTP(secret).now()
    with_code = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "totplogin@example.com",
            "password": "SuperSecret123",
            "totp_code": valid_code,
        },
    )
    assert with_code.status_code == 200
    assert with_code.json()["mfa_required"] is False
    assert "access_token" in with_code.json()


async def test_login_with_recovery_code_is_single_use(client: AsyncClient):
    _, _, recovery_codes = await _enable_totp(client, "totprecovery@example.com")
    code = recovery_codes[0]

    first_use = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "totprecovery@example.com",
            "password": "SuperSecret123",
            "recovery_code": code,
        },
    )
    assert first_use.status_code == 200
    assert "access_token" in first_use.json()

    second_use = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "totprecovery@example.com",
            "password": "SuperSecret123",
            "recovery_code": code,
        },
    )
    assert second_use.status_code == 401


async def test_disable_totp_requires_valid_code(client: AsyncClient):
    tokens, secret, _ = await _enable_totp(client, "totpdisable@example.com")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    wrong_code_response = await client.post(
        "/api/v1/auth/2fa/disable", headers=headers, json={"code": "000000"}
    )
    assert wrong_code_response.status_code == 401

    valid_code = pyotp.TOTP(secret).now()
    disable_response = await client.post(
        "/api/v1/auth/2fa/disable", headers=headers, json={"code": valid_code}
    )
    assert disable_response.status_code == 204

    status_response = await client.get("/api/v1/auth/2fa/status", headers=headers)
    assert status_response.json()["enabled"] is False

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "totpdisable@example.com", "password": "SuperSecret123"},
    )
    assert login_response.status_code == 200
    assert login_response.json()["mfa_required"] is False
