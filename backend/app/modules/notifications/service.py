import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, ValidationAppError
from app.modules.notifications.models import Notification
from app.modules.notifications.provider import MockEmailProvider
from app.modules.notifications.repository import NotificationRepository

RETRY_BACKOFF_MINUTES = 5


class NotificationService:
    def __init__(self, db: AsyncSession):
        self._db = db
        self._notifications = NotificationRepository(db)
        self._email_provider = MockEmailProvider()

    async def create_reminder(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        source_type: str,
        source_id: uuid.UUID,
        notification_type: str,
        title: str,
        body: str,
        due_at: datetime | None = None,
        offset_minutes: int | None = None,
        remind_at: datetime | None = None,
        channel: str = "in_app",
    ) -> Notification:
        if offset_minutes is not None:
            if due_at is None:
                raise ValidationAppError(
                    "This item has no due date to compute a reminder offset from."
                )
            scheduled_at = due_at - timedelta(minutes=offset_minutes)
        elif remind_at is not None:
            scheduled_at = remind_at
        else:
            raise ValidationAppError("Provide exactly one of offset_minutes or remind_at.")

        existing = await self._notifications.get_existing(
            tenant_id=tenant_id,
            source_type=source_type,
            source_id=source_id,
            channel=channel,
            scheduled_at=scheduled_at,
        )
        if existing is not None:
            raise ConflictError("A reminder already exists for this source, channel and time.")

        return await self._notifications.create(
            tenant_id=tenant_id,
            organization_id=organization_id,
            user_id=user_id,
            title=title,
            body=body,
            notification_type=notification_type,
            channel=channel,
            scheduled_at=scheduled_at,
            source_type=source_type,
            source_id=source_id,
        )

    async def list_for_user(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        status: str | None = None,
    ) -> list[Notification]:
        return await self._notifications.list_for_user(
            tenant_id=tenant_id,
            organization_id=organization_id,
            user_id=user_id,
            status=status,
        )

    async def mark_read(self, *, notification: Notification) -> Notification:
        return await self._notifications.mark_read(notification=notification)

    async def process_due(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        now: datetime | None = None,
    ) -> dict[str, int]:
        current_time = now or datetime.now(timezone.utc)
        due_notifications = await self._notifications.list_due(
            tenant_id=tenant_id,
            organization_id=organization_id,
            now=current_time,
        )

        sent = 0
        failed = 0
        dead_lettered = 0

        for notification in due_notifications:
            try:
                if notification.channel == "email":
                    await self._email_provider.send(
                        to_email=str(notification.user_id),
                        title=notification.title,
                        body=notification.body,
                    )
                await self._notifications.mark_sent(notification=notification, sent_at=current_time)
                sent += 1
            except Exception as exc:
                next_attempt_at = current_time + timedelta(
                    minutes=RETRY_BACKOFF_MINUTES * (notification.attempts + 1)
                )
                await self._notifications.record_failure(
                    notification=notification,
                    error_message=str(exc),
                    next_attempt_at=next_attempt_at,
                )
                if notification.status == "dead_letter":
                    dead_lettered += 1
                else:
                    failed += 1

        return {
            "processed": len(due_notifications),
            "sent": sent,
            "failed": failed,
            "dead_lettered": dead_lettered,
        }
