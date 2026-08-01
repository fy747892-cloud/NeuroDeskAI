import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import AuthError, ConflictError
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    generate_secure_token,
    hash_password,
    hash_refresh_token,
    hash_token,
    refresh_token_expiry,
    verify_password,
)
from app.modules.auth import totp
from app.modules.auth.repository import AuthRepository
from app.modules.auth.schemas import TokenResponse, TotpSetupOut, TotpVerifyOut
from app.modules.billing.service import BillingService
from app.modules.notifications.provider import get_email_provider
from app.modules.organizations.repository import OrganizationRepository
from app.modules.users.models import User
from app.modules.users.repository import UserRepository

PASSWORD_RESET_TOKEN_TTL_MINUTES = 60
INVITE_TOKEN_TTL_MINUTES = 60 * 24 * 7


class DeviceContext:
    def __init__(
        self, device_id: str | None = None, ip_address: str | None = None, user_agent: str | None = None
    ):
        self.device_id = device_id
        self.ip_address = ip_address
        self.user_agent = user_agent


class AuthService:
    def __init__(self, db: AsyncSession):
        self._db = db
        self._users = UserRepository(db)
        self._orgs = OrganizationRepository(db)
        self._auth = AuthRepository(db)
        self._email_provider = get_email_provider()

    async def register_user(
        self, *, email: str, password: str, display_name: str, device: DeviceContext
    ) -> TokenResponse:
        normalized_email = email.strip().lower()

        existing = await self._users.get_by_email_any_tenant(email=normalized_email)
        if existing is not None:
            raise ConflictError("A user with this email already exists.")

        tenant, organization = await self._orgs.create_personal_tenant_and_org(
            display_name=display_name
        )
        await BillingService(self._db).create_default_subscription(tenant_id=tenant.id)

        user = User(
            tenant_id=tenant.id,
            organization_id=organization.id,
            email=normalized_email,
            password_hash=hash_password(password),
            auth_provider="local",
            is_email_verified=False,
            status="active",
        )
        await self._users.create(user)
        await self._users.create_profile(
            tenant_id=tenant.id,
            user_id=user.id,
            full_name=display_name,
        )
        await self._orgs.create_member(
            tenant_id=tenant.id,
            organization_id=organization.id,
            user_id=user.id,
            role="owner",
        )

        tokens = await self._issue_tokens(user, device)
        await self._db.commit()
        return tokens

    async def authenticate(
        self,
        *,
        email: str,
        password: str,
        device: DeviceContext,
        totp_code: str | None = None,
        recovery_code: str | None = None,
    ) -> TokenResponse:
        normalized_email = email.strip().lower()
        user = await self._users.get_by_email_any_tenant(email=normalized_email)

        if user is None or user.password_hash is None or not verify_password(
            password, user.password_hash
        ):
            raise AuthError("Invalid email or password.")

        if user.status != "active":
            raise AuthError("This account is not active.")

        if user.totp_enabled:
            if recovery_code:
                if not await self._consume_recovery_code(user, recovery_code):
                    raise AuthError("Invalid recovery code.")
            elif totp_code:
                if not user.totp_secret or not totp.verify_code(secret=user.totp_secret, code=totp_code):
                    raise AuthError("Invalid authentication code.")
            else:
                return TokenResponse(mfa_required=True)

        tokens = await self._issue_tokens(user, device)
        await self._db.commit()
        return tokens

    async def setup_totp(self, *, user: User) -> TotpSetupOut:
        secret = totp.generate_secret()
        user.totp_secret = secret
        user.totp_enabled = False
        await self._db.commit()

        otpauth_url = totp.build_otpauth_url(secret=secret, account_email=user.email)
        return TotpSetupOut(secret=secret, otpauth_url=otpauth_url)

    async def verify_totp(self, *, user: User, code: str) -> TotpVerifyOut:
        if not user.totp_secret or not totp.verify_code(secret=user.totp_secret, code=code):
            raise AuthError("Invalid authentication code.")

        recovery_codes = totp.generate_recovery_codes()
        metadata = dict(user.user_metadata or {})
        metadata["totp_recovery_codes"] = [hash_token(rc) for rc in recovery_codes]
        user.user_metadata = metadata
        user.totp_enabled = True
        await self._db.commit()

        return TotpVerifyOut(recovery_codes=recovery_codes)

    async def disable_totp(self, *, user: User, code: str) -> None:
        if not user.totp_secret or not totp.verify_code(secret=user.totp_secret, code=code):
            raise AuthError("Invalid authentication code.")

        user.totp_enabled = False
        user.totp_secret = None
        metadata = dict(user.user_metadata or {})
        metadata.pop("totp_recovery_codes", None)
        user.user_metadata = metadata
        await self._db.commit()

    async def _consume_recovery_code(self, user: User, recovery_code: str) -> bool:
        metadata = user.user_metadata or {}
        hashed_codes: list[str] = metadata.get("totp_recovery_codes", [])
        code_hash = hash_token(recovery_code.strip())

        if code_hash not in hashed_codes:
            return False

        remaining = [h for h in hashed_codes if h != code_hash]
        metadata = dict(metadata)
        metadata["totp_recovery_codes"] = remaining
        user.user_metadata = metadata
        return True

    async def login_with_google(
        self, *, email: str, display_name: str, device: DeviceContext
    ) -> TokenResponse:
        normalized_email = email.strip().lower()
        user = await self._users.get_by_email_any_tenant(email=normalized_email)

        if user is None:
            tenant, organization = await self._orgs.create_personal_tenant_and_org(
                display_name=display_name
            )
            await BillingService(self._db).create_default_subscription(tenant_id=tenant.id)

            user = User(
                tenant_id=tenant.id,
                organization_id=organization.id,
                email=normalized_email,
                password_hash=None,
                auth_provider="google",
                is_email_verified=True,
                status="active",
            )
            await self._users.create(user)
            await self._users.create_profile(
                tenant_id=tenant.id, user_id=user.id, full_name=display_name
            )
            await self._orgs.create_member(
                tenant_id=tenant.id,
                organization_id=organization.id,
                user_id=user.id,
                role="owner",
            )
        else:
            if user.status != "active":
                raise AuthError("This account is not active.")
            if user.totp_enabled:
                raise AuthError(
                    "This account has two-factor authentication enabled. "
                    "Sign in with your password instead."
                )

        tokens = await self._issue_tokens(user, device)
        await self._db.commit()
        return tokens

    async def _issue_tokens(self, user: User, device: DeviceContext) -> TokenResponse:
        expires_at = refresh_token_expiry()

        session = await self._auth.create_session(
            user_id=user.id,
            tenant_id=user.tenant_id,
            device_id=device.device_id,
            ip_address=device.ip_address,
            user_agent=device.user_agent,
            expires_at=expires_at,
        )

        raw_refresh_token = generate_refresh_token()
        await self._auth.create_refresh_token(
            user_id=user.id,
            session_id=session.id,
            token_hash=hash_refresh_token(raw_refresh_token),
            expires_at=expires_at,
        )

        access_token = await self._build_access_token(user)
        return TokenResponse(access_token=access_token, refresh_token=raw_refresh_token)

    async def _build_access_token(self, user: User) -> str:
        member = await self._orgs.get_member(
            tenant_id=user.tenant_id,
            organization_id=user.organization_id,
            user_id=user.id,
        ) if user.organization_id else None

        return create_access_token(
            user_id=user.id,
            tenant_id=user.tenant_id,
            organization_id=user.organization_id,
            roles=[member.role] if member else [],
        )

    async def rotate_refresh_token(self, *, raw_refresh_token: str, device: DeviceContext) -> TokenResponse:
        token_hash = hash_refresh_token(raw_refresh_token)
        refresh_token = await self._auth.get_refresh_token_by_hash(token_hash)

        if refresh_token is None:
            raise AuthError("Invalid refresh token.")

        if refresh_token.revoked_at is not None:
            # Reuse of an already-revoked token: treat as compromise, revoke everything.
            await self._auth.revoke_all_for_user(refresh_token.user_id)
            await self._db.commit()
            raise AuthError("Refresh token has already been used. All sessions revoked.")

        if refresh_token.expires_at < datetime.now(timezone.utc):
            raise AuthError("Refresh token has expired.")

        user = await self._users.get_by_id(refresh_token.user_id)
        if user is None or user.status != "active":
            raise AuthError("Invalid refresh token.")

        await self._auth.revoke_refresh_token(refresh_token)

        # Rotation continues the same session (device_id/ip/user_agent may shift
        # slightly, e.g. a new IP mid-session) rather than spawning a new
        # "active session" row every ~14 minutes while a tab stays open.
        expires_at = refresh_token_expiry()
        await self._auth.touch_session(
            session_id=refresh_token.session_id,
            expires_at=expires_at,
            ip_address=device.ip_address,
            user_agent=device.user_agent,
        )

        raw_new_refresh_token = generate_refresh_token()
        await self._auth.create_refresh_token(
            user_id=user.id,
            session_id=refresh_token.session_id,
            token_hash=hash_refresh_token(raw_new_refresh_token),
            expires_at=expires_at,
        )

        access_token = await self._build_access_token(user)
        tokens = TokenResponse(access_token=access_token, refresh_token=raw_new_refresh_token)
        await self._db.commit()
        return tokens

    async def logout(self, *, raw_refresh_token: str) -> None:
        token_hash = hash_refresh_token(raw_refresh_token)
        refresh_token = await self._auth.get_refresh_token_by_hash(token_hash)

        if refresh_token is None or refresh_token.revoked_at is not None:
            return

        await self._auth.revoke_refresh_token(refresh_token)
        await self._auth.revoke_session(refresh_token.session_id)
        await self._db.commit()

    async def logout_all(self, *, user_id: uuid.UUID) -> None:
        await self._auth.revoke_all_for_user(user_id)
        await self._db.commit()

    async def request_password_reset(self, *, email: str) -> None:
        normalized_email = email.strip().lower()
        user = await self._users.get_by_email_any_tenant(email=normalized_email)

        # Always behave the same whether or not the account exists, so the
        # response can't be used to enumerate registered emails.
        if user is None or user.password_hash is None or user.status != "active":
            return

        await self._auth.invalidate_account_tokens(user_id=user.id, purpose="password_reset")

        raw_token = generate_secure_token()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=PASSWORD_RESET_TOKEN_TTL_MINUTES)
        await self._auth.create_account_token(
            user_id=user.id,
            tenant_id=user.tenant_id,
            purpose="password_reset",
            token_hash=hash_token(raw_token),
            expires_at=expires_at,
        )
        await self._db.commit()

        reset_url = f"{settings.frontend_base_url.rstrip('/')}/sifre-sifirla?token={raw_token}"
        await self._email_provider.send(
            to_email=user.email,
            title="NeuroDesk AI - Şifre sıfırlama",
            body=(
                "Şifreni sıfırlamak için bu bağlantıyı kullan (1 saat geçerlidir): "
                f"{reset_url}\n\nBu isteği sen yapmadıysan bu e-postayı yok sayabilirsin."
            ),
        )

    async def reset_password(self, *, raw_token: str, new_password: str) -> None:
        token = await self._auth.get_account_token_by_hash(
            token_hash=hash_token(raw_token), purpose="password_reset"
        )
        if token is None or token.used_at is not None or token.expires_at < datetime.now(timezone.utc):
            raise AuthError("This password reset link is invalid or has expired.")

        user = await self._users.get_by_id(token.user_id)
        if user is None or user.status != "active":
            raise AuthError("This password reset link is invalid or has expired.")

        user.password_hash = hash_password(new_password)
        await self._auth.mark_account_token_used(token)
        # A password reset is a strong signal of compromise or forgotten
        # credentials either way — sign the account out everywhere.
        await self._auth.revoke_all_for_user(user.id)
        await self._db.commit()

    async def invite_member(
        self, *, tenant_id: uuid.UUID, organization_id: uuid.UUID, email: str, role: str
    ):
        normalized_email = email.strip().lower()

        existing = await self._users.get_by_email_any_tenant(email=normalized_email)
        if existing is not None:
            raise ConflictError("A user with this email already exists.")

        user = User(
            tenant_id=tenant_id,
            organization_id=organization_id,
            email=normalized_email,
            password_hash=None,
            auth_provider="local",
            is_email_verified=False,
            status="invited",
        )
        await self._users.create(user)
        await self._users.create_profile(
            tenant_id=tenant_id, user_id=user.id, full_name=normalized_email
        )
        member = await self._orgs.create_member(
            tenant_id=tenant_id,
            organization_id=organization_id,
            user_id=user.id,
            role=role,
            status="invited",
        )

        raw_token = generate_secure_token()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=INVITE_TOKEN_TTL_MINUTES)
        await self._auth.create_account_token(
            user_id=user.id,
            tenant_id=tenant_id,
            purpose="invite",
            token_hash=hash_token(raw_token),
            expires_at=expires_at,
        )
        await self._db.commit()

        invite_url = f"{settings.frontend_base_url.rstrip('/')}/davet-kabul?token={raw_token}"
        await self._email_provider.send(
            to_email=normalized_email,
            title="NeuroDesk AI - Takım daveti",
            body=(
                "NeuroDesk AI ekibine katılmaya davet edildin. Daveti kabul etmek için "
                f"bu bağlantıyı kullan (7 gün geçerlidir): {invite_url}"
            ),
        )
        return member

    async def accept_invite(
        self, *, raw_token: str, password: str, display_name: str, device: DeviceContext
    ) -> TokenResponse:
        token = await self._auth.get_account_token_by_hash(
            token_hash=hash_token(raw_token), purpose="invite"
        )
        if token is None or token.used_at is not None or token.expires_at < datetime.now(timezone.utc):
            raise AuthError("This invitation link is invalid or has expired.")

        user = await self._users.get_by_id(token.user_id)
        if user is None or user.status != "invited":
            raise AuthError("This invitation link is invalid or has expired.")

        user.password_hash = hash_password(password)
        user.status = "active"
        user.is_email_verified = True

        profile = user.profile
        if profile is None:
            await self._users.create_profile(
                tenant_id=user.tenant_id, user_id=user.id, full_name=display_name
            )
        else:
            await self._users.update_profile(profile=profile, full_name=display_name)

        if user.organization_id is not None:
            member = await self._orgs.get_member_any_status(
                tenant_id=user.tenant_id,
                organization_id=user.organization_id,
                user_id=user.id,
            )
            if member is not None:
                await self._orgs.activate_member(member=member)

        await self._auth.mark_account_token_used(token)

        tokens = await self._issue_tokens(user, device)
        await self._db.commit()
        return tokens
