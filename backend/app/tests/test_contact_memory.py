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


async def _create_contact(client: AsyncClient, headers: dict[str, str], **overrides) -> dict:
    body = {"full_name": "Ada Lovelace", "email": "ada@example.com"}
    body.update(overrides)
    response = await client.post("/api/v1/contacts", headers=headers, json=body)
    assert response.status_code == 201
    return response.json()


async def _create_call_conversation(client: AsyncClient, headers: dict[str, str], text: str) -> dict:
    response = await client.post(
        "/api/v1/calls/text",
        headers=headers,
        json={"title": "Pricing discussion", "transcript_text": text},
    )
    assert response.status_code == 201
    return response.json()["conversation"]


async def _link_conversation(
    client: AsyncClient, headers: dict[str, str], contact_id: str, conversation_id: str
) -> None:
    response = await client.post(
        f"/api/v1/contacts/{contact_id}/link-conversation",
        headers=headers,
        json={"conversation_id": conversation_id},
    )
    assert response.status_code == 204


async def _connect_gmail(client: AsyncClient, headers: dict[str, str]) -> dict:
    start = await client.post("/api/v1/email/gmail/connect", headers=headers)
    assert start.status_code == 200
    callback = await client.get(
        "/api/v1/email/gmail/callback",
        params={"code": "mock-code", "state": start.json()["state"]},
    )
    assert callback.status_code == 200
    return callback.json()


async def test_customer_memory_synthesizes_conversation_task_and_appointment(client: AsyncClient):
    headers = await _auth_headers(client, "memory-full@example.com")
    contact = await _create_contact(client, headers, full_name="Ahmet Yilmaz")

    conversation = await _create_call_conversation(
        client, headers, "We discussed the domain transfer and next steps for pricing."
    )
    await _link_conversation(client, headers, contact["id"], conversation["id"])

    analysis_response = await client.post(
        f"/api/v1/ai/analysis/conversations/{conversation['id']}", headers=headers
    )
    assert analysis_response.status_code == 201

    task_response = await client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"title": "Send proposal", "contact_id": contact["id"]},
    )
    assert task_response.status_code == 201

    future_start = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
    future_end = (datetime.now(timezone.utc) + timedelta(days=3, hours=1)).isoformat()
    appointment_response = await client.post(
        "/api/v1/appointments",
        headers=headers,
        json={
            "title": "Follow-up call",
            "start_at": future_start,
            "end_at": future_end,
            "contact_id": contact["id"],
        },
    )
    assert appointment_response.status_code == 201

    memory_response = await client.get(f"/api/v1/contacts/{contact['id']}/memory", headers=headers)
    assert memory_response.status_code == 200
    memory = memory_response.json()

    assert memory["contact_id"] == contact["id"]
    assert memory["full_name"] == "Ahmet Yilmaz"
    assert memory["last_conversation"]["id"] == conversation["id"]
    assert memory["last_topic"] is not None
    assert memory["pending_items_count"] == 1
    assert memory["next_appointment"]["title"] == "Follow-up call"


async def test_customer_memory_matches_last_email_by_address(client: AsyncClient):
    headers = await _auth_headers(client, "memory-email@example.com")
    contact = await _create_contact(
        client, headers, full_name="Sender Contact", email="sender@example.com"
    )

    account = await _connect_gmail(client, headers)
    sync_response = await client.post(
        f"/api/v1/email/accounts/{account['id']}/sync", headers=headers
    )
    assert sync_response.status_code == 200

    memory_response = await client.get(f"/api/v1/contacts/{contact['id']}/memory", headers=headers)
    assert memory_response.status_code == 200
    last_email = memory_response.json()["last_email"]
    assert last_email is not None
    assert last_email["from_address"] == "sender@example.com"


async def test_customer_memory_is_empty_for_contact_with_no_activity(client: AsyncClient):
    headers = await _auth_headers(client, "memory-empty@example.com")
    contact = await _create_contact(client, headers, full_name="Nobody Yet")

    response = await client.get(f"/api/v1/contacts/{contact['id']}/memory", headers=headers)
    assert response.status_code == 200
    memory = response.json()
    assert memory["last_conversation"] is None
    assert memory["last_email"] is None
    assert memory["last_topic"] is None
    assert memory["pending_items_count"] == 0
    assert memory["open_deals_count"] == 0
    assert memory["open_deals_total_value"] == 0
    assert memory["next_appointment"] is None


async def test_customer_memory_reflects_open_deals(client: AsyncClient):
    headers = await _auth_headers(client, "memory-deals@example.com")
    contact = await _create_contact(client, headers, full_name="Deal Contact")

    open_response = await client.post(
        "/api/v1/deals",
        headers=headers,
        json={
            "title": "Open opportunity",
            "value": 1000,
            "stage": "proposal_sent",
            "contact_id": contact["id"],
        },
    )
    assert open_response.status_code == 201
    another_open_response = await client.post(
        "/api/v1/deals",
        headers=headers,
        json={
            "title": "Second opportunity",
            "value": 500,
            "stage": "negotiation",
            "contact_id": contact["id"],
        },
    )
    assert another_open_response.status_code == 201
    won_response = await client.post(
        "/api/v1/deals",
        headers=headers,
        json={
            "title": "Closed opportunity",
            "value": 9999,
            "stage": "won",
            "contact_id": contact["id"],
        },
    )
    assert won_response.status_code == 201

    memory_response = await client.get(f"/api/v1/contacts/{contact['id']}/memory", headers=headers)
    assert memory_response.status_code == 200
    memory = memory_response.json()
    assert memory["open_deals_count"] == 2
    assert memory["open_deals_total_value"] == 1500


async def test_customer_memory_is_tenant_scoped(client: AsyncClient):
    first_headers = await _auth_headers(client, "memory-tenant-one@example.com")
    second_headers = await _auth_headers(client, "memory-tenant-two@example.com")
    contact = await _create_contact(client, first_headers)

    response = await client.get(f"/api/v1/contacts/{contact['id']}/memory", headers=second_headers)
    assert response.status_code == 404