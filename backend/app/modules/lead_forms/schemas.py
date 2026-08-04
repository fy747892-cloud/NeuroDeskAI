from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.core.config import settings


class LeadFormOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    public_token: str
    is_active: bool
    created_at: datetime

    @computed_field  # type: ignore[prop-decorator]
    @property
    def public_url(self) -> str:
        return f"{settings.frontend_base_url}/lead-form/{self.public_token}"


class LeadFormUpdate(BaseModel):
    is_active: bool


class LeadFormPublicOut(BaseModel):
    organization_name: str
    is_active: bool


class LeadFormSubmitIn(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=64)
    company: str | None = Field(default=None, max_length=255)
    message: str | None = Field(default=None, max_length=2000)
    website: str | None = Field(default=None, max_length=255)
