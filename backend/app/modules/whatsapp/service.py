import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, ValidationAppError
from app.modules.ai.repository import AIRepository
from app.modules.contacts.models import Contact
from app.modules.contacts.repository import ContactRepository
from app.modules.whatsapp.link_builder import build_whatsapp_deep_link, normalize_phone_for_whatsapp
from app.modules.whatsapp.models import WhatsAppMessage
from app.modules.whatsapp.repository import WhatsAppRepository

VALID_ACTION_TYPES = {
    "whatsapp_message",
    "create_whatsapp_message",
    "whatsapp_message/create_whatsapp_message",
}


class WhatsAppService:
    def __init__(self, db: AsyncSession):
        self._db = db
        self._wa = WhatsAppRepository(db)
        self._ai = AIRepository(db)
        self._contacts = ContactRepository(db)

    async def prepare_message_from_approval(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        approval_id: uuid.UUID,
    ) -> WhatsAppMessage:
        approval = await self._ai.get_action_approval(
            tenant_id=tenant_id, organization_id=organization_id, approval_id=approval_id
        )
        if approval is None:
            raise NotFoundError("AI action approval not found.")
        if approval.action_type not in VALID_ACTION_TYPES:
            raise ValidationAppError("Only WhatsApp message approvals can prepare messages.")
        if approval.status != "approved":
            raise ValidationAppError("Only approved AI WhatsApp suggestions can be prepared.")

        existing = await self._wa.get_message_by_approval(
            tenant_id=tenant_id, organization_id=organization_id, approval_id=approval.id
        )
        if existing is not None:
            return existing

        payload = approval.approved_payload or approval.suggested_payload
        contact = await self._get_contact_or_raise(
            tenant_id=tenant_id, organization_id=organization_id, contact_id=payload.get("contact_id")
        )
        body = str(payload.get("body") or "").strip()
        if not body:
            raise ValidationAppError("Approved WhatsApp message payload must include a body.")

        return await self._prepare_message(
            tenant_id=tenant_id,
            organization_id=organization_id,
            user_id=user_id,
            contact=contact,
            body=body,
            source_type="ai_chat",
            source_id=approval.source_id,
            ai_action_approval_id=approval.id,
        )

    async def prepare_manual_message(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        contact_id: uuid.UUID,
        body: str,
    ) -> WhatsAppMessage:
        contact = await self._get_contact_or_raise(
            tenant_id=tenant_id, organization_id=organization_id, contact_id=contact_id
        )
        body = body.strip()
        if not body:
            raise ValidationAppError("Message body is required.")

        return await self._prepare_message(
            tenant_id=tenant_id,
            organization_id=organization_id,
            user_id=user_id,
            contact=contact,
            body=body,
            source_type="manual",
            source_id=None,
            ai_action_approval_id=None,
        )

    async def mark_opened(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        message_id: uuid.UUID,
    ) -> WhatsAppMessage:
        message = await self._wa.get_message(
            tenant_id=tenant_id, organization_id=organization_id, message_id=message_id
        )
        if message is None:
            raise NotFoundError("WhatsApp message not found.")
        return await self._wa.mark_opened(message=message)

    async def list_history_for_contact(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        contact_id: uuid.UUID,
    ) -> list[WhatsAppMessage]:
        contact = await self._contacts.get_by_id(
            tenant_id=tenant_id, organization_id=organization_id, contact_id=contact_id
        )
        if contact is None:
            raise NotFoundError("Contact not found.")
        return await self._wa.list_for_contact(
            tenant_id=tenant_id, organization_id=organization_id, contact_id=contact_id
        )

    async def _prepare_message(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        contact: Contact,
        body: str,
        source_type: str,
        source_id: uuid.UUID | None,
        ai_action_approval_id: uuid.UUID | None,
    ) -> WhatsAppMessage:
        phone_digits = normalize_phone_for_whatsapp(contact.phone or "")
        if phone_digits is None:
            raise ValidationAppError("Kişinin geçerli bir telefon numarası yok.")

        deep_link = build_whatsapp_deep_link(phone_digits=phone_digits, body=body)
        message = await self._wa.create_message(
            tenant_id=tenant_id,
            organization_id=organization_id,
            user_id=user_id,
            contact_id=contact.id,
            body=body,
            to_phone_raw=contact.phone or "",
            to_phone_normalized=phone_digits,
            deep_link_url=deep_link,
            source_type=source_type,
            source_id=source_id,
            ai_action_approval_id=ai_action_approval_id,
        )
        await self._contacts.add_timeline_event(
            tenant_id=tenant_id,
            contact_id=contact.id,
            event_type="whatsapp_draft_ready",
            source_type="whatsapp_message",
            source_id=message.id,
            event_metadata={"body": body},
        )
        return message

    async def _get_contact_or_raise(
        self, *, tenant_id: uuid.UUID, organization_id: uuid.UUID, contact_id
    ) -> Contact:
        if not contact_id:
            raise ValidationAppError("contact_id is required.")
        if isinstance(contact_id, str):
            try:
                contact_id = uuid.UUID(contact_id)
            except ValueError as exc:
                raise ValidationAppError("contact_id must be a valid UUID.") from exc
        contact = await self._contacts.get_by_id(
            tenant_id=tenant_id, organization_id=organization_id, contact_id=contact_id
        )
        if contact is None:
            raise NotFoundError("Contact not found.")
        return contact
