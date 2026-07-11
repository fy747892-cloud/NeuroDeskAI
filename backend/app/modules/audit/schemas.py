from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    actor_id: UUID | None
    action: str
    entity_type: str
    entity_id: UUID | None
    request_id: str | None
    ip_address: str | None
    user_agent: str | None
    audit_metadata: dict | None
    created_at: datetime
