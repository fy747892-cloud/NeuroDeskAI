from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CalendarAccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    organization_id: UUID
    user_id: UUID
    provider: str
    external_account_id: str | None
    status: str
    connected_at: datetime | None
    created_at: datetime
