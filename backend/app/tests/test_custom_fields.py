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


async def _create_field(client: AsyncClient, headers: dict[str, str], **overrides) -> dict:
    body = {"entity_type": "contact", "field_key": "sektor", "label": "Sektör", "field_type": "text"}
    body.update(overrides)
    response = await client.post("/api/v1/custom-fields", headers=headers, json=body)
    assert response.status_code == 201
    return response.json()


async def test_custom_field_crud(client: AsyncClient):
    headers = await _auth_headers(client, "custom-field-crud@example.com")

    created = await _create_field(client, headers)
    assert created["entity_type"] == "contact"
    assert created["field_key"] == "sektor"
    assert created["label"] == "Sektör"

    list_response = await client.get(
        "/api/v1/custom-fields", headers=headers, params={"entity_type": "contact"}
    )
    assert list_response.status_code == 200
    assert created["id"] in {row["id"] for row in list_response.json()}

    update_response = await client.patch(
        f"/api/v1/custom-fields/{created['id']}", headers=headers, json={"label": "Endüstri"}
    )
    assert update_response.status_code == 200
    assert update_response.json()["label"] == "Endüstri"

    delete_response = await client.delete(f"/api/v1/custom-fields/{created['id']}", headers=headers)
    assert delete_response.status_code == 204

    after_delete = await client.get(
        "/api/v1/custom-fields", headers=headers, params={"entity_type": "contact"}
    )
    assert created["id"] not in {row["id"] for row in after_delete.json()}


async def test_duplicate_field_key_is_rejected(client: AsyncClient):
    headers = await _auth_headers(client, "custom-field-duplicate@example.com")
    await _create_field(client, headers, field_key="sektor")

    response = await client.post(
        "/api/v1/custom-fields",
        headers=headers,
        json={"entity_type": "contact", "field_key": "sektor", "label": "Duplicate", "field_type": "text"},
    )
    assert response.status_code == 409


async def test_select_field_requires_options(client: AsyncClient):
    headers = await _auth_headers(client, "custom-field-select-no-options@example.com")

    response = await client.post(
        "/api/v1/custom-fields",
        headers=headers,
        json={
            "entity_type": "contact",
            "field_key": "kaynak",
            "label": "Kaynak",
            "field_type": "select",
            "options": [],
        },
    )
    assert response.status_code == 422


async def test_contact_create_accepts_valid_custom_field_values(client: AsyncClient):
    headers = await _auth_headers(client, "custom-field-contact-valid@example.com")
    await _create_field(client, headers, field_key="sektor", field_type="text")
    await _create_field(
        client, headers, field_key="calisan_sayisi", label="Çalışan Sayısı", field_type="number"
    )
    await _create_field(
        client,
        headers,
        field_key="kaynak",
        label="Kaynak",
        field_type="select",
        options=["Referans", "Web"],
    )

    response = await client.post(
        "/api/v1/contacts",
        headers=headers,
        json={
            "full_name": "Ada Lovelace",
            "custom_fields": {"sektor": "Teknoloji", "calisan_sayisi": 42, "kaynak": "Referans"},
        },
    )
    assert response.status_code == 201
    contact = response.json()
    assert contact["custom_fields"] == {"sektor": "Teknoloji", "calisan_sayisi": 42, "kaynak": "Referans"}


async def test_contact_create_rejects_unknown_custom_field_key(client: AsyncClient):
    headers = await _auth_headers(client, "custom-field-contact-unknown@example.com")

    response = await client.post(
        "/api/v1/contacts",
        headers=headers,
        json={"full_name": "Ada Lovelace", "custom_fields": {"does_not_exist": "value"}},
    )
    assert response.status_code == 422


async def test_contact_create_rejects_wrong_type_value(client: AsyncClient):
    headers = await _auth_headers(client, "custom-field-contact-wrong-type@example.com")
    await _create_field(
        client, headers, field_key="calisan_sayisi", label="Çalışan Sayısı", field_type="number"
    )

    response = await client.post(
        "/api/v1/contacts",
        headers=headers,
        json={"full_name": "Ada Lovelace", "custom_fields": {"calisan_sayisi": "not-a-number"}},
    )
    assert response.status_code == 422


async def test_contact_create_rejects_invalid_select_option(client: AsyncClient):
    headers = await _auth_headers(client, "custom-field-contact-invalid-select@example.com")
    await _create_field(
        client, headers, field_key="kaynak", label="Kaynak", field_type="select", options=["Referans", "Web"]
    )

    response = await client.post(
        "/api/v1/contacts",
        headers=headers,
        json={"full_name": "Ada Lovelace", "custom_fields": {"kaynak": "Bilinmeyen"}},
    )
    assert response.status_code == 422


async def test_contact_create_requires_required_field(client: AsyncClient):
    headers = await _auth_headers(client, "custom-field-contact-required@example.com")
    await _create_field(
        client, headers, field_key="sektor", label="Sektör", field_type="text", is_required=True
    )

    response = await client.post(
        "/api/v1/contacts",
        headers=headers,
        json={"full_name": "Ada Lovelace", "custom_fields": {}},
    )
    assert response.status_code == 422


async def test_deal_create_accepts_and_stores_custom_field_values(client: AsyncClient):
    headers = await _auth_headers(client, "custom-field-deal-valid@example.com")
    await _create_field(
        client, headers, entity_type="deal", field_key="oncelik", label="Öncelik", field_type="boolean"
    )

    response = await client.post(
        "/api/v1/deals",
        headers=headers,
        json={"title": "Yıllık Lisans", "custom_fields": {"oncelik": True}},
    )
    assert response.status_code == 201
    assert response.json()["custom_fields"] == {"oncelik": True}


async def test_contact_update_validates_custom_fields(client: AsyncClient):
    headers = await _auth_headers(client, "custom-field-contact-update@example.com")
    await _create_field(client, headers, field_key="sektor", field_type="text")

    create_response = await client.post(
        "/api/v1/contacts", headers=headers, json={"full_name": "Ada Lovelace"}
    )
    contact_id = create_response.json()["id"]

    ok_response = await client.patch(
        f"/api/v1/contacts/{contact_id}",
        headers=headers,
        json={"custom_fields": {"sektor": "Finans"}},
    )
    assert ok_response.status_code == 200
    assert ok_response.json()["custom_fields"] == {"sektor": "Finans"}

    bad_response = await client.patch(
        f"/api/v1/contacts/{contact_id}",
        headers=headers,
        json={"custom_fields": {"unknown_field": "value"}},
    )
    assert bad_response.status_code == 422
