import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import require_permission
from app.core.errors import ForbiddenError, NotFoundError
from app.core.permissions import Permission
from app.db.session import get_db
from app.modules.audit.repository import AuditRepository
from app.modules.organizations.models import Organization, OrganizationMember
from app.modules.organizations.repository import OrganizationRepository
from app.modules.auth.service import AuthService
from app.modules.organizations.schemas import (
    OrganizationCreate,
    OrganizationMemberInvite,
    OrganizationMemberOut,
    OrganizationMemberRoleUpdate,
    OrganizationOut,
    OrganizationUpdate,
)
from app.modules.users.models import User
from app.modules.users.repository import UserRepository

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.post("", response_model=OrganizationOut, status_code=201)
async def create_organization(
    body: OrganizationCreate,
    request: Request,
    current_user: User = Depends(require_permission(Permission.ORGANIZATIONS_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> Organization:
    organizations = OrganizationRepository(db)
    organization = await organizations.create_organization(
        tenant_id=current_user.tenant_id,
        name=body.name,
    )
    await organizations.create_member(
        tenant_id=current_user.tenant_id,
        organization_id=organization.id,
        user_id=current_user.id,
        role="owner",
    )
    await UserRepository(db).update_active_organization(
        user=current_user,
        organization_id=organization.id,
    )
    await AuditRepository(db).record(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action="organization.created",
        entity_type="organization",
        entity_id=organization.id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    return organization


@router.get("/current", response_model=OrganizationOut)
async def get_current_organization(
    current_user: User = Depends(require_permission(Permission.ORGANIZATIONS_READ)),
    db: AsyncSession = Depends(get_db),
) -> Organization:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    organization = await OrganizationRepository(db).get_by_id(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
    )
    if organization is None:
        raise NotFoundError("Current organization not found.")
    return organization


@router.patch("/current", response_model=OrganizationOut)
async def update_current_organization(
    body: OrganizationUpdate,
    request: Request,
    current_user: User = Depends(require_permission(Permission.ORGANIZATIONS_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> Organization:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    organizations = OrganizationRepository(db)
    organization = await organizations.get_by_id(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
    )
    if organization is None:
        raise NotFoundError("Current organization not found.")

    await organizations.update_organization(organization=organization, name=body.name)
    await AuditRepository(db).record(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action="organization.updated",
        entity_type="organization",
        entity_id=organization.id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata={"fields": ["name"] if body.name is not None else []},
    )
    await db.commit()
    return organization


@router.get("/members", response_model=list[OrganizationMemberOut])
async def list_current_organization_members(
    current_user: User = Depends(require_permission(Permission.USERS_READ)),
    db: AsyncSession = Depends(get_db),
) -> list[OrganizationMember]:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    return await OrganizationRepository(db).list_members(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
    )


@router.post("/members/invite", response_model=OrganizationMemberOut, status_code=201)
async def invite_organization_member(
    body: OrganizationMemberInvite,
    request: Request,
    current_user: User = Depends(require_permission(Permission.ROLES_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> OrganizationMember:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    member = await AuthService(db).invite_member(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        email=body.email,
        role=body.role.value,
    )
    await AuditRepository(db).record(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action="organization_member.invited",
        entity_type="organization_member",
        entity_id=member.id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata={"role": body.role.value},
    )
    await db.commit()
    member.email = body.email.strip().lower()
    member.full_name = None
    return member


@router.patch("/members/{member_id}/role", response_model=OrganizationMemberOut)
async def update_current_organization_member_role(
    member_id: uuid.UUID,
    body: OrganizationMemberRoleUpdate,
    request: Request,
    current_user: User = Depends(require_permission(Permission.ROLES_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> OrganizationMember:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    organizations = OrganizationRepository(db)
    member = await organizations.get_member_by_id(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        member_id=member_id,
    )
    if member is None:
        raise NotFoundError("Organization member not found.")

    if member.user_id == current_user.id:
        raise ForbiddenError("You cannot change your own organization role.")

    previous_role = member.role
    await organizations.update_member_role(member=member, role=body.role.value)
    await AuditRepository(db).record(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action="organization_member.role_updated",
        entity_type="organization_member",
        entity_id=member.id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata={"previous_role": previous_role, "role": body.role.value},
    )
    await db.commit()
    return member
