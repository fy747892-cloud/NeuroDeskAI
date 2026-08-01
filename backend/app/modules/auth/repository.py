import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import AccountToken, RefreshToken, UserSession


class AuthRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def create_session(
        self,
        *,
        user_id: uuid.UUID,
        tenant_id: uuid.UUID,
        device_id: str | None,
        ip_address: str | None,
        user_agent: str | None,
        expires_at: datetime,
    ) -> UserSession:
        session = UserSession(
            user_id=user_id,
            tenant_id=tenant_id,
            device_id=device_id,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at,
        )
        self._db.add(session)
        await self._db.flush()
        return session

    async def create_refresh_token(
        self,
        *,
        user_id: uuid.UUID,
        session_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> RefreshToken:
        refresh_token = RefreshToken(
            user_id=user_id,
            session_id=session_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self._db.add(refresh_token)
        await self._db.flush()
        return refresh_token

    async def get_refresh_token_by_hash(self, token_hash: str) -> RefreshToken | None:
        result = await self._db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def revoke_refresh_token(self, refresh_token: RefreshToken) -> None:
        refresh_token.revoked_at = datetime.now(timezone.utc)
        await self._db.flush()

    async def list_active_sessions(self, *, user_id: uuid.UUID) -> list[UserSession]:
        now = datetime.now(timezone.utc)
        result = await self._db.execute(
            select(UserSession)
            .where(
                UserSession.user_id == user_id,
                UserSession.revoked_at.is_(None),
                UserSession.expires_at > now,
            )
            .order_by(UserSession.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_session_by_id(self, *, session_id: uuid.UUID) -> UserSession | None:
        result = await self._db.execute(select(UserSession).where(UserSession.id == session_id))
        return result.scalar_one_or_none()

    async def touch_session(
        self,
        *,
        session_id: uuid.UUID,
        expires_at: datetime,
        ip_address: str | None,
        user_agent: str | None,
    ) -> None:
        await self._db.execute(
            update(UserSession)
            .where(UserSession.id == session_id)
            .values(expires_at=expires_at, ip_address=ip_address, user_agent=user_agent)
        )

    async def revoke_session(self, session_id: uuid.UUID) -> None:
        now = datetime.now(timezone.utc)
        await self._db.execute(
            update(UserSession).where(UserSession.id == session_id).values(revoked_at=now)
        )
        await self._db.execute(
            update(RefreshToken)
            .where(RefreshToken.session_id == session_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now)
        )

    async def revoke_all_for_user(self, user_id: uuid.UUID) -> None:
        now = datetime.now(timezone.utc)
        await self._db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        await self._db.execute(
            update(UserSession)
            .where(UserSession.user_id == user_id, UserSession.revoked_at.is_(None))
            .values(revoked_at=now)
        )

    async def create_account_token(
        self,
        *,
        user_id: uuid.UUID,
        tenant_id: uuid.UUID,
        purpose: str,
        token_hash: str,
        expires_at: datetime,
    ) -> AccountToken:
        token = AccountToken(
            user_id=user_id,
            tenant_id=tenant_id,
            purpose=purpose,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self._db.add(token)
        await self._db.flush()
        return token

    async def get_account_token_by_hash(self, *, token_hash: str, purpose: str) -> AccountToken | None:
        result = await self._db.execute(
            select(AccountToken).where(
                AccountToken.token_hash == token_hash,
                AccountToken.purpose == purpose,
            )
        )
        return result.scalar_one_or_none()

    async def mark_account_token_used(self, token: AccountToken) -> None:
        token.used_at = datetime.now(timezone.utc)
        await self._db.flush()

    async def invalidate_account_tokens(self, *, user_id: uuid.UUID, purpose: str) -> None:
        now = datetime.now(timezone.utc)
        await self._db.execute(
            update(AccountToken)
            .where(
                AccountToken.user_id == user_id,
                AccountToken.purpose == purpose,
                AccountToken.used_at.is_(None),
            )
            .values(used_at=now)
        )
