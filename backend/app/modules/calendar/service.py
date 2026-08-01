import uuid
from datetime import datetime, timezone

import httpx
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import decrypt_token, encrypt_token
from app.core.errors import AuthError, NotFoundError, ProviderError, ValidationAppError
from app.core.oauth_state import OAuthStateStore
from app.modules.appointments.repository import AppointmentRepository
from app.modules.calendar.models import CalendarAccount
from app.modules.calendar.provider import get_calendar_events_provider, get_calendar_oauth_provider
from app.modules.calendar.repository import CalendarAccountRepository, CalendarTokenRepository

STATE_KEY_PREFIX = "calendar_oauth_state:"


class CalendarService:
    def __init__(self, db: AsyncSession, redis: Redis):
        self._db = db
        self._accounts = CalendarAccountRepository(db)
        self._tokens = CalendarTokenRepository(db)
        self._appointments = AppointmentRepository(db)
        self._states = OAuthStateStore(redis, key_prefix=STATE_KEY_PREFIX)

    async def start_connect(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        provider: str = "google",
        return_to: str | None = None,
    ) -> dict:
        account = await self._accounts.get_by_provider(
            tenant_id=tenant_id, organization_id=organization_id, user_id=user_id, provider=provider
        )
        if account is None:
            account = await self._accounts.create(
                tenant_id=tenant_id, organization_id=organization_id, user_id=user_id, provider=provider
            )

        state = await self._states.generate(
            user_id=user_id, tenant_id=tenant_id, organization_id=organization_id, return_to=return_to
        )
        try:
            oauth_provider = get_calendar_oauth_provider()
        except RuntimeError as exc:
            raise ProviderError(str(exc)) from exc
        authorize_url = oauth_provider.build_authorize_url(state=state)
        return {"authorize_url": authorize_url, "state": state}

    async def complete_connect(
        self, *, provider: str, state: str, code: str
    ) -> tuple[CalendarAccount, str | None]:
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
            raise NotFoundError("No pending calendar connection found for this state.")

        oauth_provider = get_calendar_oauth_provider()
        try:
            token_payload = await oauth_provider.exchange_code(code)
        except RuntimeError as exc:
            raise ProviderError(str(exc)) from exc

        await self._tokens.upsert(
            tenant_id=tenant_id,
            calendar_account_id=account.id,
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
        return account, claims.get("return_to")

    async def revoke(self, *, account: CalendarAccount) -> CalendarAccount:
        await self._tokens.delete_for_account(calendar_account_id=account.id)
        return await self._accounts.mark_revoked(account=account)

    async def refresh_access_token(self, *, account: CalendarAccount) -> CalendarAccount:
        if account.status != "connected":
            raise ValidationAppError("Only a connected calendar account can have its token refreshed.")

        token_row = await self._tokens.get_by_account(calendar_account_id=account.id)
        if token_row is None or token_row.refresh_token_encrypted is None:
            raise ValidationAppError("This account has no refresh token to use.")

        oauth_provider = get_calendar_oauth_provider()
        try:
            refreshed = await oauth_provider.refresh_token(
                decrypt_token(token_row.refresh_token_encrypted)
            )
        except RuntimeError as exc:
            raise ProviderError(str(exc)) from exc

        await self._tokens.upsert(
            tenant_id=account.tenant_id,
            calendar_account_id=account.id,
            access_token_encrypted=encrypt_token(refreshed["access_token"]),
            refresh_token_encrypted=encrypt_token(refreshed["refresh_token"]),
            scope=refreshed["scope"],
            expires_at=refreshed["expires_at"],
        )
        return account

    async def sync_events(self, *, account: CalendarAccount) -> dict:
        if account.status != "connected":
            raise ValidationAppError(
                "Only a connected calendar account can be synced (it may be revoked or not yet connected)."
            )

        token_row = await self._tokens.get_by_account(calendar_account_id=account.id)
        if token_row is None:
            raise ValidationAppError("This account has no stored access token.")
        if "calendar" not in (account.consent_scope or token_row.scope or ""):
            raise ValidationAppError(
                "Takvim senkronu için Google OAuth consent ekranında Calendar izni verilmeli. "
                "Sadece temel profil izniyle bağlandıysanız Ayarlar'dan bağlantıyı kesip "
                "tekrar bağlanın."
            )

        if token_row.expires_at is not None and token_row.expires_at <= datetime.now(timezone.utc):
            account = await self.refresh_access_token(account=account)
            token_row = await self._tokens.get_by_account(calendar_account_id=account.id)
            if token_row is None:
                raise ValidationAppError("This account has no stored access token.")

        access_token = decrypt_token(token_row.access_token_encrypted)
        events_provider = get_calendar_events_provider()
        try:
            fetched_events = await events_provider.list_events(
                access_token=access_token, time_min=datetime.now(timezone.utc)
            )
        except httpx.HTTPStatusError as exc:
            raise ProviderError(f"Calendar provider request failed: {exc}") from exc

        created = 0
        skipped = 0
        for event in fetched_events:
            existing = await self._appointments.get_by_external_event_id(
                tenant_id=account.tenant_id,
                organization_id=account.organization_id,
                external_event_id=event["external_event_id"],
            )
            if existing is not None:
                await self._appointments.update_appointment(
                    appointment=existing,
                    title=event["title"] or existing.title,
                    description=event["description"],
                    location=event["location"],
                    start_at=event["start_at"],
                    end_at=event["end_at"],
                )
                skipped += 1
                continue

            await self._appointments.create_appointment(
                tenant_id=account.tenant_id,
                organization_id=account.organization_id,
                user_id=account.user_id,
                title=event["title"] or "Google Calendar etkinliği",
                start_at=event["start_at"],
                end_at=event["end_at"],
                location=event["location"],
                description=event["description"],
                source_type="google_calendar",
                source_id=account.id,
                external_event_id=event["external_event_id"],
            )
            created += 1

        await self._accounts.mark_synced(account=account, synced_at=datetime.now(timezone.utc))
        return {"fetched": len(fetched_events), "created": created, "skipped": skipped}

    async def list_accounts(
        self, *, tenant_id: uuid.UUID, organization_id: uuid.UUID
    ) -> list[CalendarAccount]:
        return await self._accounts.list_accounts(tenant_id=tenant_id, organization_id=organization_id)
