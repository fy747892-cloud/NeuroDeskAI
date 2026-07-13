from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DealOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    organization_id: UUID
    owner_user_id: UUID
    contact_id: UUID | None
    title: str
    description: str | None
    value: float | None
    currency: str
    stage: str
    expected_close_date: datetime | None
    source_type: str
    source_id: UUID | None
    ai_action_approval_id: UUID | None
    created_at: datetime


class DealCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=20_000)
    value: float | None = Field(default=None, ge=0)
    currency: str = Field(default="TRY", min_length=1, max_length=10)
    stage: str = Field(default="lead", min_length=1, max_length=50)
    expected_close_date: datetime | None = None
    contact_id: UUID | None = None


class DealUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=20_000)
    value: float | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=1, max_length=10)
    stage: str | None = Field(default=None, min_length=1, max_length=50)
    expected_close_date: datetime | None = None
    contact_id: UUID | None = None


class DealCreateFromApproval(BaseModel):
    approval_id: UUID