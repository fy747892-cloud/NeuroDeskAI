from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CalendarConnectStartOut(BaseModel):
    authorize_url: str
    state: str


class CalendarAccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    organization_id: UUID
    user_id: UUID
    provider: str
    external_account_id: str | None
    email_address: str | None
    status: str
    consent_scope: str | None
    connected_at: datetime | None
    last_synced_at: datetime | None
    created_at: datetime


class CalendarSyncSummaryOut(BaseModel):
    fetched: int
    created: int
    skipped: int
