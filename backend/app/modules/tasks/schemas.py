from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    organization_id: UUID
    user_id: UUID
    contact_id: UUID | None
    title: str
    description: str | None
    status: str
    priority: str
    due_at: datetime | None
    source_type: str
    source_id: UUID | None
    ai_action_approval_id: UUID | None
    created_at: datetime


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=20_000)
    priority: str = Field(default="medium", min_length=1, max_length=50)
    due_at: datetime | None = None
    contact_id: UUID | None = None
    repeat_count: int | None = Field(default=None, ge=2, le=52)
    repeat_interval_days: int = Field(default=7, ge=1, le=365)


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=20_000)
    status: str | None = Field(default=None, min_length=1, max_length=50)
    priority: str | None = Field(default=None, min_length=1, max_length=50)
    due_at: datetime | None = None
    contact_id: UUID | None = None


class TaskCreateFromApproval(BaseModel):
    approval_id: UUID
