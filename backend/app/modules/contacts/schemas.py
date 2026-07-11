from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ContactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    organization_id: UUID
    owner_user_id: UUID
    full_name: str
    email: str | None
    phone: str | None
    company: str | None
    title: str | None
    tags: list[str]
    status: str
    created_at: datetime


class ContactNoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    contact_id: UUID
    user_id: UUID
    note_text: str
    created_at: datetime


class ContactTimelineEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    contact_id: UUID
    event_type: str
    source_type: str | None
    source_id: UUID | None
    occurred_at: datetime
    event_metadata: dict | None


class ContactDetailOut(ContactOut):
    notes: list[ContactNoteOut] = []
    recent_timeline: list[ContactTimelineEventOut] = []


class ContactCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=64)
    company: str | None = Field(default=None, max_length=255)
    title: str | None = Field(default=None, max_length=255)
    tags: list[str] = Field(default_factory=list, max_length=20)


class ContactUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=64)
    company: str | None = Field(default=None, max_length=255)
    title: str | None = Field(default=None, max_length=255)
    tags: list[str] | None = Field(default=None, max_length=20)
    status: str | None = Field(default=None, min_length=1, max_length=50)


class ContactNoteCreate(BaseModel):
    note_text: str = Field(min_length=1, max_length=20_000)


class LinkConversationRequest(BaseModel):
    conversation_id: UUID
