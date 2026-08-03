import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.calendar.models import CalendarAccount, CalendarToken


class CalendarAccountRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_by_provider(
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

    async def get_by_id(
        self, *, tenant_id: uuid.UUID, organization_id: uuid.UUID, account_id: uuid.UUID
    ) -> CalendarAccount | None:
        result = await self._db.execute(
            select(CalendarAccount).where(
                CalendarAccount.tenant_id == tenant_id,
                CalendarAccount.organization_id == organization_id,
                CalendarAccount.id == account_id,
                CalendarAccount.is_deleted.is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def list_accounts(
        self, *, tenant_id: uuid.UUID, organization_id: uuid.UUID
    ) -> list[CalendarAccount]:
        result = await self._db.execute(
            select(CalendarAccount)
            .where(
                CalendarAccount.tenant_id == tenant_id,
                CalendarAccount.organization_id == organization_id,
                CalendarAccount.is_deleted.is_(False),
            )
            .order_by(CalendarAccount.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_all_connected(self) -> list[CalendarAccount]:
        result = await self._db.execute(
            select(CalendarAccount)
            .where(
                CalendarAccount.status == "connected",
                CalendarAccount.is_deleted.is_(False),
            )
            .order_by(CalendarAccount.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(
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

    async def mark_connected(
        self, *, account: CalendarAccount, email_address: str, scope: str
    ) -> CalendarAccount:
        account.status = "connected"
        account.email_address = email_address
        account.consent_scope = scope
        account.connected_at = datetime.now(timezone.utc)
        await self._db.flush()
        return account

    async def mark_revoked(self, *, account: CalendarAccount) -> CalendarAccount:
        account.status = "revoked"
        await self._db.flush()
        return account

    async def mark_synced(self, *, account: CalendarAccount, synced_at: datetime) -> CalendarAccount:
        account.last_synced_at = synced_at
        await self._db.flush()
        return account


class CalendarTokenRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_by_account(self, *, calendar_account_id: uuid.UUID) -> CalendarToken | None:
        result = await self._db.execute(
            select(CalendarToken).where(CalendarToken.calendar_account_id == calendar_account_id)
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        *,
        tenant_id: uuid.UUID,
        calendar_account_id: uuid.UUID,
        access_token_encrypted: str,
        refresh_token_encrypted: str | None,
        scope: str | None,
        expires_at: datetime | None,
    ) -> CalendarToken:
        existing = await self.get_by_account(calendar_account_id=calendar_account_id)
        if existing is not None:
            existing.access_token_encrypted = access_token_encrypted
            existing.refresh_token_encrypted = refresh_token_encrypted
            existing.scope = scope
            existing.expires_at = expires_at
            await self._db.flush()
            return existing

        token = CalendarToken(
            tenant_id=tenant_id,
            calendar_account_id=calendar_account_id,
            access_token_encrypted=access_token_encrypted,
            refresh_token_encrypted=refresh_token_encrypted,
            scope=scope,
            expires_at=expires_at,
        )
        self._db.add(token)
        await self._db.flush()
        return token

    async def delete_for_account(self, *, calendar_account_id: uuid.UUID) -> None:
        existing = await self.get_by_account(calendar_account_id=calendar_account_id)
        if existing is not None:
            await self._db.delete(existing)
            await self._db.flush()
