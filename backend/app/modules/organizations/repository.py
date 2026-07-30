import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.organizations.models import Organization, OrganizationMember, Tenant
from app.modules.users.models import User, UserProfile


class OrganizationRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def create_personal_tenant_and_org(self, *, display_name: str) -> tuple[Tenant, Organization]:
        tenant = Tenant(name=display_name, status="active", plan_type="free")
        self._db.add(tenant)
        await self._db.flush()

        organization = Organization(
            tenant_id=tenant.id, name=display_name, type="personal", status="active"
        )
        self._db.add(organization)
        await self._db.flush()

        return tenant, organization

    async def create_organization(
        self,
        *,
        tenant_id: uuid.UUID,
        name: str,
        organization_type: str = "workspace",
    ) -> Organization:
        organization = Organization(
            tenant_id=tenant_id,
            name=name,
            type=organization_type,
            status="active",
        )
        self._db.add(organization)
        await self._db.flush()
        return organization

    async def create_member(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str,
        status: str = "active",
    ) -> OrganizationMember:
        member = OrganizationMember(
            tenant_id=tenant_id,
            organization_id=organization_id,
            user_id=user_id,
            role=role,
            status=status,
        )
        self._db.add(member)
        await self._db.flush()
        return member

    async def activate_member(self, *, member: OrganizationMember) -> OrganizationMember:
        member.status = "active"
        await self._db.flush()
        return member

    async def get_by_id(
        self, *, tenant_id: uuid.UUID, organization_id: uuid.UUID
    ) -> Organization | None:
        result = await self._db.execute(
            select(Organization).where(
                Organization.tenant_id == tenant_id,
                Organization.id == organization_id,
                Organization.is_deleted.is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def get_member(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> OrganizationMember | None:
        result = await self._db.execute(
            select(OrganizationMember).where(
                OrganizationMember.tenant_id == tenant_id,
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.user_id == user_id,
                OrganizationMember.status == "active",
                OrganizationMember.is_deleted.is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def list_members(
        self, *, tenant_id: uuid.UUID, organization_id: uuid.UUID
    ) -> list[OrganizationMember]:
        result = await self._db.execute(
            select(OrganizationMember)
            .where(
                OrganizationMember.tenant_id == tenant_id,
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.status.in_(["active", "invited"]),
                OrganizationMember.is_deleted.is_(False),
            )
            .order_by(OrganizationMember.created_at.asc())
        )
        members = list(result.scalars().all())
        if not members:
            return members

        # OrganizationMember only stores user_id; attach email/full_name here
        # (rather than a relationship) so OrganizationMemberOut.from_attributes
        # can read them without changing the ORM model's join surface.
        user_ids = [member.user_id for member in members]
        user_result = await self._db.execute(
            select(User.id, User.email, UserProfile.full_name)
            .outerjoin(UserProfile, UserProfile.user_id == User.id)
            .where(User.id.in_(user_ids))
        )
        user_info = {row.id: (row.email, row.full_name) for row in user_result.all()}

        for member in members:
            email, full_name = user_info.get(member.user_id, (None, None))
            member.email = email
            member.full_name = full_name

        return members

    async def get_member_any_status(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> OrganizationMember | None:
        result = await self._db.execute(
            select(OrganizationMember).where(
                OrganizationMember.tenant_id == tenant_id,
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.user_id == user_id,
                OrganizationMember.is_deleted.is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def get_member_by_id(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        member_id: uuid.UUID,
    ) -> OrganizationMember | None:
        result = await self._db.execute(
            select(OrganizationMember).where(
                OrganizationMember.tenant_id == tenant_id,
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.id == member_id,
                OrganizationMember.status == "active",
                OrganizationMember.is_deleted.is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def update_member_role(
        self, *, member: OrganizationMember, role: str
    ) -> OrganizationMember:
        member.role = role
        await self._db.flush()
        return member

    async def update_organization(
        self, *, organization: Organization, name: str | None = None
    ) -> Organization:
        if name is not None:
            organization.name = name
        await self._db.flush()
        return organization
