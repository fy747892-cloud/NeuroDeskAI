from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    organization_id: UUID
    user_id: UUID
    title: str
    body: str
    notification_type: str
    channel: str
    source_type: str | None
    source_id: UUID | None
    status: str
    scheduled_at: datetime
    sent_at: datetime | None
    read_at: datetime | None
    attempts: int
    max_attempts: int
    error_message: str | None
    created_at: datetime


class ReminderCreate(BaseModel):
    offset_minutes: int | None = Field(default=None, gt=0)
    remind_at: datetime | None = None
    channel: str = Field(default="in_app", pattern="^(in_app|email)$")

    @model_validator(mode="after")
    def _exactly_one_of_offset_or_remind_at(self) -> "ReminderCreate":
        if (self.offset_minutes is None) == (self.remind_at is None):
            raise ValueError("Provide exactly one of offset_minutes or remind_at.")
        return self


class ProcessDueOut(BaseModel):
    processed: int
    sent: int
    failed: int
    dead_lettered: int
