import re
import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.appointments.repository import AppointmentRepository
from app.modules.contacts.repository import ContactRepository
from app.modules.conversations.repository import ConversationRepository
from app.modules.tasks.repository import TaskRepository

DEFAULT_LIMIT = 8
MIN_KEYWORD_LENGTH = 4
MAX_KEYWORDS = 3


@dataclass(frozen=True)
class ContextItem:
    source_type: str
    source_id: uuid.UUID
    title: str
    snippet: str


def _extract_keywords(query: str) -> list[str]:
    """Free-text questions rarely appear verbatim in a title, so search by the
    most distinctive words rather than the whole sentence."""
    words = re.findall(r"\w+", query)
    keywords: list[str] = []
    seen_lower: set[str] = set()
    for word in words:
        lowered = word.lower()
        if len(word) >= MIN_KEYWORD_LENGTH and lowered not in seen_lower:
            keywords.append(word)
            seen_lower.add(lowered)
        if len(keywords) >= MAX_KEYWORDS:
            break
    return keywords or [query]


async def retrieve_context(
    *,
    db: AsyncSession,
    tenant_id: uuid.UUID,
    organization_id: uuid.UUID,
    query: str,
    limit: int = DEFAULT_LIMIT,
) -> list[ContextItem]:
    tasks_repo = TaskRepository(db)
    appointments_repo = AppointmentRepository(db)
    conversations_repo = ConversationRepository(db)
    contacts_repo = ContactRepository(db)

    seen_keys: set[tuple[str, uuid.UUID]] = set()
    items: list[ContextItem] = []

    for keyword in _extract_keywords(query):
        tasks = await tasks_repo.list_tasks(
            tenant_id=tenant_id, organization_id=organization_id, search=keyword
        )
        for task in tasks:
            _append_unique(
                items,
                seen_keys,
                ContextItem(
                    source_type="task",
                    source_id=task.id,
                    title=task.title,
                    snippet=task.description or task.title,
                ),
            )

        appointments = await appointments_repo.list_appointments(
            tenant_id=tenant_id, organization_id=organization_id, search=keyword
        )
        for appointment in appointments:
            _append_unique(
                items,
                seen_keys,
                ContextItem(
                    source_type="appointment",
                    source_id=appointment.id,
                    title=appointment.title,
                    snippet=appointment.description or appointment.title,
                ),
            )

        conversations = await conversations_repo.list_conversations(
            tenant_id=tenant_id, organization_id=organization_id, search=keyword
        )
        for conversation in conversations:
            _append_unique(
                items,
                seen_keys,
                ContextItem(
                    source_type="conversation",
                    source_id=conversation.id,
                    title=conversation.title,
                    snippet=conversation.title,
                ),
            )

        contacts = await contacts_repo.list_contacts(
            tenant_id=tenant_id, organization_id=organization_id, search=keyword
        )
        for contact in contacts:
            _append_unique(
                items,
                seen_keys,
                ContextItem(
                    source_type="contact",
                    source_id=contact.id,
                    title=contact.full_name,
                    snippet=(
                        f"{contact.full_name} ({contact.company or 'şirket yok'}) - "
                        f"{contact.phone or 'telefon yok'}"
                    ),
                ),
            )

    return items[:limit]


def _append_unique(
    items: list[ContextItem],
    seen_keys: set[tuple[str, uuid.UUID]],
    item: ContextItem,
) -> None:
    key = (item.source_type, item.source_id)
    if key not in seen_keys:
        seen_keys.add(key)
        items.append(item)
