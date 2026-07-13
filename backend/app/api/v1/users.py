from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.db.session import get_db
from app.modules.audit.repository import AuditRepository
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserOut, UserProfileUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.patch("/me", response_model=UserOut)
async def update_me(
    body: UserProfileUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    users = UserRepository(db)
    profile = current_user.profile
    if profile is None:
        profile = await users.create_profile(
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            full_name=body.full_name or current_user.email,
        )
    else:
        await users.update_profile(
            profile=profile,
            full_name=body.full_name,
            title=body.title,
            avatar_url=str(body.avatar_url) if body.avatar_url is not None else None,
        )

    await AuditRepository(db).record(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action="user.profile_updated",
        entity_type="user",
        entity_id=current_user.id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    return await users.get_by_id(current_user.id) or current_user
