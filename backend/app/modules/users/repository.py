import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.users.models import User, UserProfile


class UserRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self._db.execute(
            select(User)
            .options(selectinload(User.profile))
            .where(User.id == user_id, User.is_deleted.is_(False))
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, *, tenant_id: uuid.UUID, email: str) -> User | None:
        result = await self._db.execute(
            select(User).where(
                User.tenant_id == tenant_id,
                User.email == email,
                User.is_deleted.is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_email_any_tenant(self, *, email: str) -> User | None:
        result = await self._db.execute(
            select(User).where(User.email == email, User.is_deleted.is_(False))
        )
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        self._db.add(user)
        await self._db.flush()
        return user

    async def create_profile(
        self,
        *,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        full_name: str,
        title: str | None = None,
        avatar_url: str | None = None,
    ) -> UserProfile:
        profile = UserProfile(
            tenant_id=tenant_id,
            user_id=user_id,
            full_name=full_name,
            title=title,
            avatar_url=avatar_url,
        )
        self._db.add(profile)
        await self._db.flush()
        return profile

    async def update_profile(
        self,
        *,
        profile: UserProfile,
        full_name: str | None = None,
        title: str | None = None,
        avatar_url: str | None = None,
    ) -> UserProfile:
        if full_name is not None:
            profile.full_name = full_name
        if title is not None:
            profile.title = title
        if avatar_url is not None:
            profile.avatar_url = avatar_url
        await self._db.flush()
        return profile

    async def update_active_organization(
        self, *, user: User, organization_id: uuid.UUID
    ) -> User:
        user.organization_id = organization_id
        await self._db.flush()
        return user
