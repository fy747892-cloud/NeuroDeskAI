import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai_chat.service import ChatService
from app.modules.organizations.models import OrganizationMember
from app.modules.whatsapp.link_builder import build_whatsapp_deep_link, normalize_phone_for_whatsapp


def test_normalize_phone_for_whatsapp_strips_non_digits():
    assert normalize_phone_for_whatsapp("+90 (555) 123-45-67") == "905551234567"


def test_normalize_phone_for_whatsapp_rejects_too_short():
    assert normalize_phone_for_whatsapp("12345") is None


def test_normalize_phone_for_whatsapp_rewrites_turkish_leading_zero():
    assert normalize_phone_for_whatsapp("0555 123 45 67") == "905551234567"


def test_normalize_phone_for_whatsapp_rewrites_turkish_bare_local_number():
    assert normalize_phone_for_whatsapp("555 123 45 67") == "905551234567"


def test_build_whatsapp_deep_link_encodes_body():
    link = build_whatsapp_deep_link(phone_digits="905551234567", body="Merhaba, nasılsınız?")
    assert link.startswith("https://wa.me/905551234567?text=")
    assert "Merhaba" in link
    assert " " not in link


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
    body = {"full_name": "Ada Lovelace", "phone": "+905551234567"}
    body.update(overrides)
    response = await client.post("/api/v1/contacts", headers=headers, json=body)
    assert response.status_code == 201
    return response.json()


async def test_manual_draft_creates_ready_message_with_deep_link(client: AsyncClient):
    headers = await _auth_headers(client, "whatsapp-manual@example.com")
    contact = await _create_contact(client, headers)

    response = await client.post(
        "/api/v1/whatsapp/manual",
        headers=headers,
        json={"contact_id": contact["id"], "body": "Merhaba, yarın uygun musunuz?"},
    )
    assert response.status_code == 201
    message = response.json()
    assert message["status"] == "ready"
    assert message["contact_id"] == contact["id"]
    assert message["deep_link_url"].startswith("https://wa.me/905551234567?text=")
    assert message["source_type"] == "manual"
    assert message["ai_action_approval_id"] is None

    history = await client.get(f"/api/v1/whatsapp/contacts/{contact['id']}", headers=headers)
    assert history.status_code == 200
    assert [m["id"] for m in history.json()] == [message["id"]]

    single = await client.get(f"/api/v1/whatsapp/{message['id']}", headers=headers)
    assert single.status_code == 200
    assert single.json()["id"] == message["id"]


async def test_manual_draft_rejects_contact_without_phone(client: AsyncClient):
    headers = await _auth_headers(client, "whatsapp-nophone@example.com")
    contact = await _create_contact(client, headers, phone=None)

    response = await client.post(
        "/api/v1/whatsapp/manual",
        headers=headers,
        json={"contact_id": contact["id"], "body": "Merhaba"},
    )
    assert response.status_code == 422


async def test_mark_opened_updates_status(client: AsyncClient):
    headers = await _auth_headers(client, "whatsapp-opened@example.com")
    contact = await _create_contact(client, headers)
    create_response = await client.post(
        "/api/v1/whatsapp/manual",
        headers=headers,
        json={"contact_id": contact["id"], "body": "Merhaba"},
    )
    message_id = create_response.json()["id"]

    opened = await client.post(f"/api/v1/whatsapp/{message_id}/mark-opened", headers=headers)
    assert opened.status_code == 200
    assert opened.json()["status"] == "opened"
    assert opened.json()["opened_at"] is not None


async def test_viewer_can_read_but_not_create_whatsapp_message(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_headers(client, "whatsapp-viewer@example.com")
    contact = await _create_contact(client, headers)
    me_response = await client.get("/api/v1/users/me", headers=headers)
    user_id = me_response.json()["id"]

    await db_session.execute(
        update(OrganizationMember).where(OrganizationMember.user_id == user_id).values(role="viewer")
    )
    await db_session.flush()

    denied = await client.post(
        "/api/v1/whatsapp/manual",
        headers=headers,
        json={"contact_id": contact["id"], "body": "Merhaba"},
    )
    assert denied.status_code == 403

    allowed = await client.get(f"/api/v1/whatsapp/contacts/{contact['id']}", headers=headers)
    assert allowed.status_code == 200


async def test_ai_chat_whatsapp_intent_creates_approval_and_auto_materializes(
    client: AsyncClient,
):
    headers = await _auth_headers(client, "whatsapp-chat@example.com")
    contact = await _create_contact(client, headers, full_name="Zephyr Yildiz")

    reply = await client.post(
        "/api/v1/ai/chat",
        headers=headers,
        json={"message": "Zephyr Yildiz kişisine whatsapp mesajı oluştur"},
    )
    assert reply.status_code == 201
    body = reply.json()
    assert body["pending_action_approval_id"] is not None

    approval_response = await client.get(
        f"/api/v1/ai/approvals/{body['pending_action_approval_id']}", headers=headers
    )
    assert approval_response.status_code == 200
    approval = approval_response.json()
    assert approval["action_type"] == "whatsapp_message"
    assert approval["status"] == "pending"
    assert approval["suggested_payload"]["contact_id"] == contact["id"]
    assert approval["analysis_result_id"] is None

    approve_response = await client.post(
        f"/api/v1/ai/approvals/{approval['id']}/approve", headers=headers, json={}
    )
    assert approve_response.status_code == 200
    assert approve_response.json()["status"] == "approved"

    history = await client.get(f"/api/v1/whatsapp/contacts/{contact['id']}", headers=headers)
    assert history.status_code == 200
    messages = history.json()
    assert len(messages) == 1
    assert messages[0]["status"] == "ready"
    assert messages[0]["ai_action_approval_id"] == approval["id"]


async def test_ai_chat_without_whatsapp_intent_behaves_as_normal_chat(client: AsyncClient):
    headers = await _auth_headers(client, "whatsapp-no-intent@example.com")

    reply = await client.post(
        "/api/v1/ai/chat", headers=headers, json={"message": "Merhaba, bugün ne yapmalıyım?"}
    )
    assert reply.status_code == 201
    assert reply.json()["pending_action_approval_id"] is None


async def test_resolve_contact_for_intent_returns_candidates_when_ambiguous(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_headers(client, "whatsapp-ambiguous@example.com")
    await _create_contact(client, headers, full_name="Zephyr Marketing", phone="+905550000001")
    await _create_contact(client, headers, full_name="Zephyr Sales", phone="+905550000002")

    me_response = await client.get("/api/v1/users/me", headers=headers)
    me = me_response.json()

    service = ChatService(db_session)
    contact, candidates = await service._resolve_contact_for_intent(
        tenant_id=uuid.UUID(me["tenant_id"]),
        organization_id=uuid.UUID(me["organization_id"]),
        contact_hint="Zephyr",
    )
    assert contact is None
    assert {c.full_name for c in candidates} == {"Zephyr Marketing", "Zephyr Sales"}
