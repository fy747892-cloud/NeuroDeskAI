import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.notifications.models import Notification


class NotificationRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def create(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        title: str,
        body: str,
        notification_type: str,
        channel: str,
        scheduled_at: datetime,
        source_type: str | None = None,
        source_id: uuid.UUID | None = None,
    ) -> Notification:
        notification = Notification(
            tenant_id=tenant_id,
            organization_id=organization_id,
            user_id=user_id,
            title=title,
            body=body,
            notification_type=notification_type,
            channel=channel,
            source_type=source_type,
            source_id=source_id,
            status="pending",
            scheduled_at=scheduled_at,
        )
        self._db.add(notification)
        await self._db.flush()
        return notification

    async def get_existing(
        self,
        *,
        tenant_id: uuid.UUID,
        source_type: str,
        source_id: uuid.UUID,
        channel: str,
        scheduled_at: datetime,
    ) -> Notification | None:
        result = await self._db.execute(
            select(Notification).where(
                Notification.tenant_id == tenant_id,
                Notification.source_type == source_type,
                Notification.source_id == source_id,
                Notification.channel == channel,
                Notification.scheduled_at == scheduled_at,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        notification_id: uuid.UUID,
    ) -> Notification | None:
        result = await self._db.execute(
            select(Notification).where(
                Notification.tenant_id == tenant_id,
                Notification.organization_id == organization_id,
                Notification.user_id == user_id,
                Notification.id == notification_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        status: str | None = None,
    ) -> list[Notification]:
        statement = select(Notification).where(
            Notification.tenant_id == tenant_id,
            Notification.organization_id == organization_id,
            Notification.user_id == user_id,
        )
        if status is not None:
            statement = statement.where(Notification.status == status)
        result = await self._db.execute(statement.order_by(Notification.scheduled_at.desc()))
        return list(result.scalars().all())

    async def list_due(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        now: datetime,
    ) -> list[Notification]:
        result = await self._db.execute(
            select(Notification)
            .where(
                Notification.tenant_id == tenant_id,
                Notification.organization_id == organization_id,
                Notification.status == "pending",
                Notification.scheduled_at <= now,
                Notification.attempts < Notification.max_attempts,
            )
            .order_by(Notification.scheduled_at.asc())
        )
        return list(result.scalars().all())

    async def mark_read(self, *, notification: Notification) -> Notification:
        notification.status = "read"
        notification.read_at = datetime.now(timezone.utc)
        await self._db.flush()
        return notification

    async def mark_all_read(
        self, *, tenant_id: uuid.UUID, organization_id: uuid.UUID, user_id: uuid.UUID
    ) -> int:
        result = await self._db.execute(
            update(Notification)
            .where(
                Notification.tenant_id == tenant_id,
                Notification.organization_id == organization_id,
                Notification.user_id == user_id,
                Notification.read_at.is_(None),
            )
            .values(status="read", read_at=datetime.now(timezone.utc))
        )
        await self._db.flush()
        return result.rowcount or 0

    async def mark_sent(self, *, notification: Notification, sent_at: datetime) -> Notification:
        notification.status = "sent"
        notification.sent_at = sent_at
        notification.attempts += 1
        notification.error_message = None
        await self._db.flush()
        return notification

    async def record_failure(
        self,
        *,
        notification: Notification,
        error_message: str,
        next_attempt_at: datetime | None,
    ) -> Notification:
        notification.attempts += 1
        notification.error_message = error_message
        if notification.attempts >= notification.max_attempts:
            notification.status = "dead_letter"
        elif next_attempt_at is not None:
            notification.scheduled_at = next_attempt_at
        await self._db.flush()
        return notification
