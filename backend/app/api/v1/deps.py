import uuid

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AuthError
from app.core.permissions import Permission, ensure_permission
from app.core.security import decode_access_token
from app.core.tenant import TenantContext
from app.db.session import get_db
from app.modules.organizations.repository import OrganizationRepository
from app.modules.users.models import User
from app.modules.users.repository import UserRepository

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None:
        raise AuthError("Missing authentication token.")

    try:
        payload = decode_access_token(credentials.credentials)
    except InvalidTokenError as exc:
        raise AuthError("Invalid or expired token.") from exc

    if payload.get("token_type") != "access":
        raise AuthError("Invalid token type.")

    try:
        user_id = uuid.UUID(payload["user_id"])
    except (KeyError, ValueError) as exc:
        raise AuthError("Invalid token payload.") from exc

    user = await UserRepository(db).get_by_id(user_id)
    if user is None or user.status != "active":
        raise AuthError("User not found or inactive.")

    return user


async def get_current_tenant_context(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TenantContext:
    if current_user.organization_id is None:
        raise AuthError("User has no active organization.")

    member = await OrganizationRepository(db).get_member(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
    )
    if member is None:
        raise AuthError("User has no active organization membership.")

    return TenantContext(
        user=current_user,
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        role=member.role,
    )


def require_permission(permission: Permission):
    async def _require_permission(
        tenant_context: TenantContext = Depends(get_current_tenant_context),
    ) -> User:
        ensure_permission(tenant_context.role, permission)
        return tenant_context.user

    return _require_permission
