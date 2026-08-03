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


async def test_create_list_and_get_conversation(client: AsyncClient):
    headers = await _auth_headers(client, "conversation@example.com")

    create_response = await client.post(
        "/api/v1/conversations",
        headers=headers,
        json={"title": "Discovery Call", "participant_names": ["Ada", "Bora"]},
    )
    assert create_response.status_code == 201
    body = create_response.json()
    assert body["title"] == "Discovery Call"
    assert len(body["participants"]) == 2

    list_response = await client.get("/api/v1/conversations", headers=headers)
    assert list_response.status_code == 200
    assert list_response.json()["items"][0]["id"] == body["id"]

    detail_response = await client.get(f"/api/v1/conversations/{body['id']}", headers=headers)
    assert detail_response.status_code == 200
    assert detail_response.json()["title"] == "Discovery Call"


async def test_update_and_soft_delete_conversation(client: AsyncClient):
    headers = await _auth_headers(client, "conversation-delete@example.com")
    create_response = await client.post(
        "/api/v1/conversations",
        headers=headers,
        json={"title": "Old Title"},
    )
    conversation_id = create_response.json()["id"]

    update_response = await client.patch(
        f"/api/v1/conversations/{conversation_id}",
        headers=headers,
        json={"title": "New Title"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["title"] == "New Title"

    delete_response = await client.delete(f"/api/v1/conversations/{conversation_id}", headers=headers)
    assert delete_response.status_code == 204

    list_response = await client.get("/api/v1/conversations", headers=headers)
    assert list_response.status_code == 200
    assert list_response.json()["items"] == []

    detail_response = await client.get(f"/api/v1/conversations/{conversation_id}", headers=headers)
    assert detail_response.status_code == 404


async def test_conversation_is_tenant_scoped(client: AsyncClient):
    first_headers = await _auth_headers(client, "tenant-one@example.com")
    second_headers = await _auth_headers(client, "tenant-two@example.com")

    create_response = await client.post(
        "/api/v1/conversations",
        headers=first_headers,
        json={"title": "Tenant One Conversation"},
    )
    conversation_id = create_response.json()["id"]

    cross_tenant_response = await client.get(
        f"/api/v1/conversations/{conversation_id}",
        headers=second_headers,
    )
    assert cross_tenant_response.status_code == 404


async def test_create_call_from_text_creates_conversation_call_and_transcription(client: AsyncClient):
    headers = await _auth_headers(client, "call-text@example.com")

    response = await client.post(
        "/api/v1/calls/text",
        headers=headers,
        json={
            "title": "Manual Call",
            "transcript_text": "Customer asked for a follow-up next week.",
            "participant_names": ["Customer"],
            "call_direction": "outbound",
            "duration_seconds": 120,
            "language": "en",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["conversation"]["source_type"] == "call"
    assert body["call"]["call_direction"] == "outbound"
    assert body["transcription"]["transcript_text"] == "Customer asked for a follow-up next week."

    detail_response = await client.get(
        f"/api/v1/conversations/{body['conversation']['id']}",
        headers=headers,
    )
    assert detail_response.status_code == 200
    assert detail_response.json()["calls"][0]["transcriptions"][0]["language"] == "en"


async def test_add_participant_to_existing_conversation(client: AsyncClient):
    headers = await _auth_headers(client, "participant@example.com")
    create_response = await client.post(
        "/api/v1/conversations",
        headers=headers,
        json={"title": "Participant Call"},
    )
    conversation_id = create_response.json()["id"]

    participant_response = await client.post(
        f"/api/v1/conversations/{conversation_id}/participants",
        headers=headers,
        json={"display_name": "New Person"},
    )
    assert participant_response.status_code == 201
    assert participant_response.json()["display_name"] == "New Person"

    detail_response = await client.get(f"/api/v1/conversations/{conversation_id}", headers=headers)
    assert detail_response.status_code == 200
    assert detail_response.json()["participants"][0]["display_name"] == "New Person"


async def test_call_list_detail_update_and_delete(client: AsyncClient):
    headers = await _auth_headers(client, "call-crud@example.com")
    create_response = await client.post(
        "/api/v1/calls/text",
        headers=headers,
        json={
            "title": "Call CRUD",
            "transcript_text": "Initial transcript.",
            "call_direction": "inbound",
        },
    )
    call_id = create_response.json()["call"]["id"]

    list_response = await client.get("/api/v1/calls", headers=headers)
    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == call_id

    detail_response = await client.get(f"/api/v1/calls/{call_id}", headers=headers)
    assert detail_response.status_code == 200
    assert detail_response.json()["transcriptions"][0]["transcript_text"] == "Initial transcript."

    update_response = await client.patch(
        f"/api/v1/calls/{call_id}",
        headers=headers,
        json={"call_direction": "outbound", "duration_seconds": 300},
    )
    assert update_response.status_code == 200
    assert update_response.json()["call_direction"] == "outbound"
    assert update_response.json()["duration_seconds"] == 300

    delete_response = await client.delete(f"/api/v1/calls/{call_id}", headers=headers)
    assert delete_response.status_code == 204

    missing_response = await client.get(f"/api/v1/calls/{call_id}", headers=headers)
    assert missing_response.status_code == 404


async def test_call_is_tenant_scoped(client: AsyncClient):
    first_headers = await _auth_headers(client, "call-tenant-one@example.com")
    second_headers = await _auth_headers(client, "call-tenant-two@example.com")

    create_response = await client.post(
        "/api/v1/calls/text",
        headers=first_headers,
        json={"title": "Private Call", "transcript_text": "Tenant one only."},
    )
    call_id = create_response.json()["call"]["id"]

    cross_tenant_response = await client.get(f"/api/v1/calls/{call_id}", headers=second_headers)
    assert cross_tenant_response.status_code == 404
