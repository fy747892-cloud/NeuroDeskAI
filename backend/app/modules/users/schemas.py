from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class UserProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    full_name: str
    title: str | None = None
    avatar_url: str | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    tenant_id: UUID
    organization_id: UUID | None
    status: str
    is_email_verified: bool
    created_at: datetime
    profile: UserProfileOut | None = None


class UserProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    title: str | None = Field(default=None, max_length=255)
    avatar_url: HttpUrl | None = None
