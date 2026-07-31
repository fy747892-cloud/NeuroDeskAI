from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.core.errors import AuthError, ConflictError
from app.core.security import verify_password
from app.db.session import get_db
from app.modules.audit.repository import AuditRepository
from app.modules.auth.repository import AuthRepository
from app.modules.organizations.repository import OrganizationRepository
from app.modules.users.consent import get_consent
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import (
    ConsentOut,
    ConsentUpdate,
    DeleteAccountRequest,
    UserOut,
    UserProfileUpdate,
)

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


@router.get("/me/consent", response_model=ConsentOut)
async def get_my_consent(current_user: User = Depends(get_current_user)) -> ConsentOut:
    return ConsentOut(**get_consent(current_user))


@router.patch("/me/consent", response_model=ConsentOut)
async def update_my_consent(
    body: ConsentUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConsentOut:
    users = UserRepository(db)
    await users.update_consent(user=current_user, consent=body.model_dump())

    await AuditRepository(db).record(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action="user.consent_updated",
        entity_type="user",
        entity_id=current_user.id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata=body.model_dump(),
    )
    await db.commit()
    return ConsentOut(**body.model_dump())


@router.get("/me/export")
async def export_my_data(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    orgs = OrganizationRepository(db)
    organization = None
    member = None
    if current_user.organization_id:
        organization = await orgs.get_by_id(
            tenant_id=current_user.tenant_id, organization_id=current_user.organization_id
        )
        member = await orgs.get_member(
            tenant_id=current_user.tenant_id,
            organization_id=current_user.organization_id,
            user_id=current_user.id,
        )

    sessions = await AuthRepository(db).list_active_sessions(user_id=current_user.id)

    return {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "account": {
            "id": str(current_user.id),
            "email": current_user.email,
            "status": current_user.status,
            "auth_provider": current_user.auth_provider,
            "is_email_verified": current_user.is_email_verified,
            "created_at": current_user.created_at.isoformat(),
        },
        "profile": (
            {
                "full_name": current_user.profile.full_name,
                "title": current_user.profile.title,
                "avatar_url": current_user.profile.avatar_url,
            }
            if current_user.profile
            else None
        ),
        "organization": (
            {"id": str(organization.id), "name": organization.name, "role": member.role if member else None}
            if organization
            else None
        ),
        "consent": get_consent(current_user),
        "security": {"totp_enabled": current_user.totp_enabled},
        "active_sessions": [
            {
                "id": str(session.id),
                "device_id": session.device_id,
                "ip_address": session.ip_address,
                "user_agent": session.user_agent,
                "created_at": session.created_at.isoformat(),
            }
            for session in sessions
        ],
    }


@router.delete("/me", status_code=204)
async def delete_me(
    body: DeleteAccountRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    if current_user.password_hash is None or not verify_password(
        body.password, current_user.password_hash
    ):
        raise AuthError("Incorrect password.")

    if current_user.organization_id:
        orgs = OrganizationRepository(db)
        member = await orgs.get_member(
            tenant_id=current_user.tenant_id,
            organization_id=current_user.organization_id,
            user_id=current_user.id,
        )
        if member and member.role == "owner":
            other_members = [
                m
                for m in await orgs.list_members(
                    tenant_id=current_user.tenant_id,
                    organization_id=current_user.organization_id,
                )
                if m.user_id != current_user.id
            ]
            if other_members:
                raise ConflictError(
                    "Transfer ownership or remove the other team members before deleting your account."
                )

    users = UserRepository(db)
    await users.soft_delete(current_user)
    await AuthRepository(db).revoke_all_for_user(current_user.id)

    await AuditRepository(db).record(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action="user.account_deleted",
        entity_type="user",
        entity_id=current_user.id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
