import uuid

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import require_permission
from app.core.errors import NotFoundError
from app.core.permissions import Permission
from app.db.session import get_db
from app.modules.audit.repository import AuditRepository
from app.modules.conversations.repository import ConversationRepository
from app.modules.conversations.models import Call
from app.modules.conversations.schemas import CallOut, CallTextCreate, CallTextOut, CallUpdate
from app.modules.users.models import User

router = APIRouter(prefix="/calls", tags=["calls"])


@router.get("", response_model=list[CallOut])
async def list_calls(
    current_user: User = Depends(require_permission(Permission.CONVERSATIONS_READ)),
    db: AsyncSession = Depends(get_db),
) -> list[Call]:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    return await ConversationRepository(db).list_calls(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
    )


@router.post("/text", response_model=CallTextOut, status_code=status.HTTP_201_CREATED)
async def create_call_from_text(
    body: CallTextCreate,
    request: Request,
    current_user: User = Depends(require_permission(Permission.CONVERSATIONS_CREATE)),
    db: AsyncSession = Depends(get_db),
) -> CallTextOut:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    conversations = ConversationRepository(db)
    conversation, call, transcription = await conversations.create_call_with_transcription(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        title=body.title,
        transcript_text=body.transcript_text,
        participant_names=body.participant_names,
        call_direction=body.call_direction,
        phone_number=body.phone_number,
        started_at=body.started_at,
        duration_seconds=body.duration_seconds,
        language=body.language,
    )
    await AuditRepository(db).record(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action="call.text_uploaded",
        entity_type="call",
        entity_id=call.id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata={"conversation_id": str(conversation.id)},
    )
    await db.commit()
    return CallTextOut(conversation=conversation, call=call, transcription=transcription)


@router.get("/{call_id}", response_model=CallOut)
async def get_call(
    call_id: uuid.UUID,
    current_user: User = Depends(require_permission(Permission.CONVERSATIONS_READ)),
    db: AsyncSession = Depends(get_db),
) -> Call:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    call = await ConversationRepository(db).get_call(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        call_id=call_id,
    )
    if call is None:
        raise NotFoundError("Call not found.")
    return call


@router.patch("/{call_id}", response_model=CallOut)
async def update_call(
    call_id: uuid.UUID,
    body: CallUpdate,
    request: Request,
    current_user: User = Depends(require_permission(Permission.CONVERSATIONS_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> Call:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    conversations = ConversationRepository(db)
    call = await conversations.get_call(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        call_id=call_id,
    )
    if call is None:
        raise NotFoundError("Call not found.")

    await conversations.update_call(
        call=call,
        call_direction=body.call_direction,
        phone_number=body.phone_number,
        started_at=body.started_at,
        duration_seconds=body.duration_seconds,
        status=body.status,
    )
    await AuditRepository(db).record(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action="call.updated",
        entity_type="call",
        entity_id=call.id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    return call


@router.delete("/{call_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_call(
    call_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_permission(Permission.CONVERSATIONS_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> None:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    conversations = ConversationRepository(db)
    call = await conversations.get_call(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        call_id=call_id,
    )
    if call is None:
        raise NotFoundError("Call not found.")

    await conversations.soft_delete_call(call=call)
    await AuditRepository(db).record(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action="call.deleted",
        entity_type="call",
        entity_id=call.id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
