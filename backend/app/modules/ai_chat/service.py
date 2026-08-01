import time
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.modules.ai.repository import AIRepository
from app.modules.ai_chat.models import ChatMessage, ChatSession
from app.modules.ai_chat.provider import ChatIntent, get_chat_provider
from app.modules.ai_chat.repository import ChatRepository
from app.modules.ai_chat.retrieval import retrieve_context
from app.modules.analytics.repository import AICostLogRepository
from app.modules.billing.service import AI_CHAT_REQUESTS_QUOTA_TYPE, BillingService
from app.modules.contacts.models import Contact
from app.modules.contacts.repository import ContactRepository

TITLE_PREVIEW_LENGTH = 60
INTENT_CONFIDENCE_THRESHOLD = 0.5


class ChatService:
    def __init__(self, db: AsyncSession):
        self._db = db
        self._chats = ChatRepository(db)
        self._cost_logs = AICostLogRepository(db)
        self._billing = BillingService(db)
        self._provider = get_chat_provider()
        self._ai = AIRepository(db)
        self._contacts = ContactRepository(db)

    async def send_message(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        session_id: uuid.UUID | None,
        message: str,
    ) -> tuple[ChatSession, ChatMessage]:
        await self._billing.enforce_ai_usage_guard(
            tenant_id=tenant_id, quota_type=AI_CHAT_REQUESTS_QUOTA_TYPE
        )

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

        intent_start = time.monotonic()
        intent = await self._provider.detect_intent(message=message, recent_context=context_items)
        intent_latency_ms = int((time.monotonic() - intent_start) * 1000)
        await self._cost_logs.record(
            tenant_id=tenant_id,
            user_id=user_id,
            provider=self._provider.provider_name,
            model=self._provider.model_name,
            source_type="ai_chat_intent",
            input_tokens=max(1, len(message) // 4),
            output_tokens=max(1, len(intent.message_body or "") // 4),
            latency_ms=intent_latency_ms,
        )

        if intent.intent == "draft_whatsapp_message" and intent.confidence >= INTENT_CONFIDENCE_THRESHOLD:
            answer_text, pending_action_approval_id = await self._handle_whatsapp_draft_intent(
                tenant_id=tenant_id,
                organization_id=organization_id,
                user_id=user_id,
                session=session,
                intent=intent,
            )
            await self._billing.record_ai_usage(
                tenant_id=tenant_id, user_id=user_id, usage_type=AI_CHAT_REQUESTS_QUOTA_TYPE
            )
            assistant_message = await self._chats.add_message(
                tenant_id=tenant_id,
                session_id=session.id,
                role="assistant",
                content=answer_text,
                confidence=intent.confidence,
                sources=[],
                pending_action_approval_id=pending_action_approval_id,
            )
            return session, assistant_message

        start_time = time.monotonic()
        answer = await self._provider.generate_answer(question=message, context_items=context_items)
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
        await self._billing.record_ai_usage(
            tenant_id=tenant_id, user_id=user_id, usage_type=AI_CHAT_REQUESTS_QUOTA_TYPE
        )

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

    async def _handle_whatsapp_draft_intent(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        session: ChatSession,
        intent: ChatIntent,
    ) -> tuple[str, uuid.UUID | None]:
        contact, candidates = await self._resolve_contact_for_intent(
            tenant_id=tenant_id,
            organization_id=organization_id,
            contact_hint=intent.contact_hint,
        )
        if contact is not None and contact.phone:
            approval = await self._ai.create_action_approval(
                tenant_id=tenant_id,
                organization_id=organization_id,
                requested_by=user_id,
                analysis_result_id=None,
                action_type="whatsapp_message",
                source_type="ai_chat_session",
                source_id=session.id,
                suggested_payload={
                    "contact_id": str(contact.id),
                    "contact_name": contact.full_name,
                    "body": intent.message_body or "",
                },
                confidence_score=intent.confidence,
            )
            answer_text = (
                f"{contact.full_name} için bir WhatsApp mesajı taslağı hazırladım, "
                "onayınızı bekliyor."
            )
            return answer_text, approval.id

        if candidates:
            names = ", ".join(candidate.full_name for candidate in candidates)
            return (
                f"Birden fazla '{intent.contact_hint}' kişisi buldum: {names}. "
                "Hangisini kastettiniz?",
                None,
            )
        if contact is not None and not contact.phone:
            return "Bu kişinin kayıtlı telefon numarası yok.", None
        return "Belirttiğiniz kişiyi bulamadım.", None

    async def _resolve_contact_for_intent(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        contact_hint: str | None,
    ) -> tuple[Contact | None, list[Contact]]:
        if not contact_hint:
            return None, []
        contacts = await self._contacts.list_contacts(
            tenant_id=tenant_id, organization_id=organization_id, search=contact_hint
        )
        if len(contacts) == 1:
            return contacts[0], []
        if len(contacts) == 0:
            return None, []
        return None, contacts
