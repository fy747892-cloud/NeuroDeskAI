import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import RefreshToken, UserSession


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

    async def revoke_session(self, session_id: uuid.UUID) -> None:
        await self._db.execute(
            update(UserSession)
            .where(UserSession.id == session_id)
            .values(revoked_at=datetime.now(timezone.utc))
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
