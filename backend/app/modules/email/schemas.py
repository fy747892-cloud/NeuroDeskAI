from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ConnectStartOut(BaseModel):
    authorize_url: str
    state: str


class EmailAccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    organization_id: UUID
    user_id: UUID
    provider: str
    email_address: str | None
    status: str
    consent_granted_at: datetime | None
    consent_scope: str | None
    last_synced_at: datetime | None
    created_at: datetime


class EmailMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email_account_id: UUID
    provider_message_id: str
    thread_id: str | None
    subject: str | None
    from_address: str | None
    snippet: str | None
    body: str | None
    received_at: datetime | None
    is_replied: bool
    direction: str
    contact_id: UUID | None


class SyncSummaryOut(BaseModel):
    fetched: int
    created: int
    skipped: int


class SendEmailIn(BaseModel):
    contact_id: UUID
    subject: str = Field(min_length=1, max_length=255)
    body: str = Field(min_length=1, max_length=20_000)
