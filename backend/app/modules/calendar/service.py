import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.calendar.models import CalendarAccount
from app.modules.calendar.repository import CalendarRepository


class CalendarService:
    def __init__(self, db: AsyncSession):
        self._db = db
        self._calendar = CalendarRepository(db)

    async def connect(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        provider: str,
    ) -> CalendarAccount:
        existing = await self._calendar.get_account(
            tenant_id=tenant_id,
            organization_id=organization_id,
            user_id=user_id,
            provider=provider,
        )
        if existing is not None:
            return existing

        return await self._calendar.create_account(
            tenant_id=tenant_id,
            organization_id=organization_id,
            user_id=user_id,
            provider=provider,
        )

    async def list_accounts(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> list[CalendarAccount]:
        return await self._calendar.list_accounts(
            tenant_id=tenant_id,
            organization_id=organization_id,
            user_id=user_id,
        )
