from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AppointmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    organization_id: UUID
    user_id: UUID
    contact_id: UUID | None
    title: str
    description: str | None
    location: str | None
    start_at: datetime
    end_at: datetime
    timezone: str | None
    status: str
    source_type: str
    source_id: UUID | None
    ai_action_approval_id: UUID | None
    created_at: datetime


class _TimeRangeMixin(BaseModel):
    @model_validator(mode="after")
    def _validate_range(self) -> "_TimeRangeMixin":
        start_at = getattr(self, "start_at", None)
        end_at = getattr(self, "end_at", None)
        if start_at is not None and end_at is not None and end_at <= start_at:
            raise ValueError("end_at must be after start_at.")
        return self


class AppointmentCreate(_TimeRangeMixin):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=20_000)
    location: str | None = Field(default=None, max_length=255)
    start_at: datetime
    end_at: datetime
    timezone: str | None = Field(default=None, max_length=64)
    contact_id: UUID | None = None
    force: bool = False
    repeat_count: int | None = Field(default=None, ge=2, le=52)
    repeat_interval_days: int = Field(default=7, ge=1, le=365)


class AppointmentUpdate(_TimeRangeMixin):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=20_000)
    location: str | None = Field(default=None, max_length=255)
    start_at: datetime | None = None
    end_at: datetime | None = None
    timezone: str | None = Field(default=None, max_length=64)
    status: str | None = Field(default=None, min_length=1, max_length=50)
    contact_id: UUID | None = None
    force: bool = False


class AppointmentCreateFromApproval(BaseModel):
    approval_id: UUID
    force: bool = False


class ConflictCheckRequest(_TimeRangeMixin):
    start_at: datetime
    end_at: datetime
    exclude_appointment_id: UUID | None = None


class ConflictCheckOut(BaseModel):
    has_conflicts: bool
    conflicts: list[AppointmentOut]
