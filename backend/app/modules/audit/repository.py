import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.models import AuditLog


class AuditRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def record(
        self,
        *,
        tenant_id: uuid.UUID,
        actor_id: uuid.UUID | None,
        action: str,
        entity_type: str,
        entity_id: uuid.UUID | None,
        request_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        metadata: dict | None = None,
    ) -> AuditLog:
        log = AuditLog(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
            audit_metadata=metadata,
        )
        self._db.add(log)
        await self._db.flush()
        return log

    async def list_for_tenant(self, *, tenant_id: uuid.UUID, limit: int = 50) -> list[AuditLog]:
        result = await self._db.execute(
            select(AuditLog)
            .where(AuditLog.tenant_id == tenant_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
