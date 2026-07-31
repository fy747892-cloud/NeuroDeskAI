import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.observability.models import ClientErrorReport


class ObservabilityRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def create(
        self,
        *,
        tenant_id: uuid.UUID | None,
        user_id: uuid.UUID | None,
        message: str,
        stack: str | None,
        digest: str | None,
        url: str | None,
        context: str | None,
        user_agent: str | None,
    ) -> ClientErrorReport:
        report = ClientErrorReport(
            tenant_id=tenant_id,
            user_id=user_id,
            message=message,
            stack=stack,
            digest=digest,
            url=url,
            context=context,
            user_agent=user_agent,
        )
        self._db.add(report)
        await self._db.flush()
        return report

    async def list_recent(self, *, limit: int = 100) -> list[ClientErrorReport]:
        result = await self._db.execute(
            select(ClientErrorReport).order_by(ClientErrorReport.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())
