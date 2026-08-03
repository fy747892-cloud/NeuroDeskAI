import uuid
from datetime import datetime, timezone

import httpx
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import decrypt_token, encrypt_token
from app.core.errors import AuthError, NotFoundError, ProviderError, ValidationAppError
from app.core.oauth_state import OAuthStateStore
from app.modules.contacts.models import Contact
from app.modules.contacts.repository import ContactRepository
from app.modules.email.models import EmailAccount, EmailMessageMetadata
from app.modules.email.provider import get_mail_provider, get_oauth_provider
from app.modules.email.repository import (
    EmailAccountRepository,
    EmailMessageRepository,
    EmailTokenRepository,
)
from app.modules.email.tracking import build_html_body


class EmailIntegrationService:
    def __init__(self, db: AsyncSession, redis: Redis):
        self._accounts = EmailAccountRepository(db)
        self._tokens = EmailTokenRepository(db)
        self._messages = EmailMessageRepository(db)
        self._contacts = ContactRepository(db)
        self._states = OAuthStateStore(redis, key_prefix="gmail_oauth_state:")

    async def start_connect(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        provider: str,
        return_to: str | None = None,
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
            user_id=user_id,
            tenant_id=tenant_id,
            organization_id=organization_id,
            return_to=return_to,
        )
        try:
            oauth_provider = get_oauth_provider(provider)
        except RuntimeError as exc:
            raise ProviderError(str(exc)) from exc
        authorize_url = oauth_provider.build_authorize_url(state=state)
        return {"authorize_url": authorize_url, "state": state}

    async def complete_connect(
        self, *, provider: str, state: str, code: str
    ) -> tuple[EmailAccount, str | None]:
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

        oauth_provider = get_oauth_provider(provider)
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
        return account, claims.get("return_to")

    async def revoke(self, *, account: EmailAccount) -> EmailAccount:
        await self._tokens.delete_for_account(email_account_id=account.id)
        return await self._accounts.mark_revoked(account=account)

    async def refresh_access_token(self, *, account: EmailAccount) -> EmailAccount:
        if account.status != "connected":
            raise ValidationAppError("Only a connected email account can have its token refreshed.")

        token_row = await self._tokens.get_by_account(email_account_id=account.id)
        if token_row is None or token_row.refresh_token_encrypted is None:
            raise ValidationAppError("This account has no refresh token to use.")

        oauth_provider = get_oauth_provider(account.provider)
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

        token_row = await self._tokens.get_by_account(email_account_id=account.id)
        if token_row is None:
            raise ValidationAppError("This account has no stored access token.")
        if account.provider == "gmail" and "gmail." not in (account.consent_scope or token_row.scope or ""):
            raise ValidationAppError(
                "Gmail mesaj senkronu için GOOGLE_OAUTH_SCOPES değeri Gmail API izni içermeli. "
                "Hızlı bağlantı için sadece openid email kullanıldıysa hesap bağlanır, "
                "ancak mesaj okuma için Google OAuth consent ekranında test kullanıcısı "
                "ekleyin veya uygulamayı yayına/doğrulamaya alın."
            )
        if account.provider == "outlook" and "mail.read" not in (account.consent_scope or token_row.scope or "").lower():
            raise ValidationAppError(
                "Outlook mesaj senkronu için MICROSOFT_OAUTH_SCOPES değeri Mail.Read izni içermeli."
            )

        if token_row.expires_at is not None and token_row.expires_at <= datetime.now(timezone.utc):
            account = await self.refresh_access_token(account=account)
            token_row = await self._tokens.get_by_account(email_account_id=account.id)
            if token_row is None:
                raise ValidationAppError("This account has no stored access token.")

        access_token = decrypt_token(token_row.access_token_encrypted)
        mail_provider = get_mail_provider(account.provider)
        try:
            fetched_messages = await mail_provider.list_message_metadata(access_token=access_token)
        except httpx.HTTPStatusError as exc:
            raise ProviderError(f"Mail provider request failed: {exc}") from exc

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
                body=message["body"],
                received_at=message["received_at"],
            )
            created += 1

        await self._accounts.mark_synced(account=account, synced_at=datetime.now(timezone.utc))
        return {"fetched": len(fetched_messages), "created": created, "skipped": skipped}

    async def send_message(
        self, *, account: EmailAccount, contact: Contact, subject: str, body: str
    ) -> EmailMessageMetadata:
        if account.status != "connected":
            raise ValidationAppError(
                "Only a connected email account can send messages (it may be revoked or not yet connected)."
            )
        if not contact.email:
            raise ValidationAppError("This contact has no email address to send to.")

        token_row = await self._tokens.get_by_account(email_account_id=account.id)
        if token_row is None:
            raise ValidationAppError("This account has no stored access token.")
        if account.provider == "gmail" and "gmail.send" not in (
            account.consent_scope or token_row.scope or ""
        ):
            raise ValidationAppError(
                "E-posta göndermek için Gmail hesabınızın gönderme iznine (gmail.send) sahip "
                "olması gerekiyor. Lütfen Mailler sayfasından Gmail hesabınızı yeniden bağlayın."
            )
        if account.provider != "gmail":
            raise ValidationAppError("Sending is currently only supported for Gmail accounts.")

        if token_row.expires_at is not None and token_row.expires_at <= datetime.now(timezone.utc):
            account = await self.refresh_access_token(account=account)
            token_row = await self._tokens.get_by_account(email_account_id=account.id)
            if token_row is None:
                raise ValidationAppError("This account has no stored access token.")

        # Generated before sending so the open/click tracking URLs embedded in the
        # HTML body can reference the message's id — it's created in the DB below,
        # only after the send succeeds, but the id itself is decided up front.
        message_id = uuid.uuid4()
        html_body = build_html_body(message_id=message_id, plain_text=body)

        access_token = decrypt_token(token_row.access_token_encrypted)
        mail_provider = get_mail_provider(account.provider)
        try:
            sent = await mail_provider.send_message(
                access_token=access_token,
                to=contact.email,
                subject=subject,
                body_text=body,
                body_html=html_body,
            )
        except httpx.HTTPStatusError as exc:
            raise ProviderError(f"Mail provider request failed: {exc}") from exc

        message = await self._messages.create(
            id=message_id,
            tenant_id=account.tenant_id,
            organization_id=account.organization_id,
            email_account_id=account.id,
            provider_message_id=sent["id"],
            thread_id=sent.get("threadId"),
            subject=subject,
            from_address=account.email_address,
            snippet=body[:280],
            body=body,
            received_at=datetime.now(timezone.utc),
            direction="outbound",
            contact_id=contact.id,
        )
        await self._contacts.add_timeline_event(
            tenant_id=account.tenant_id,
            contact_id=contact.id,
            event_type="email_sent",
            source_type="email_message",
            source_id=message.id,
            event_metadata={"title": f"E-posta: {subject}", "summary": body[:280]},
        )
        return message
