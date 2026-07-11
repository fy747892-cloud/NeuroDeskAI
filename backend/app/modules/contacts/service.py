import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.modules.contacts.models import Contact, ContactNote
from app.modules.contacts.repository import ContactRepository
from app.modules.conversations.repository import ConversationRepository


class ContactService:
    def __init__(self, db: AsyncSession):
        self._db = db
        self._contacts = ContactRepository(db)
        self._conversations = ConversationRepository(db)

    async def create_contact(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        owner_user_id: uuid.UUID,
        full_name: str,
        email: str | None = None,
        phone: str | None = None,
        company: str | None = None,
        title: str | None = None,
        tags: list[str] | None = None,
    ) -> Contact:
        contact = await self._contacts.create(
            tenant_id=tenant_id,
            organization_id=organization_id,
            owner_user_id=owner_user_id,
            full_name=full_name,
            email=email,
            phone=phone,
            company=company,
            title=title,
            tags=tags,
        )
        await self._contacts.add_timeline_event(
            tenant_id=tenant_id,
            contact_id=contact.id,
            event_type="contact_created",
            event_metadata={"full_name": contact.full_name},
        )
        return contact

    async def update_contact(
        self,
        *,
        contact: Contact,
        full_name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        company: str | None = None,
        title: str | None = None,
        tags: list[str] | None = None,
        status: str | None = None,
    ) -> Contact:
        return await self._contacts.update(
            contact=contact,
            full_name=full_name,
            email=email,
            phone=phone,
            company=company,
            title=title,
            tags=tags,
            status=status,
        )

    async def delete_contact(self, *, contact: Contact) -> None:
        await self._contacts.soft_delete(contact=contact)

    async def add_note(
        self,
        *,
        tenant_id: uuid.UUID,
        contact: Contact,
        user_id: uuid.UUID,
        note_text: str,
    ) -> ContactNote:
        note = await self._contacts.add_note(
            tenant_id=tenant_id,
            contact_id=contact.id,
            user_id=user_id,
            note_text=note_text,
        )
        preview = note_text[:80]
        await self._contacts.add_timeline_event(
            tenant_id=tenant_id,
            contact_id=contact.id,
            event_type="note_added",
            source_type="contact_note",
            source_id=note.id,
            event_metadata={"preview": preview},
        )
        return note

    async def link_conversation(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        contact: Contact,
        conversation_id: uuid.UUID,
    ) -> None:
        conversation = await self._conversations.get_conversation(
            tenant_id=tenant_id,
            organization_id=organization_id,
            conversation_id=conversation_id,
        )
        if conversation is None:
            raise NotFoundError("Conversation not found.")

        await self._conversations.add_participant(
            tenant_id=tenant_id,
            conversation_id=conversation.id,
            display_name=contact.full_name,
            participant_type="contact",
            participant_id=contact.id,
        )
        await self._contacts.add_timeline_event(
            tenant_id=tenant_id,
            contact_id=contact.id,
            event_type="conversation_linked",
            source_type="conversation",
            source_id=conversation.id,
            event_metadata={"conversation_title": conversation.title},
        )
