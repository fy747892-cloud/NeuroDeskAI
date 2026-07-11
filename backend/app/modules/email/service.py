import uuid
from datetime import datetime, timezone

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import decrypt_token, encrypt_token
from app.core.errors import AuthError, NotFoundError, ProviderError, ValidationAppError
from app.modules.email.models import EmailAccount
from app.modules.email.oauth_state import OAuthStateStore
from app.modules.email.provider import MAIL_PROVIDERS, OAUTH_PROVIDERS
from app.modules.email.repository import (
    EmailAccountRepository,
    EmailMessageRepository,
    EmailTokenRepository,
)


class EmailIntegrationService:
    def __init__(self, db: AsyncSession, redis: Redis):
        self._accounts = EmailAccountRepository(db)
        self._tokens = EmailTokenRepository(db)
        self._messages = EmailMessageRepository(db)
        self._states = OAuthStateStore(redis)

    async def start_connect(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        provider: str,
    ) -> dict:
        account = await self._accounts.get_by_provider(
            tenant_id=tenant_id, organization_id=organization_id, user_id=user_id, provider=provider
        )
        if account is None:
            account = await self._accounts.create(
                tenant_id=tenant_id,
                organization_id=organization_id,
                user_id=user_id,
                provider=provider,
            )

        state = await self._states.generate(
            user_id=user_id, tenant_id=tenant_id, organization_id=organization_id
        )
        oauth_provider = OAUTH_PROVIDERS[provider]()
        authorize_url = oauth_provider.build_authorize_url(state=state)
        return {"authorize_url": authorize_url, "state": state}

    async def complete_connect(self, *, provider: str, state: str, code: str) -> EmailAccount:
        claims = await self._states.consume(state)
        if claims is None:
            raise AuthError("Invalid or expired OAuth state.")

        tenant_id = uuid.UUID(claims["tenant_id"])
        organization_id = uuid.UUID(claims["organization_id"])
        user_id = uuid.UUID(claims["user_id"])

        account = await self._accounts.get_by_provider(
            tenant_id=tenant_id, organization_id=organization_id, user_id=user_id, provider=provider
        )
        if account is None:
            raise NotFoundError("No pending email connection found for this state.")

        oauth_provider = OAUTH_PROVIDERS[provider]()
        try:
            token_payload = await oauth_provider.exchange_code(code)
        except RuntimeError as exc:
            raise ProviderError(str(exc)) from exc

        await self._tokens.upsert(
            tenant_id=tenant_id,
            email_account_id=account.id,
            access_token_encrypted=encrypt_token(token_payload["access_token"]),
            refresh_token_encrypted=encrypt_token(token_payload["refresh_token"]),
            scope=token_payload["scope"],
            expires_at=token_payload["expires_at"],
        )
        await self._accounts.mark_connected(
            account=account,
            email_address=token_payload["email_address"],
            scope=token_payload["scope"],
        )
        return account

    async def revoke(self, *, account: EmailAccount) -> EmailAccount:
        await self._tokens.delete_for_account(email_account_id=account.id)
        return await self._accounts.mark_revoked(account=account)

    async def refresh_access_token(self, *, account: EmailAccount) -> EmailAccount:
        if account.status != "connected":
            raise ValidationAppError(
                "Only a connected email account can have its token refreshed."
            )

        token_row = await self._tokens.get_by_account(email_account_id=account.id)
        if token_row is None or token_row.refresh_token_encrypted is None:
            raise ValidationAppError("This account has no refresh token to use.")

        oauth_provider = OAUTH_PROVIDERS[account.provider]()
        try:
            refreshed = await oauth_provider.refresh_token(
                decrypt_token(token_row.refresh_token_encrypted)
            )
        except RuntimeError as exc:
            raise ProviderError(str(exc)) from exc

        await self._tokens.upsert(
            tenant_id=account.tenant_id,
            email_account_id=account.id,
            access_token_encrypted=encrypt_token(refreshed["access_token"]),
            refresh_token_encrypted=encrypt_token(refreshed["refresh_token"]),
            scope=refreshed["scope"],
            expires_at=refreshed["expires_at"],
        )
        return account

    async def sync_messages(self, *, account: EmailAccount) -> dict:
        if account.status != "connected":
            raise ValidationAppError(
                "Only a connected email account can be synced (it may be revoked or not yet connected)."
            )

        mail_provider = MAIL_PROVIDERS[account.provider]()
        fetched_messages = await mail_provider.list_message_metadata()

        created = 0
        skipped = 0
        for message in fetched_messages:
            already_exists = await self._messages.exists(
                email_account_id=account.id, provider_message_id=message["provider_message_id"]
            )
            if already_exists:
                skipped += 1
                continue

            await self._messages.create(
                tenant_id=account.tenant_id,
                organization_id=account.organization_id,
                email_account_id=account.id,
                provider_message_id=message["provider_message_id"],
                thread_id=message["thread_id"],
                subject=message["subject"],
                from_address=message["from_address"],
                snippet=message["snippet"],
                received_at=message["received_at"],
            )
            created += 1

        await self._accounts.mark_synced(account=account, synced_at=datetime.now(timezone.utc))
        return {"fetched": len(fetched_messages), "created": created, "skipped": skipped}
