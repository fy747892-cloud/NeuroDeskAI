import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import require_permission
from app.core.errors import NotFoundError
from app.core.permissions import Permission
from app.db.session import get_db
from app.modules.audit.repository import AuditRepository
from app.modules.notifications.models import Notification
from app.modules.notifications.repository import NotificationRepository
from app.modules.notifications.schemas import MarkAllReadOut, NotificationOut, ProcessDueOut
from app.modules.notifications.service import NotificationService
from app.modules.users.models import User

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationOut])
async def list_notifications(
    status_filter: str | None = None,
    current_user: User = Depends(require_permission(Permission.NOTIFICATIONS_READ)),
    db: AsyncSession = Depends(get_db),
) -> list[Notification]:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")
    return await NotificationRepository(db).list_for_user(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        status=status_filter,
    )


@router.patch("/{notification_id}/read", response_model=NotificationOut)
async def mark_notification_read(
    notification_id: uuid.UUID,
    current_user: User = Depends(require_permission(Permission.NOTIFICATIONS_READ)),
    db: AsyncSession = Depends(get_db),
) -> Notification:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")
    repository = NotificationRepository(db)
    notification = await repository.get_by_id(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        notification_id=notification_id,
    )
    if notification is None:
        raise NotFoundError("Notification not found.")
    notification = await NotificationService(db).mark_read(notification=notification)
    await db.commit()
    return notification


@router.post("/read-all", response_model=MarkAllReadOut)
async def mark_all_notifications_read(
    current_user: User = Depends(require_permission(Permission.NOTIFICATIONS_READ)),
    db: AsyncSession = Depends(get_db),
) -> MarkAllReadOut:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")
    updated = await NotificationService(db).mark_all_read(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
    )
    await db.commit()
    return MarkAllReadOut(updated=updated)


@router.post("/process-due", response_model=ProcessDueOut)
async def process_due_notifications(
    request: Request,
    current_user: User = Depends(require_permission(Permission.NOTIFICATIONS_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> ProcessDueOut:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    summary = await NotificationService(db).process_due(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
    )
    await AuditRepository(db).record(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action="notification.process_due_run",
        entity_type="notification_batch",
        entity_id=current_user.organization_id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata=summary,
    )
    await db.commit()
    return ProcessDueOut(**summary)
