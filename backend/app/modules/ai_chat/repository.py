import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai_chat.models import ChatMessage, ChatSession


class ChatRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def create_session(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        title: str | None = None,
    ) -> ChatSession:
        session = ChatSession(
            tenant_id=tenant_id,
            organization_id=organization_id,
            user_id=user_id,
            title=title,
            status="active",
        )
        self._db.add(session)
        await self._db.flush()
        return session

    async def get_session(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        session_id: uuid.UUID,
    ) -> ChatSession | None:
        result = await self._db.execute(
            select(ChatSession).where(
                ChatSession.tenant_id == tenant_id,
                ChatSession.organization_id == organization_id,
                ChatSession.id == session_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_sessions(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> list[ChatSession]:
        result = await self._db.execute(
            select(ChatSession)
            .where(
                ChatSession.tenant_id == tenant_id,
                ChatSession.organization_id == organization_id,
                ChatSession.user_id == user_id,
                ChatSession.status != "archived",
            )
            .order_by(ChatSession.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_title(self, *, session: ChatSession, title: str) -> ChatSession:
        session.title = title
        await self._db.flush()
        return session

    async def archive_session(self, *, session: ChatSession) -> None:
        session.status = "archived"
        await self._db.flush()

    async def add_message(
        self,
        *,
        tenant_id: uuid.UUID,
        session_id: uuid.UUID,
        role: str,
        content: str,
        confidence: float | None = None,
        sources: list[dict] | None = None,
    ) -> ChatMessage:
        message = ChatMessage(
            tenant_id=tenant_id,
            session_id=session_id,
            role=role,
            content=content,
            confidence=confidence,
            sources=sources,
        )
        self._db.add(message)
        await self._db.flush()
        return message

    async def list_messages(
        self, *, tenant_id: uuid.UUID, session_id: uuid.UUID
    ) -> list[ChatMessage]:
        result = await self._db.execute(
            select(ChatMessage)
            .where(ChatMessage.tenant_id == tenant_id, ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
        )
        return list(result.scalars().all())
