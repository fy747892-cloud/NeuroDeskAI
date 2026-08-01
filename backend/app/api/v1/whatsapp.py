import uuid

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import require_permission
from app.core.errors import NotFoundError
from app.core.permissions import Permission
from app.db.session import get_db
from app.modules.audit.repository import AuditRepository
from app.modules.whatsapp.models import WhatsAppMessage
from app.modules.whatsapp.repository import WhatsAppRepository
from app.modules.whatsapp.schemas import (
    WhatsAppManualDraft,
    WhatsAppMessageOut,
    WhatsAppSendFromApproval,
)
from app.modules.whatsapp.service import WhatsAppService
from app.modules.users.models import User

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])


@router.post("/from-approval", response_model=WhatsAppMessageOut, status_code=status.HTTP_201_CREATED)
async def prepare_message_from_approval(
    body: WhatsAppSendFromApproval,
    request: Request,
    current_user: User = Depends(require_permission(Permission.WHATSAPP_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> WhatsAppMessage:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    message = await WhatsAppService(db).prepare_message_from_approval(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        approval_id=body.approval_id,
    )
    await _record_whatsapp_audit(
        db, request, current_user, "whatsapp_message.prepared_from_ai_approval", message
    )
    await db.commit()
    return message


@router.post("/manual", response_model=WhatsAppMessageOut, status_code=status.HTTP_201_CREATED)
async def prepare_manual_message(
    body: WhatsAppManualDraft,
    request: Request,
    current_user: User = Depends(require_permission(Permission.WHATSAPP_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> WhatsAppMessage:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    message = await WhatsAppService(db).prepare_manual_message(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        contact_id=body.contact_id,
        body=body.body,
    )
    await _record_whatsapp_audit(db, request, current_user, "whatsapp_message.prepared_manual", message)
    await db.commit()
    return message


@router.post("/{message_id}/mark-opened", response_model=WhatsAppMessageOut)
async def mark_message_opened(
    message_id: uuid.UUID,
    current_user: User = Depends(require_permission(Permission.WHATSAPP_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> WhatsAppMessage:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    message = await WhatsAppService(db).mark_opened(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        message_id=message_id,
    )
    await db.commit()
    return message


@router.get("/contacts/{contact_id}", response_model=list[WhatsAppMessageOut])
async def list_whatsapp_history_for_contact(
    contact_id: uuid.UUID,
    current_user: User = Depends(require_permission(Permission.WHATSAPP_READ)),
    db: AsyncSession = Depends(get_db),
) -> list[WhatsAppMessage]:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    return await WhatsAppService(db).list_history_for_contact(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        contact_id=contact_id,
    )


@router.get("/{message_id}", response_model=WhatsAppMessageOut)
async def get_whatsapp_message(
    message_id: uuid.UUID,
    current_user: User = Depends(require_permission(Permission.WHATSAPP_READ)),
    db: AsyncSession = Depends(get_db),
) -> WhatsAppMessage:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    message = await WhatsAppRepository(db).get_message(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        message_id=message_id,
    )
    if message is None:
        raise NotFoundError("WhatsApp message not found.")
    return message


async def _record_whatsapp_audit(
    db: AsyncSession,
    request: Request,
    current_user: User,
    action: str,
    message: WhatsAppMessage,
) -> None:
    await AuditRepository(db).record(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action=action,
        entity_type="whatsapp_message",
        entity_id=message.id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
