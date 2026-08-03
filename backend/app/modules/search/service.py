import hashlib
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.appointments.repository import AppointmentRepository
from app.modules.contacts.repository import ContactRepository
from app.modules.conversations.repository import ConversationRepository
from app.modules.email.repository import EmailMessageRepository
from app.modules.search.provider import get_embedding_provider
from app.modules.search.repository import EmbeddingRepository
from app.modules.search.schemas import SearchResultOut
from app.modules.tasks.repository import TaskRepository

SNIPPET_LENGTH = 160


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class SearchService:
    def __init__(self, db: AsyncSession):
        self._embeddings = EmbeddingRepository(db)
        self._tasks = TaskRepository(db)
        self._appointments = AppointmentRepository(db)
        self._conversations = ConversationRepository(db)
        self._contacts = ContactRepository(db)
        self._emails = EmailMessageRepository(db)
        self._provider = get_embedding_provider()

    async def reindex(
        self, *, tenant_id: uuid.UUID, organization_id: uuid.UUID
    ) -> dict[str, int]:
        summary = {"processed": 0, "created": 0, "updated": 0, "skipped": 0}

        sources: list[tuple[str, uuid.UUID, str, dict]] = []

        for task in await self._tasks.list_tasks(
            tenant_id=tenant_id, organization_id=organization_id
        ):
            text = f"{task.title}\n{task.description or ''}".strip()
            sources.append(("task", task.id, text, {"title": task.title}))

        for appointment in await self._appointments.list_appointments(
            tenant_id=tenant_id, organization_id=organization_id
        ):
            text = f"{appointment.title}\n{appointment.description or ''}".strip()
            sources.append(("appointment", appointment.id, text, {"title": appointment.title}))

        conversations, _ = await self._conversations.list_conversations(
            tenant_id=tenant_id, organization_id=organization_id
        )
        for conversation in conversations:
            sources.append(
                ("conversation", conversation.id, conversation.title, {"title": conversation.title})
            )

        contacts, _ = await self._contacts.list_contacts(
            tenant_id=tenant_id, organization_id=organization_id
        )
        for contact in contacts:
            text = f"{contact.full_name}\n{contact.company or ''}".strip()
            sources.append(("contact", contact.id, text, {"title": contact.full_name}))

        for message in await self._emails.list_for_org(
            tenant_id=tenant_id, organization_id=organization_id
        ):
            text = f"{message.subject or ''}\n{message.body or message.snippet or ''}".strip()
            if not text:
                continue
            sources.append(
                ("email_message", message.id, text, {"title": message.subject or "(no subject)"})
            )

        for source_type, source_id, text, meta in sources:
            summary["processed"] += 1
            content_hash = _content_hash(text)
            existing = await self._embeddings.get_by_source(
                tenant_id=tenant_id, source_type=source_type, source_id=source_id
            )
            if existing is not None and existing.content_hash == content_hash:
                summary["skipped"] += 1
                continue

            vector = await self._provider.embed(text)
            meta = {**meta, "snippet": text[:SNIPPET_LENGTH]}
            await self._embeddings.upsert(
                tenant_id=tenant_id,
                organization_id=organization_id,
                source_type=source_type,
                source_id=source_id,
                embedding_vector=vector,
                content_hash=content_hash,
                embedding_model=self._provider.model_name,
                metadata=meta,
            )
            if existing is not None:
                summary["updated"] += 1
            else:
                summary["created"] += 1

        return summary

    async def semantic_search(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        query: str,
        limit: int = 10,
    ) -> list[SearchResultOut]:
        query_vector = await self._provider.embed(query)
        matches = await self._embeddings.search(
            tenant_id=tenant_id,
            organization_id=organization_id,
            query_vector=query_vector,
            limit=limit,
        )

        results: list[SearchResultOut] = []
        for embedding, distance in matches:
            metadata = embedding.embedding_metadata or {}
            title = metadata.get("title", "")
            results.append(
                SearchResultOut(
                    source_type=embedding.source_type,
                    source_id=embedding.source_id,
                    title=title,
                    snippet=metadata.get("snippet", title),
                    score=1 - distance,
                )
            )
        return results
