import uuid
from datetime import datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.contacts.models import Contact, ContactNote, ContactTimelineEvent


class ContactRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def create(
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
        contact = Contact(
            tenant_id=tenant_id,
            organization_id=organization_id,
            owner_user_id=owner_user_id,
            full_name=full_name,
            email=email,
            phone=phone,
            company=company,
            title=title,
            tags=tags or [],
            status="active",
        )
        self._db.add(contact)
        await self._db.flush()
        return contact

    async def list_contacts(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        search: str | None = None,
        status: str | None = None,
    ) -> list[Contact]:
        statement = select(Contact).where(
            Contact.tenant_id == tenant_id,
            Contact.organization_id == organization_id,
            Contact.is_deleted.is_(False),
        )
        if status is not None:
            statement = statement.where(Contact.status == status)
        if search is not None:
            term = f"%{search}%"
            statement = statement.where(
                or_(
                    Contact.full_name.ilike(term),
                    Contact.email.ilike(term),
                    Contact.phone.ilike(term),
                    Contact.company.ilike(term),
                )
            )
        result = await self._db.execute(statement.order_by(Contact.full_name.asc()))
        return list(result.scalars().all())

    async def get_by_id(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        contact_id: uuid.UUID,
    ) -> Contact | None:
        result = await self._db.execute(
            select(Contact).where(
                Contact.tenant_id == tenant_id,
                Contact.organization_id == organization_id,
                Contact.id == contact_id,
                Contact.is_deleted.is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def update(
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
        if full_name is not None:
            contact.full_name = full_name
        if email is not None:
            contact.email = email
        if phone is not None:
            contact.phone = phone
        if company is not None:
            contact.company = company
        if title is not None:
            contact.title = title
        if tags is not None:
            contact.tags = tags
        if status is not None:
            contact.status = status
        await self._db.flush()
        return contact

    async def soft_delete(self, *, contact: Contact) -> None:
        contact.is_deleted = True
        contact.deleted_at = datetime.now(timezone.utc)
        contact.status = "archived"
        await self._db.flush()

    async def add_note(
        self,
        *,
        tenant_id: uuid.UUID,
        contact_id: uuid.UUID,
        user_id: uuid.UUID,
        note_text: str,
    ) -> ContactNote:
        note = ContactNote(
            tenant_id=tenant_id,
            contact_id=contact_id,
            user_id=user_id,
            note_text=note_text,
        )
        self._db.add(note)
        await self._db.flush()
        return note

    async def list_notes(self, *, tenant_id: uuid.UUID, contact_id: uuid.UUID) -> list[ContactNote]:
        result = await self._db.execute(
            select(ContactNote)
            .where(ContactNote.tenant_id == tenant_id, ContactNote.contact_id == contact_id)
            .order_by(ContactNote.created_at.desc())
        )
        return list(result.scalars().all())

    async def add_timeline_event(
        self,
        *,
        tenant_id: uuid.UUID,
        contact_id: uuid.UUID,
        event_type: str,
        source_type: str | None = None,
        source_id: uuid.UUID | None = None,
        event_metadata: dict | None = None,
        occurred_at: datetime | None = None,
    ) -> ContactTimelineEvent:
        event = ContactTimelineEvent(
            tenant_id=tenant_id,
            contact_id=contact_id,
            event_type=event_type,
            source_type=source_type,
            source_id=source_id,
            event_metadata=event_metadata,
            occurred_at=occurred_at or datetime.now(timezone.utc),
        )
        self._db.add(event)
        await self._db.flush()
        return event

    async def list_timeline(
        self,
        *,
        tenant_id: uuid.UUID,
        contact_id: uuid.UUID,
        limit: int | None = None,
    ) -> list[ContactTimelineEvent]:
        statement = (
            select(ContactTimelineEvent)
            .where(
                ContactTimelineEvent.tenant_id == tenant_id,
                ContactTimelineEvent.contact_id == contact_id,
            )
            .order_by(ContactTimelineEvent.occurred_at.desc())
        )
        if limit is not None:
            statement = statement.limit(limit)
        result = await self._db.execute(statement)
        return list(result.scalars().all())
