import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.email.models import EmailAccount, EmailMessageMetadata, EmailToken


class EmailAccountRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_by_provider(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        provider: str,
    ) -> EmailAccount | None:
        result = await self._db.execute(
            select(EmailAccount).where(
                EmailAccount.tenant_id == tenant_id,
                EmailAccount.organization_id == organization_id,
                EmailAccount.user_id == user_id,
                EmailAccount.provider == provider,
                EmailAccount.is_deleted.is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id(
        self, *, tenant_id: uuid.UUID, organization_id: uuid.UUID, account_id: uuid.UUID
    ) -> EmailAccount | None:
        result = await self._db.execute(
            select(EmailAccount).where(
                EmailAccount.tenant_id == tenant_id,
                EmailAccount.organization_id == organization_id,
                EmailAccount.id == account_id,
                EmailAccount.is_deleted.is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def list_accounts(
        self, *, tenant_id: uuid.UUID, organization_id: uuid.UUID
    ) -> list[EmailAccount]:
        result = await self._db.execute(
            select(EmailAccount)
            .where(
                EmailAccount.tenant_id == tenant_id,
                EmailAccount.organization_id == organization_id,
                EmailAccount.is_deleted.is_(False),
            )
            .order_by(EmailAccount.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_all_connected(self) -> list[EmailAccount]:
        result = await self._db.execute(
            select(EmailAccount)
            .where(
                EmailAccount.status == "connected",
                EmailAccount.is_deleted.is_(False),
            )
            .order_by(EmailAccount.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        provider: str,
    ) -> EmailAccount:
        account = EmailAccount(
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
        self, *, account: EmailAccount, email_address: str, scope: str
    ) -> EmailAccount:
        account.status = "connected"
        account.email_address = email_address
        account.consent_granted_at = datetime.now(timezone.utc)
        account.consent_scope = scope
        await self._db.flush()
        return account

    async def mark_revoked(self, *, account: EmailAccount) -> EmailAccount:
        account.status = "revoked"
        await self._db.flush()
        return account

    async def mark_synced(self, *, account: EmailAccount, synced_at: datetime) -> EmailAccount:
        account.last_synced_at = synced_at
        await self._db.flush()
        return account


class EmailTokenRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_by_account(self, *, email_account_id: uuid.UUID) -> EmailToken | None:
        result = await self._db.execute(
            select(EmailToken).where(EmailToken.email_account_id == email_account_id)
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        *,
        tenant_id: uuid.UUID,
        email_account_id: uuid.UUID,
        access_token_encrypted: str,
        refresh_token_encrypted: str | None,
        scope: str | None,
        expires_at: datetime | None,
    ) -> EmailToken:
        existing = await self.get_by_account(email_account_id=email_account_id)
        if existing is not None:
            existing.access_token_encrypted = access_token_encrypted
            existing.refresh_token_encrypted = refresh_token_encrypted
            existing.scope = scope
            existing.expires_at = expires_at
            await self._db.flush()
            return existing

        token = EmailToken(
            tenant_id=tenant_id,
            email_account_id=email_account_id,
            access_token_encrypted=access_token_encrypted,
            refresh_token_encrypted=refresh_token_encrypted,
            scope=scope,
            expires_at=expires_at,
        )
        self._db.add(token)
        await self._db.flush()
        return token

    async def delete_for_account(self, *, email_account_id: uuid.UUID) -> None:
        existing = await self.get_by_account(email_account_id=email_account_id)
        if existing is not None:
            await self._db.delete(existing)
            await self._db.flush()


class EmailMessageRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_by_id(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        message_id: uuid.UUID,
    ) -> EmailMessageMetadata | None:
        result = await self._db.execute(
            select(EmailMessageMetadata).where(
                EmailMessageMetadata.tenant_id == tenant_id,
                EmailMessageMetadata.organization_id == organization_id,
                EmailMessageMetadata.id == message_id,
            )
        )
        return result.scalar_one_or_none()

    async def mark_replied(self, *, message: EmailMessageMetadata) -> EmailMessageMetadata:
        message.is_replied = True
        await self._db.flush()
        return message

    async def count_unreplied_since(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        since: datetime,
    ) -> int:
        result = await self._db.execute(
            select(func.count(EmailMessageMetadata.id)).where(
                EmailMessageMetadata.tenant_id == tenant_id,
                EmailMessageMetadata.organization_id == organization_id,
                EmailMessageMetadata.is_replied.is_(False),
                EmailMessageMetadata.received_at >= since,
            )
        )
        return result.scalar_one()

    async def exists(self, *, email_account_id: uuid.UUID, provider_message_id: str) -> bool:
        result = await self._db.execute(
            select(EmailMessageMetadata.id).where(
                EmailMessageMetadata.email_account_id == email_account_id,
                EmailMessageMetadata.provider_message_id == provider_message_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def create(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        email_account_id: uuid.UUID,
        provider_message_id: str,
        thread_id: str | None,
        subject: str | None,
        from_address: str | None,
        snippet: str | None,
        body: str | None,
        received_at: datetime | None,
        direction: str = "inbound",
        contact_id: uuid.UUID | None = None,
    ) -> EmailMessageMetadata:
        message = EmailMessageMetadata(
            tenant_id=tenant_id,
            organization_id=organization_id,
            email_account_id=email_account_id,
            provider_message_id=provider_message_id,
            thread_id=thread_id,
            subject=subject,
            from_address=from_address,
            snippet=snippet,
            body=body,
            received_at=received_at,
            direction=direction,
            contact_id=contact_id,
        )
        self._db.add(message)
        await self._db.flush()
        return message

    async def list_for_account(
        self, *, email_account_id: uuid.UUID
    ) -> list[EmailMessageMetadata]:
        result = await self._db.execute(
            select(EmailMessageMetadata)
            .where(EmailMessageMetadata.email_account_id == email_account_id)
            .order_by(EmailMessageMetadata.received_at.desc())
        )
        return list(result.scalars().all())

    async def list_for_org(
        self, *, tenant_id: uuid.UUID, organization_id: uuid.UUID
    ) -> list[EmailMessageMetadata]:
        result = await self._db.execute(
            select(EmailMessageMetadata).where(
                EmailMessageMetadata.tenant_id == tenant_id,
                EmailMessageMetadata.organization_id == organization_id,
            )
        )
        return list(result.scalars().all())

    async def get_last_for_address(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        from_address: str,
    ) -> EmailMessageMetadata | None:
        result = await self._db.execute(
            select(EmailMessageMetadata)
            .where(
                EmailMessageMetadata.tenant_id == tenant_id,
                EmailMessageMetadata.organization_id == organization_id,
                func.lower(EmailMessageMetadata.from_address) == from_address.lower(),
            )
            .order_by(EmailMessageMetadata.received_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
