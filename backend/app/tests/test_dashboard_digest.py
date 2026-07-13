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


async def _create_contact(client: AsyncClient, headers: dict[str, str]) -> dict:
    response = await client.post(
        "/api/v1/contacts", headers=headers, json={"full_name": "Ahmet Yilmaz"}
    )
    assert response.status_code == 201
    return response.json()


async def _create_overdue_task(client: AsyncClient, headers: dict[str, str], contact_id: str) -> dict:
    due_at = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    response = await client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"title": "Send proposal", "due_at": due_at, "contact_id": contact_id},
    )
    assert response.status_code == 201
    return response.json()


async def _create_appointment(
    client: AsyncClient, headers: dict[str, str], *, start_at: datetime, end_at: datetime
) -> dict:
    response = await client.post(
        "/api/v1/appointments",
        headers=headers,
        json={
            "title": "Follow-up call",
            "start_at": start_at.isoformat(),
            "end_at": end_at.isoformat(),
        },
    )
    assert response.status_code == 201
    return response.json()


async def _create_call(client: AsyncClient, headers: dict[str, str], *, started_at: datetime) -> dict:
    response = await client.post(
        "/api/v1/calls/text",
        headers=headers,
        json={
            "title": "Domain transfer call",
            "transcript_text": "We discussed the domain transfer.",
            "started_at": started_at.isoformat(),
        },
    )
    assert response.status_code == 201
    return response.json()


async def _connect_gmail_and_sync(client: AsyncClient, headers: dict[str, str]) -> dict:
    start = await client.post("/api/v1/email/gmail/connect", headers=headers)
    assert start.status_code == 200
    callback = await client.get(
        "/api/v1/email/gmail/callback",
        params={"code": "mock-code", "state": start.json()["state"]},
    )
    assert callback.status_code == 200
    account = callback.json()
    sync_response = await client.post(
        f"/api/v1/email/accounts/{account['id']}/sync", headers=headers
    )
    assert sync_response.status_code == 200
    return account


async def _setup_digest_scenario(client: AsyncClient, headers: dict[str, str]) -> None:
    now = datetime.now(timezone.utc)
    contact = await _create_contact(client, headers)
    await _create_overdue_task(client, headers, contact["id"])

    await _create_appointment(
        client, headers, start_at=now + timedelta(hours=1), end_at=now + timedelta(hours=2)
    )
    # Outside every window (daily "yesterday", weekly "last 7 days", weekly "this week").
    await _create_appointment(
        client, headers, start_at=now + timedelta(days=10), end_at=now + timedelta(days=10, hours=1)
    )

    await _create_call(client, headers, started_at=now - timedelta(days=1))
    await _create_call(client, headers, started_at=now - timedelta(days=10))

    await _connect_gmail_and_sync(client, headers)


async def test_daily_digest_computes_exact_counts_and_narrative(client: AsyncClient):
    headers = await _auth_headers(client, "digest-daily@example.com")
    await _setup_digest_scenario(client, headers)

    response = await client.get(
        "/api/v1/dashboard/digest", headers=headers, params={"period": "daily"}
    )
    assert response.status_code == 200
    digest = response.json()

    assert digest["period"] == "daily"
    assert digest["appointments_count"] == 1
    assert digest["calls_count"] == 1
    assert digest["contacts_awaiting_reply_count"] == 1
    assert digest["unanswered_emails_count"] == 10
    assert digest["open_deals_count"] == 0
    assert digest["narrative"] == (
        "Bugün 1 toplantın var. Dün 1 görüşme yaptın. "
        "1 müşteri geri dönüş bekliyor. 10 e-postaya henüz cevap verilmedi."
    )


async def test_weekly_digest_excludes_out_of_window_data(client: AsyncClient):
    headers = await _auth_headers(client, "digest-weekly@example.com")
    await _setup_digest_scenario(client, headers)

    response = await client.get(
        "/api/v1/dashboard/digest", headers=headers, params={"period": "weekly"}
    )
    assert response.status_code == 200
    digest = response.json()

    assert digest["period"] == "weekly"
    assert digest["appointments_count"] == 1
    assert digest["calls_count"] == 1
    assert digest["narrative"].startswith("Bu hafta 1 toplantın var. Geçen hafta 1 görüşme yaptın.")


async def test_mark_replied_reduces_unanswered_email_count(client: AsyncClient):
    headers = await _auth_headers(client, "digest-mark-replied@example.com")
    account = await _connect_gmail_and_sync(client, headers)

    messages_response = await client.get(
        f"/api/v1/email/accounts/{account['id']}/messages", headers=headers
    )
    assert messages_response.status_code == 200
    message_id = messages_response.json()[0]["id"]

    before = await client.get(
        "/api/v1/dashboard/digest", headers=headers, params={"period": "daily"}
    )
    assert before.json()["unanswered_emails_count"] == 10

    mark_response = await client.post(
        f"/api/v1/email/messages/{message_id}/mark-replied", headers=headers
    )
    assert mark_response.status_code == 200
    assert mark_response.json()["is_replied"] is True

    after = await client.get(
        "/api/v1/dashboard/digest", headers=headers, params={"period": "daily"}
    )
    assert after.json()["unanswered_emails_count"] == 9


async def test_digest_reflects_open_deals_count(client: AsyncClient):
    headers = await _auth_headers(client, "digest-deals@example.com")

    open_response = await client.post(
        "/api/v1/deals", headers=headers, json={"title": "Open deal", "stage": "lead"}
    )
    assert open_response.status_code == 201
    won_response = await client.post(
        "/api/v1/deals", headers=headers, json={"title": "Won deal", "stage": "won"}
    )
    assert won_response.status_code == 201

    response = await client.get("/api/v1/dashboard/digest", headers=headers)
    assert response.status_code == 200
    assert response.json()["open_deals_count"] == 1


async def test_digest_shares_daily_ai_quota_with_chat(client: AsyncClient):
    headers = await _auth_headers(client, "digest-quota@example.com")

    for index in range(4):
        response = await client.post(
            "/api/v1/ai/chat", headers=headers, json={"message": f"chat message {index}"}
        )
        assert response.status_code == 201

    digest_response = await client.get("/api/v1/dashboard/digest", headers=headers)
    assert digest_response.status_code == 200

    blocked_response = await client.get("/api/v1/dashboard/digest", headers=headers)
    assert blocked_response.status_code == 429
    assert blocked_response.json()["error_code"] == "quota_exceeded"