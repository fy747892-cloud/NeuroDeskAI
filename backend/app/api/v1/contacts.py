import uuid

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import require_permission
from app.core.errors import NotFoundError
from app.core.pagination import Page, PaginationParams
from app.core.permissions import Permission
from app.core.pii import mask_email, mask_phone
from app.db.session import get_db
from app.modules.audit.repository import AuditRepository
from app.modules.contacts.models import Contact, ContactNote
from app.modules.contacts.repository import ContactRepository
from app.modules.contacts.schemas import (
    ContactCreate,
    ContactDetailOut,
    ContactMemoryOut,
    ContactNoteCreate,
    ContactNoteOut,
    ContactOut,
    ContactTimelineEventOut,
    ContactUpdate,
    LinkConversationRequest,
)
from app.modules.contacts.service import ContactService
from app.modules.users.models import User

router = APIRouter(prefix="/contacts", tags=["contacts"])

RECENT_TIMELINE_PREVIEW_LIMIT = 10


def _masked_contact_metadata(contact: Contact) -> dict:
    metadata: dict = {"full_name": contact.full_name}
    if contact.email:
        metadata["email"] = mask_email(contact.email)
    if contact.phone:
        metadata["phone"] = mask_phone(contact.phone)
    return metadata


@router.get("", response_model=Page[ContactOut])
async def list_contacts(
    search: str | None = None,
    status_filter: str | None = None,
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(require_permission(Permission.CONTACTS_READ)),
    db: AsyncSession = Depends(get_db),
) -> Page[ContactOut]:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")
    items, total = await ContactRepository(db).list_contacts(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        search=search,
        status=status_filter,
        limit=pagination.page_size,
        offset=pagination.offset,
    )
    return Page.create(items, total, pagination.page, pagination.page_size)


@router.post("", response_model=ContactOut, status_code=status.HTTP_201_CREATED)
async def create_contact(
    body: ContactCreate,
    request: Request,
    current_user: User = Depends(require_permission(Permission.CONTACTS_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> Contact:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    contact = await ContactService(db).create_contact(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        owner_user_id=current_user.id,
        full_name=body.full_name,
        email=body.email,
        phone=body.phone,
        company=body.company,
        title=body.title,
        tags=body.tags,
    )
    await AuditRepository(db).record(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action="contact.created",
        entity_type="contact",
        entity_id=contact.id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata=_masked_contact_metadata(contact),
    )
    await db.commit()
    return contact


@router.get("/{contact_id}", response_model=ContactDetailOut)
async def get_contact(
    contact_id: uuid.UUID,
    current_user: User = Depends(require_permission(Permission.CONTACTS_READ)),
    db: AsyncSession = Depends(get_db),
) -> ContactDetailOut:
    contact = await _get_current_contact(db, current_user, contact_id)
    repository = ContactRepository(db)
    notes = await repository.list_notes(tenant_id=current_user.tenant_id, contact_id=contact.id)
    timeline = await repository.list_timeline(
        tenant_id=current_user.tenant_id,
        contact_id=contact.id,
        limit=RECENT_TIMELINE_PREVIEW_LIMIT,
    )
    return ContactDetailOut(
        **ContactOut.model_validate(contact).model_dump(),
        notes=[ContactNoteOut.model_validate(note) for note in notes],
        recent_timeline=[ContactTimelineEventOut.model_validate(event) for event in timeline],
    )


@router.patch("/{contact_id}", response_model=ContactOut)
async def update_contact(
    contact_id: uuid.UUID,
    body: ContactUpdate,
    request: Request,
    current_user: User = Depends(require_permission(Permission.CONTACTS_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> Contact:
    contact = await _get_current_contact(db, current_user, contact_id)
    contact = await ContactService(db).update_contact(
        contact=contact,
        full_name=body.full_name,
        email=body.email,
        phone=body.phone,
        company=body.company,
        title=body.title,
        tags=body.tags,
        status=body.status,
    )
    await AuditRepository(db).record(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action="contact.updated",
        entity_type="contact",
        entity_id=contact.id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata=_masked_contact_metadata(contact),
    )
    await db.commit()
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_permission(Permission.CONTACTS_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> None:
    contact = await _get_current_contact(db, current_user, contact_id)
    await ContactService(db).delete_contact(contact=contact)
    await AuditRepository(db).record(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action="contact.deleted",
        entity_type="contact",
        entity_id=contact.id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()


@router.get("/{contact_id}/timeline", response_model=list[ContactTimelineEventOut])
async def get_contact_timeline(
    contact_id: uuid.UUID,
    current_user: User = Depends(require_permission(Permission.CONTACTS_READ)),
    db: AsyncSession = Depends(get_db),
):
    contact = await _get_current_contact(db, current_user, contact_id)
    return await ContactRepository(db).list_timeline(
        tenant_id=current_user.tenant_id, contact_id=contact.id
    )


@router.get("/{contact_id}/memory", response_model=ContactMemoryOut)
async def get_contact_memory(
    contact_id: uuid.UUID,
    current_user: User = Depends(require_permission(Permission.CONTACTS_READ)),
    db: AsyncSession = Depends(get_db),
) -> ContactMemoryOut:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")
    contact = await _get_current_contact(db, current_user, contact_id)
    return await ContactService(db).get_memory(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        contact=contact,
    )


@router.get("/{contact_id}/notes", response_model=list[ContactNoteOut])
async def list_contact_notes(
    contact_id: uuid.UUID,
    current_user: User = Depends(require_permission(Permission.CONTACTS_READ)),
    db: AsyncSession = Depends(get_db),
) -> list[ContactNote]:
    contact = await _get_current_contact(db, current_user, contact_id)
    return await ContactRepository(db).list_notes(
        tenant_id=current_user.tenant_id, contact_id=contact.id
    )


@router.post(
    "/{contact_id}/notes", response_model=ContactNoteOut, status_code=status.HTTP_201_CREATED
)
async def add_contact_note(
    contact_id: uuid.UUID,
    body: ContactNoteCreate,
    request: Request,
    current_user: User = Depends(require_permission(Permission.CONTACTS_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> ContactNote:
    contact = await _get_current_contact(db, current_user, contact_id)
    note = await ContactService(db).add_note(
        tenant_id=current_user.tenant_id,
        contact=contact,
        user_id=current_user.id,
        note_text=body.note_text,
    )
    await AuditRepository(db).record(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action="contact.note_added",
        entity_type="contact",
        entity_id=contact.id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata={"note_id": str(note.id)},
    )
    await db.commit()
    return note


@router.post("/{contact_id}/link-conversation", status_code=status.HTTP_204_NO_CONTENT)
async def link_contact_conversation(
    contact_id: uuid.UUID,
    body: LinkConversationRequest,
    request: Request,
    current_user: User = Depends(require_permission(Permission.CONTACTS_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> None:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")
    contact = await _get_current_contact(db, current_user, contact_id)
    await ContactService(db).link_conversation(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        contact=contact,
        conversation_id=body.conversation_id,
    )
    await AuditRepository(db).record(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action="contact.conversation_linked",
        entity_type="contact",
        entity_id=contact.id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata={"conversation_id": str(body.conversation_id)},
    )
    await db.commit()


async def _get_current_contact(
    db: AsyncSession, current_user: User, contact_id: uuid.UUID
) -> Contact:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")
    contact = await ContactRepository(db).get_by_id(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        contact_id=contact_id,
    )
    if contact is None:
        raise NotFoundError("Contact not found.")
    return contact
