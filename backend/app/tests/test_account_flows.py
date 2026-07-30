import re

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


class _CapturingEmailProvider:
    def __init__(self):
        self.sent: list[dict] = []

    async def send(self, *, to_email: str, title: str, body: str) -> None:
        self.sent.append({"to_email": to_email, "title": title, "body": body})


def _capture_emails(monkeypatch) -> _CapturingEmailProvider:
    capture = _CapturingEmailProvider()
    monkeypatch.setattr("app.modules.auth.service.get_email_provider", lambda: capture)
    return capture


def _extract_token(body: str) -> str:
    match = re.search(r"token=([^\s]+)", body)
    assert match, f"No token found in email body: {body}"
    return match.group(1)


# ---------------------------------------------------------------------------
# Password reset
# ---------------------------------------------------------------------------


async def test_forgot_password_unknown_email_is_silent(client: AsyncClient, monkeypatch):
    capture = _capture_emails(monkeypatch)
    response = await client.post(
        "/api/v1/auth/forgot-password", json={"email": "nobody@example.com"}
    )
    assert response.status_code == 204
    assert capture.sent == []


async def test_forgot_password_then_reset_changes_password(client: AsyncClient, monkeypatch):
    await _register(client, email="resetme@example.com")
    capture = _capture_emails(monkeypatch)

    forgot_response = await client.post(
        "/api/v1/auth/forgot-password", json={"email": "resetme@example.com"}
    )
    assert forgot_response.status_code == 204
    assert len(capture.sent) == 1
    token = _extract_token(capture.sent[0]["body"])

    reset_response = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": "BrandNewPassword123"},
    )
    assert reset_response.status_code == 204

    old_password_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "resetme@example.com", "password": "SuperSecret123"},
    )
    assert old_password_login.status_code == 401

    new_password_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "resetme@example.com", "password": "BrandNewPassword123"},
    )
    assert new_password_login.status_code == 200


async def test_reset_password_token_is_single_use(client: AsyncClient, monkeypatch):
    await _register(client, email="onetime@example.com")
    capture = _capture_emails(monkeypatch)
    await client.post("/api/v1/auth/forgot-password", json={"email": "onetime@example.com"})
    token = _extract_token(capture.sent[0]["body"])

    first = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": "FirstNewPassword123"},
    )
    assert first.status_code == 204

    second = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": "SecondNewPassword123"},
    )
    assert second.status_code == 401


async def test_reset_password_rejects_garbage_token(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": "not-a-real-token", "new_password": "WhateverPassword123"},
    )
    assert response.status_code == 401


async def test_reset_password_revokes_existing_sessions(client: AsyncClient, monkeypatch):
    tokens = await _register(client, email="revokeme@example.com")
    capture = _capture_emails(monkeypatch)
    await client.post("/api/v1/auth/forgot-password", json={"email": "revokeme@example.com"})
    token = _extract_token(capture.sent[0]["body"])

    await client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": "AnotherPassword123"},
    )

    refresh_response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert refresh_response.status_code == 401


# ---------------------------------------------------------------------------
# Team invites
# ---------------------------------------------------------------------------


async def test_owner_can_invite_member_and_invitee_accepts(client: AsyncClient, monkeypatch):
    headers = await _auth_headers(client, "owner@example.com")
    capture = _capture_emails(monkeypatch)

    invite_response = await client.post(
        "/api/v1/organizations/members/invite",
        headers=headers,
        json={"email": "invitee@example.com", "role": "member"},
    )
    assert invite_response.status_code == 201
    assert invite_response.json()["status"] == "invited"
    assert invite_response.json()["role"] == "member"
    assert len(capture.sent) == 1
    token = _extract_token(capture.sent[0]["body"])

    members_response = await client.get("/api/v1/organizations/members", headers=headers)
    statuses = {member["email"]: member["status"] for member in members_response.json()}
    assert statuses["invitee@example.com"] == "invited"

    accept_response = await client.post(
        "/api/v1/auth/accept-invite",
        json={"token": token, "password": "InviteePassword123", "display_name": "Invitee Person"},
    )
    assert accept_response.status_code == 200
    assert "access_token" in accept_response.json()

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "invitee@example.com", "password": "InviteePassword123"},
    )
    assert login_response.status_code == 200

    members_after = await client.get("/api/v1/organizations/members", headers=headers)
    statuses_after = {member["email"]: member["status"] for member in members_after.json()}
    assert statuses_after["invitee@example.com"] == "active"


async def test_invite_rejects_already_registered_email(client: AsyncClient, monkeypatch):
    headers = await _auth_headers(client, "owner2@example.com")
    await _register(client, email="existing@example.com")
    _capture_emails(monkeypatch)

    response = await client.post(
        "/api/v1/organizations/members/invite",
        headers=headers,
        json={"email": "existing@example.com", "role": "member"},
    )
    assert response.status_code == 409


async def test_accept_invite_rejects_invalid_token(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/accept-invite",
        json={"token": "bogus", "password": "SomePassword123", "display_name": "Nobody"},
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Chat sessions
# ---------------------------------------------------------------------------


async def test_rename_and_delete_chat_session(client: AsyncClient):
    headers = await _auth_headers(client, "chatmanage@example.com")
    message_response = await client.post(
        "/api/v1/ai/chat", headers=headers, json={"message": "Merhaba"}
    )
    assert message_response.status_code == 201
    session_id = message_response.json()["session_id"]

    rename_response = await client.patch(
        f"/api/v1/ai/chat/sessions/{session_id}",
        headers=headers,
        json={"title": "Renamed session"},
    )
    assert rename_response.status_code == 200
    assert rename_response.json()["title"] == "Renamed session"

    delete_response = await client.delete(
        f"/api/v1/ai/chat/sessions/{session_id}", headers=headers
    )
    assert delete_response.status_code == 204

    list_response = await client.get("/api/v1/ai/chat/sessions", headers=headers)
    assert all(session["id"] != session_id for session in list_response.json())


async def test_cannot_rename_another_users_chat_session(client: AsyncClient):
    headers_a = await _auth_headers(client, "chatowner@example.com")
    headers_b = await _auth_headers(client, "chatintruder@example.com")

    message_response = await client.post(
        "/api/v1/ai/chat", headers=headers_a, json={"message": "Merhaba"}
    )
    session_id = message_response.json()["session_id"]

    response = await client.patch(
        f"/api/v1/ai/chat/sessions/{session_id}",
        headers=headers_b,
        json={"title": "Hijacked"},
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------


async def test_mark_all_notifications_read(client: AsyncClient):
    headers = await _auth_headers(client, "notifyall@example.com")
    task_response = await client.post(
        "/api/v1/tasks", headers=headers, json={"title": "Reminder me", "due_at": "2027-01-01T10:00:00Z"}
    )
    task_id = task_response.json()["id"]

    for remind_at in ("2020-01-01T00:00:00Z", "2020-01-02T00:00:00Z"):
        reminder_response = await client.post(
            f"/api/v1/tasks/{task_id}/reminders",
            headers=headers,
            json={"remind_at": remind_at, "channel": "in_app"},
        )
        assert reminder_response.status_code == 201

    process_response = await client.post("/api/v1/notifications/process-due", headers=headers)
    assert process_response.status_code == 200

    read_all_response = await client.post("/api/v1/notifications/read-all", headers=headers)
    assert read_all_response.status_code == 200
    assert read_all_response.json()["updated"] >= 1

    list_response = await client.get("/api/v1/notifications", headers=headers)
    assert all(item["read_at"] is not None for item in list_response.json())


# ---------------------------------------------------------------------------
# Repeating tasks / appointments
# ---------------------------------------------------------------------------


async def test_create_task_with_repeat_materializes_instances(client: AsyncClient):
    headers = await _auth_headers(client, "repeattask@example.com")
    response = await client.post(
        "/api/v1/tasks",
        headers=headers,
        json={
            "title": "Weekly check-in",
            "due_at": "2027-02-01T09:00:00Z",
            "repeat_count": 3,
            "repeat_interval_days": 7,
        },
    )
    assert response.status_code == 201

    list_response = await client.get("/api/v1/tasks", headers=headers)
    matching = [task for task in list_response.json() if task["title"] == "Weekly check-in"]
    assert len(matching) == 3
    due_dates = sorted(task["due_at"] for task in matching)
    assert due_dates[0] == "2027-02-01T09:00:00Z"


async def test_create_appointment_with_repeat_materializes_instances(client: AsyncClient):
    headers = await _auth_headers(client, "repeatappt@example.com")
    response = await client.post(
        "/api/v1/appointments",
        headers=headers,
        json={
            "title": "Weekly sync",
            "start_at": "2027-03-01T09:00:00Z",
            "end_at": "2027-03-01T09:30:00Z",
            "repeat_count": 2,
            "repeat_interval_days": 7,
        },
    )
    assert response.status_code == 201

    list_response = await client.get(
        "/api/v1/appointments",
        headers=headers,
        params={"start_date": "2027-01-01T00:00:00Z", "end_date": "2027-12-31T00:00:00Z"},
    )
    matching = [appt for appt in list_response.json() if appt["title"] == "Weekly sync"]
    assert len(matching) == 2


# ---------------------------------------------------------------------------
# Consent gating
# ---------------------------------------------------------------------------


async def test_disabling_ai_processing_blocks_conversation_analysis(client: AsyncClient):
    headers = await _auth_headers(client, "consentgate@example.com")

    consent_response = await client.patch(
        "/api/v1/users/me/consent",
        headers=headers,
        json={"ai_processing": False, "contact_memory": True, "operational_reminders": True},
    )
    assert consent_response.status_code == 200
    assert consent_response.json()["ai_processing"] is False

    call_response = await client.post(
        "/api/v1/calls/text",
        headers=headers,
        json={"title": "Gated Conversation", "transcript_text": "Follow up next week."},
    )
    conversation_id = call_response.json()["conversation"]["id"]

    analysis_response = await client.post(
        f"/api/v1/ai/analysis/conversations/{conversation_id}",
        headers=headers,
    )
    assert analysis_response.status_code == 422


async def test_consent_defaults_to_enabled(client: AsyncClient):
    headers = await _auth_headers(client, "consentdefault@example.com")
    response = await client.get("/api/v1/users/me/consent", headers=headers)
    assert response.status_code == 200
    assert response.json() == {
        "ai_processing": True,
        "contact_memory": True,
        "operational_reminders": True,
    }
