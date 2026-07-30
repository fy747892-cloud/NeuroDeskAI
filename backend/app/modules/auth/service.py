import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AuthError, ConflictError
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    refresh_token_expiry,
    verify_password,
)
from app.modules.auth.repository import AuthRepository
from app.modules.auth.schemas import TokenResponse
from app.modules.billing.service import BillingService
from app.modules.organizations.repository import OrganizationRepository
from app.modules.users.models import User
from app.modules.users.repository import UserRepository


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

    async def authenticate(self, *, email: str, password: str, device: DeviceContext) -> TokenResponse:
        normalized_email = email.strip().lower()
        user = await self._users.get_by_email_any_tenant(email=normalized_email)

        if user is None or user.password_hash is None or not verify_password(
            password, user.password_hash
        ):
            raise AuthError("Invalid email or password.")

        if user.status != "active":
            raise AuthError("This account is not active.")

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

        member = await self._orgs.get_member(
            tenant_id=user.tenant_id,
            organization_id=user.organization_id,
            user_id=user.id,
        ) if user.organization_id else None

        access_token = create_access_token(
            user_id=user.id,
            tenant_id=user.tenant_id,
            organization_id=user.organization_id,
            roles=[member.role] if member else [],
        )

        return TokenResponse(access_token=access_token, refresh_token=raw_refresh_token)

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

        tokens = await self._issue_tokens(user, device)
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
