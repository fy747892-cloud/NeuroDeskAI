import uuid
from dataclasses import dataclass

from app.modules.users.models import User


@dataclass(frozen=True)
class TenantContext:
    user: User
    tenant_id: uuid.UUID
    organization_id: uuid.UUID
    role: str
