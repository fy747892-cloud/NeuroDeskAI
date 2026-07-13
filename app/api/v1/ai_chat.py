import uuid

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import require_permission
from app.core.errors import NotFoundError
from app.core.permissions import Permission
from app.db.session import get_db
from app.modules.ai_chat.models import ChatSession
from app.modules.ai_chat.repository import ChatRepository
from app.modules.ai_chat.schemas import (
    ChatMessageOut,
    ChatMessageRequest,
    ChatSessionDetailOut,
    ChatSessionOut,
)
from app.modules.ai_chat.service import ChatService
from app.modules.audit.repository import AuditRepository
from app.modules.users.models import User

router = APIRouter(prefix="/ai/chat", tags=["ai-chat"])


@router.post("", response_model=ChatMessageOut, status_code=status.HTTP_201_CREATED)
async def send_chat_message(
    body: ChatMessageRequest,
    request: Request,
    current_user: User = Depends(require_permission(Permission.AI_CHAT_USE)),
    db: AsyncSession = Depends(get_db),
) -> ChatMessageOut:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    session, assistant_message = await ChatService(db).send_message(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        session_id=body.session_id,
        message=body.message,
    )
    await AuditRepository(db).record(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action="ai_chat.message_sent",
        entity_type="ai_chat_session",
        entity_id=session.id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata={"session_id": str(session.id), "confidence": assistant_message.confidence},
    )
    await db.commit()
    return ChatMessageOut.model_validate(assistant_message)


@router.get("/sessions", response_model=list[ChatSessionOut])
async def list_chat_sessions(
    current_user: User = Depends(require_permission(Permission.AI_CHAT_READ)),
    db: AsyncSession = Depends(get_db),
) -> list[ChatSession]:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")
    return await ChatRepository(db).list_sessions(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
    )


@router.get("/sessions/{session_id}", response_model=ChatSessionDetailOut)
async def get_chat_session(
    session_id: uuid.UUID,
    current_user: User = Depends(require_permission(Permission.AI_CHAT_READ)),
    db: AsyncSession = Depends(get_db),
) -> ChatSessionDetailOut:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    repository = ChatRepository(db)
    session = await repository.get_session(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        session_id=session_id,
    )
    if session is None:
        raise NotFoundError("Chat session not found.")

    messages = await repository.list_messages(
        tenant_id=current_user.tenant_id, session_id=session.id
    )
    return ChatSessionDetailOut(
        **ChatSessionOut.model_validate(session).model_dump(),
        messages=[ChatMessageOut.model_validate(message) for message in messages],
    )
