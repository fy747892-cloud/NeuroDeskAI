import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.calendar.models import CalendarAccount


class CalendarRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_account(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        provider: str,
    ) -> CalendarAccount | None:
        result = await self._db.execute(
            select(CalendarAccount).where(
                CalendarAccount.tenant_id == tenant_id,
                CalendarAccount.organization_id == organization_id,
                CalendarAccount.user_id == user_id,
                CalendarAccount.provider == provider,
                CalendarAccount.is_deleted.is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def list_accounts(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> list[CalendarAccount]:
        result = await self._db.execute(
            select(CalendarAccount)
            .where(
                CalendarAccount.tenant_id == tenant_id,
                CalendarAccount.organization_id == organization_id,
                CalendarAccount.user_id == user_id,
                CalendarAccount.is_deleted.is_(False),
            )
            .order_by(CalendarAccount.created_at.asc())
        )
        return list(result.scalars().all())

    async def create_account(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        provider: str,
    ) -> CalendarAccount:
        account = CalendarAccount(
            tenant_id=tenant_id,
            organization_id=organization_id,
            user_id=user_id,
            provider=provider,
            status="pending_oauth",
        )
        self._db.add(account)
        await self._db.flush()
        return account
