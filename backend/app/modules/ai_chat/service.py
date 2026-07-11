import time
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.modules.ai_chat.models import ChatMessage, ChatSession
from app.modules.ai_chat.provider import MockChatProvider
from app.modules.ai_chat.repository import ChatRepository
from app.modules.ai_chat.retrieval import retrieve_context
from app.modules.analytics.repository import AICostLogRepository
from app.modules.billing.service import BillingService

TITLE_PREVIEW_LENGTH = 60


class ChatService:
    def __init__(self, db: AsyncSession):
        self._db = db
        self._chats = ChatRepository(db)
        self._cost_logs = AICostLogRepository(db)
        self._billing = BillingService(db)
        self._provider = MockChatProvider()

    async def send_message(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        session_id: uuid.UUID | None,
        message: str,
    ) -> tuple[ChatSession, ChatMessage]:
        await self._billing.enforce_ai_usage_guard(tenant_id=tenant_id)

        if session_id is not None:
            session = await self._chats.get_session(
                tenant_id=tenant_id, organization_id=organization_id, session_id=session_id
            )
            if session is None:
                raise NotFoundError("Chat session not found.")
        else:
            session = await self._chats.create_session(
                tenant_id=tenant_id,
                organization_id=organization_id,
                user_id=user_id,
                title=message[:TITLE_PREVIEW_LENGTH],
            )

        await self._chats.add_message(
            tenant_id=tenant_id, session_id=session.id, role="user", content=message
        )

        context_items = await retrieve_context(
            db=self._db, tenant_id=tenant_id, organization_id=organization_id, query=message
        )
        start_time = time.monotonic()
        answer = self._provider.generate_answer(question=message, context_items=context_items)
        latency_ms = int((time.monotonic() - start_time) * 1000)
        await self._cost_logs.record(
            tenant_id=tenant_id,
            user_id=user_id,
            provider=self._provider.provider_name,
            model=self._provider.model_name,
            source_type="ai_chat",
            input_tokens=answer.input_tokens,
            output_tokens=answer.output_tokens,
            latency_ms=latency_ms,
        )
        await self._billing.record_ai_usage(tenant_id=tenant_id, user_id=user_id)

        assistant_message = await self._chats.add_message(
            tenant_id=tenant_id,
            session_id=session.id,
            role="assistant",
            content=answer.answer_text,
            confidence=answer.confidence,
            sources=[
                {
                    "source_type": item.source_type,
                    "source_id": str(item.source_id),
                    "title": item.title,
                    "snippet": item.snippet,
                }
                for item in answer.sources
            ],
        )
        return session, assistant_message
