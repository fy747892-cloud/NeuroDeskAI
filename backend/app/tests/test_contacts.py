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
    body = {
        "full_name": "Ada Lovelace",
        "email": "ada@example.com",
        "phone": "+905551234567",
        "company": "Analytical Engines Inc",
    }
    body.update(overrides)
    response = await client.post("/api/v1/contacts", headers=headers, json=body)
    assert response.status_code == 201
    return response.json()


async def _create_conversation(client: AsyncClient, headers: dict[str, str]) -> dict:
    response = await client.post(
        "/api/v1/conversations",
        headers=headers,
        json={"title": "Intro call", "source_type": "manual"},
    )
    assert response.status_code == 201
    return response.json()


async def test_contact_crud_and_soft_delete(client: AsyncClient):
    headers = await _auth_headers(client, "contact-crud@example.com")
    contact = await _create_contact(client, headers)
    assert contact["full_name"] == "Ada Lovelace"
    assert contact["status"] == "active"

    list_response = await client.get("/api/v1/contacts", headers=headers)
    assert list_response.status_code == 200
    assert contact["id"] in {item["id"] for item in list_response.json()}

    update_response = await client.patch(
        f"/api/v1/contacts/{contact['id']}", headers=headers, json={"title": "Mathematician"}
    )
    assert update_response.status_code == 200
    assert update_response.json()["title"] == "Mathematician"

    delete_response = await client.delete(f"/api/v1/contacts/{contact['id']}", headers=headers)
    assert delete_response.status_code == 204

    get_response = await client.get(f"/api/v1/contacts/{contact['id']}", headers=headers)
    assert get_response.status_code == 404


async def test_contact_search_matches_name_email_phone_company(client: AsyncClient):
    headers = await _auth_headers(client, "contact-search@example.com")
    await _create_contact(client, headers, full_name="Grace Hopper", email="grace@navy.mil")
    await _create_contact(
        client, headers, full_name="Alan Turing", email="alan@bletchley.example", company="Bletchley Park"
    )

    by_name = await client.get("/api/v1/contacts", headers=headers, params={"search": "Hopper"})
    assert [c["full_name"] for c in by_name.json()] == ["Grace Hopper"]

    by_company = await client.get(
        "/api/v1/contacts", headers=headers, params={"search": "Bletchley"}
    )
    assert [c["full_name"] for c in by_company.json()] == ["Alan Turing"]


async def test_contact_timeline_records_create_note_and_link_in_order(client: AsyncClient):
    headers = await _auth_headers(client, "contact-timeline@example.com")
    contact = await _create_contact(client, headers)

    note_response = await client.post(
        f"/api/v1/contacts/{contact['id']}/notes",
        headers=headers,
        json={"note_text": "Interested in the annual plan."},
    )
    assert note_response.status_code == 201

    conversation = await _create_conversation(client, headers)
    link_response = await client.post(
        f"/api/v1/contacts/{contact['id']}/link-conversation",
        headers=headers,
        json={"conversation_id": conversation["id"]},
    )
    assert link_response.status_code == 204

    timeline_response = await client.get(
        f"/api/v1/contacts/{contact['id']}/timeline", headers=headers
    )
    assert timeline_response.status_code == 200
    event_types = [event["event_type"] for event in timeline_response.json()]
    assert event_types == ["conversation_linked", "note_added", "contact_created"]

    detail_response = await client.get(f"/api/v1/contacts/{contact['id']}", headers=headers)
    detail = detail_response.json()
    assert len(detail["notes"]) == 1
    assert [event["event_type"] for event in detail["recent_timeline"]] == event_types


async def test_link_conversation_adds_contact_as_participant(client: AsyncClient):
    headers = await _auth_headers(client, "contact-link@example.com")
    contact = await _create_contact(client, headers)
    conversation = await _create_conversation(client, headers)

    await client.post(
        f"/api/v1/contacts/{contact['id']}/link-conversation",
        headers=headers,
        json={"conversation_id": conversation["id"]},
    )

    detail_response = await client.get(
        f"/api/v1/conversations/{conversation['id']}", headers=headers
    )
    participants = detail_response.json()["participants"]
    assert any(
        p["display_name"] == contact["full_name"] for p in participants
    )


async def test_contact_is_tenant_scoped(client: AsyncClient):
    first_headers = await _auth_headers(client, "contact-tenant-one@example.com")
    second_headers = await _auth_headers(client, "contact-tenant-two@example.com")
    contact = await _create_contact(client, first_headers)

    response = await client.get(f"/api/v1/contacts/{contact['id']}", headers=second_headers)
    assert response.status_code == 404


async def test_audit_log_masks_contact_pii(client: AsyncClient):
    headers = await _auth_headers(client, "contact-pii@example.com")
    contact = await _create_contact(
        client, headers, email="secret.person@example.com", phone="+905551239999"
    )

    audit_response = await client.get("/api/v1/audit-logs", headers=headers)
    assert audit_response.status_code == 200
    entry = next(
        log
        for log in audit_response.json()
        if log["action"] == "contact.created" and log["entity_id"] == contact["id"]
    )
    metadata = entry["audit_metadata"]
    assert "secret.person@example.com" not in str(metadata)
    assert "551239999" not in str(metadata)
    assert metadata["email"] == "s***@example.com"
    assert metadata["phone"] == "***9999"

    detail_response = await client.get(f"/api/v1/contacts/{contact['id']}", headers=headers)
    detail = detail_response.json()
    assert detail["email"] == "secret.person@example.com"
    assert detail["phone"] == "+905551239999"
