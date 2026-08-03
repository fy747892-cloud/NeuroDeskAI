import uuid

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import require_permission
from app.core.errors import NotFoundError
from app.core.pagination import Page, PaginationParams
from app.core.permissions import Permission
from app.db.session import get_db
from app.modules.audit.repository import AuditRepository
from app.modules.conversations.models import Conversation, ConversationParticipant
from app.modules.conversations.repository import ConversationRepository
from app.modules.conversations.schemas import (
    ConversationCreate,
    ConversationDetailOut,
    ConversationOut,
    ConversationParticipantCreate,
    ConversationParticipantOut,
    ConversationUpdate,
)
from app.modules.users.models import User

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=Page[ConversationOut])
async def list_conversations(
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(require_permission(Permission.CONVERSATIONS_READ)),
    db: AsyncSession = Depends(get_db),
) -> Page[ConversationOut]:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")
    items, total = await ConversationRepository(db).list_conversations(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        limit=pagination.page_size,
        offset=pagination.offset,
    )
    return Page.create(items, total, pagination.page, pagination.page_size)


@router.post("", response_model=ConversationDetailOut, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    body: ConversationCreate,
    request: Request,
    current_user: User = Depends(require_permission(Permission.CONVERSATIONS_CREATE)),
    db: AsyncSession = Depends(get_db),
) -> Conversation:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    conversations = ConversationRepository(db)
    conversation = await conversations.create_conversation(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        title=body.title,
        source_type=body.source_type,
        participant_names=body.participant_names,
    )
    await AuditRepository(db).record(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action="conversation.created",
        entity_type="conversation",
        entity_id=conversation.id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    return await conversations.get_conversation(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        conversation_id=conversation.id,
    ) or conversation


@router.get("/{conversation_id}", response_model=ConversationDetailOut)
async def get_conversation(
    conversation_id: uuid.UUID,
    current_user: User = Depends(require_permission(Permission.CONVERSATIONS_READ)),
    db: AsyncSession = Depends(get_db),
) -> Conversation:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    conversation = await ConversationRepository(db).get_conversation(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        conversation_id=conversation_id,
    )
    if conversation is None:
        raise NotFoundError("Conversation not found.")
    return conversation


@router.patch("/{conversation_id}", response_model=ConversationDetailOut)
async def update_conversation(
    conversation_id: uuid.UUID,
    body: ConversationUpdate,
    request: Request,
    current_user: User = Depends(require_permission(Permission.CONVERSATIONS_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> Conversation:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    conversations = ConversationRepository(db)
    conversation = await conversations.get_conversation(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        conversation_id=conversation_id,
    )
    if conversation is None:
        raise NotFoundError("Conversation not found.")

    await conversations.update_conversation(
        conversation=conversation,
        title=body.title,
        status=body.status,
    )
    await AuditRepository(db).record(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action="conversation.updated",
        entity_type="conversation",
        entity_id=conversation.id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    return conversation


@router.post(
    "/{conversation_id}/participants",
    response_model=ConversationParticipantOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_conversation_participant(
    conversation_id: uuid.UUID,
    body: ConversationParticipantCreate,
    request: Request,
    current_user: User = Depends(require_permission(Permission.CONVERSATIONS_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> ConversationParticipant:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    conversations = ConversationRepository(db)
    conversation = await conversations.get_conversation(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        conversation_id=conversation_id,
    )
    if conversation is None:
        raise NotFoundError("Conversation not found.")

    participant = await conversations.add_participant(
        tenant_id=current_user.tenant_id,
        conversation_id=conversation.id,
        display_name=body.display_name,
        participant_type=body.participant_type,
        participant_id=body.participant_id,
    )
    await AuditRepository(db).record(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action="conversation.participant_added",
        entity_type="conversation",
        entity_id=conversation.id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata={"participant_id": str(participant.id)},
    )
    await db.commit()
    return participant


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_permission(Permission.CONVERSATIONS_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> None:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    conversations = ConversationRepository(db)
    conversation = await conversations.get_conversation(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        conversation_id=conversation_id,
    )
    if conversation is None:
        raise NotFoundError("Conversation not found.")

    await conversations.soft_delete_conversation(conversation=conversation)
    await AuditRepository(db).record(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action="conversation.deleted",
        entity_type="conversation",
        entity_id=conversation.id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
