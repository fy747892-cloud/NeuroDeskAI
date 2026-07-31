from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ClientErrorReportIn(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    stack: str | None = Field(default=None, max_length=20_000)
    digest: str | None = Field(default=None, max_length=255)
    url: str | None = Field(default=None, max_length=2000)
    context: str | None = Field(default=None, max_length=255)


class ClientErrorReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID | None
    user_id: UUID | None
    message: str
    stack: str | None
    digest: str | None
    url: str | None
    context: str | None
    user_agent: str | None
    created_at: datetime
