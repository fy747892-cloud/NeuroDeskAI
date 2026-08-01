import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.whatsapp.models import WhatsAppMessage


class WhatsAppRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def create_message(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        contact_id: uuid.UUID,
        body: str,
        to_phone_raw: str,
        to_phone_normalized: str,
        deep_link_url: str,
        source_type: str = "ai_chat",
        source_id: uuid.UUID | None = None,
        ai_action_approval_id: uuid.UUID | None = None,
    ) -> WhatsAppMessage:
        message = WhatsAppMessage(
            tenant_id=tenant_id,
            organization_id=organization_id,
            user_id=user_id,
            contact_id=contact_id,
            body=body,
            to_phone_raw=to_phone_raw,
            to_phone_normalized=to_phone_normalized,
            deep_link_url=deep_link_url,
            status="ready",
            source_type=source_type,
            source_id=source_id,
            ai_action_approval_id=ai_action_approval_id,
        )
        self._db.add(message)
        await self._db.flush()
        return message

    async def get_message_by_approval(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        approval_id: uuid.UUID,
    ) -> WhatsAppMessage | None:
        result = await self._db.execute(
            select(WhatsAppMessage).where(
                WhatsAppMessage.tenant_id == tenant_id,
                WhatsAppMessage.organization_id == organization_id,
                WhatsAppMessage.ai_action_approval_id == approval_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_message(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        message_id: uuid.UUID,
    ) -> WhatsAppMessage | None:
        result = await self._db.execute(
            select(WhatsAppMessage).where(
                WhatsAppMessage.tenant_id == tenant_id,
                WhatsAppMessage.organization_id == organization_id,
                WhatsAppMessage.id == message_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_for_contact(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        contact_id: uuid.UUID,
    ) -> list[WhatsAppMessage]:
        result = await self._db.execute(
            select(WhatsAppMessage)
            .where(
                WhatsAppMessage.tenant_id == tenant_id,
                WhatsAppMessage.organization_id == organization_id,
                WhatsAppMessage.contact_id == contact_id,
            )
            .order_by(WhatsAppMessage.created_at.desc())
        )
        return list(result.scalars().all())

    async def mark_opened(
        self, *, message: WhatsAppMessage, opened_at: datetime | None = None
    ) -> WhatsAppMessage:
        message.status = "opened"
        message.opened_at = opened_at or datetime.now(timezone.utc)
        await self._db.flush()
        return message
