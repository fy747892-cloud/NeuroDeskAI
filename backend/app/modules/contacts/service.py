import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.modules.ai.repository import AIRepository
from app.modules.appointments.repository import AppointmentRepository
from app.modules.contacts.models import Contact, ContactNote
from app.modules.contacts.repository import ContactRepository
from app.modules.contacts.schemas import (
    ContactMemoryAppointmentOut,
    ContactMemoryConversationOut,
    ContactMemoryEmailOut,
    ContactMemoryOut,
)
from app.modules.conversations.repository import ConversationRepository
from app.modules.custom_fields.repository import CustomFieldRepository
from app.modules.custom_fields.validation import validate_custom_field_values
from app.modules.deals.repository import DealRepository
from app.modules.email.repository import EmailMessageRepository
from app.modules.tasks.repository import TaskRepository


class ContactService:
    def __init__(self, db: AsyncSession):
        self._db = db
        self._contacts = ContactRepository(db)
        self._conversations = ConversationRepository(db)
        self._tasks = TaskRepository(db)
        self._appointments = AppointmentRepository(db)
        self._email_messages = EmailMessageRepository(db)
        self._deals = DealRepository(db)
        self._ai = AIRepository(db)
        self._custom_fields = CustomFieldRepository(db)

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
        custom_fields: dict | None = None,
    ) -> Contact:
        # Always validate on create (not just when values are provided) so
        # required custom fields are actually enforced for new contacts.
        definitions = await self._custom_fields.list_for_entity(
            tenant_id=tenant_id, organization_id=organization_id, entity_type="contact"
        )
        validate_custom_field_values(definitions=definitions, values=custom_fields or {})

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
            custom_fields=custom_fields,
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
        custom_fields: dict | None = None,
    ) -> Contact:
        if custom_fields is not None:
            definitions = await self._custom_fields.list_for_entity(
                tenant_id=contact.tenant_id, organization_id=contact.organization_id, entity_type="contact"
            )
            validate_custom_field_values(definitions=definitions, values=custom_fields)

        return await self._contacts.update(
            contact=contact,
            full_name=full_name,
            email=email,
            phone=phone,
            company=company,
            title=title,
            tags=tags,
            status=status,
            custom_fields=custom_fields,
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

    async def get_memory(
        self, *, tenant_id: uuid.UUID, organization_id: uuid.UUID, contact: Contact
    ) -> ContactMemoryOut:
        last_conversation = await self._conversations.get_last_for_contact(
            tenant_id=tenant_id, organization_id=organization_id, contact_id=contact.id
        )

        last_topic: str | None = None
        if last_conversation is not None:
            summary_result = await self._ai.get_latest_result_for_source(
                tenant_id=tenant_id,
                organization_id=organization_id,
                source_type="conversation",
                source_id=last_conversation.id,
                result_type="conversation_summary",
            )
            if summary_result is not None:
                last_topic = summary_result.result_payload.get("summary_text")

        last_email = None
        if contact.email:
            last_email = await self._email_messages.get_last_for_address(
                tenant_id=tenant_id, organization_id=organization_id, from_address=contact.email
            )

        pending_items_count = await self._tasks.count_open_by_contact(
            tenant_id=tenant_id, organization_id=organization_id, contact_id=contact.id
        )
        open_deals_count = await self._deals.count_open_by_contact(
            tenant_id=tenant_id, organization_id=organization_id, contact_id=contact.id
        )
        open_deals_total_value = await self._deals.sum_open_value_by_contact(
            tenant_id=tenant_id, organization_id=organization_id, contact_id=contact.id
        )
        next_appointment = await self._appointments.get_next_by_contact(
            tenant_id=tenant_id, organization_id=organization_id, contact_id=contact.id
        )

        return ContactMemoryOut(
            contact_id=contact.id,
            full_name=contact.full_name,
            last_conversation=(
                ContactMemoryConversationOut(
                    id=last_conversation.id,
                    title=last_conversation.title,
                    occurred_at=last_conversation.created_at,
                )
                if last_conversation is not None
                else None
            ),
            last_email=(
                ContactMemoryEmailOut(
                    id=last_email.id,
                    subject=last_email.subject,
                    from_address=last_email.from_address,
                    received_at=last_email.received_at,
                )
                if last_email is not None
                else None
            ),
            last_topic=last_topic,
            pending_items_count=pending_items_count,
            open_deals_count=open_deals_count,
            open_deals_total_value=open_deals_total_value,
            next_appointment=(
                ContactMemoryAppointmentOut(
                    id=next_appointment.id,
                    title=next_appointment.title,
                    start_at=next_appointment.start_at,
                )
                if next_appointment is not None
                else None
            ),
            generated_at=datetime.now(timezone.utc),
        )
