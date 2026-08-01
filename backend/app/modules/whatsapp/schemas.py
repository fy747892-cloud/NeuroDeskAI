from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WhatsAppMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    organization_id: UUID
    user_id: UUID
    contact_id: UUID
    status: str
    body: str
    to_phone_raw: str
    deep_link_url: str
    source_type: str
    source_id: UUID | None
    ai_action_approval_id: UUID | None
    opened_at: datetime | None
    created_at: datetime


class WhatsAppSendFromApproval(BaseModel):
    approval_id: UUID


class WhatsAppManualDraft(BaseModel):
    contact_id: UUID
    body: str = Field(min_length=1, max_length=4_096)
