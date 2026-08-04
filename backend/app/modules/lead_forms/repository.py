import secrets
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.lead_forms.models import LeadForm


def generate_public_token() -> str:
    return secrets.token_urlsafe(24)


class LeadFormRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def create(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        owner_user_id: uuid.UUID,
    ) -> LeadForm:
        lead_form = LeadForm(
            tenant_id=tenant_id,
            organization_id=organization_id,
            owner_user_id=owner_user_id,
            public_token=generate_public_token(),
            is_active=True,
        )
        self._db.add(lead_form)
        await self._db.flush()
        return lead_form

    async def get_by_organization(
        self, *, tenant_id: uuid.UUID, organization_id: uuid.UUID
    ) -> LeadForm | None:
        result = await self._db.execute(
            select(LeadForm).where(
                LeadForm.tenant_id == tenant_id,
                LeadForm.organization_id == organization_id,
                LeadForm.is_deleted.is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_token(self, *, public_token: str) -> LeadForm | None:
        result = await self._db.execute(
            select(LeadForm).where(
                LeadForm.public_token == public_token,
                LeadForm.is_deleted.is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def update_active(self, *, lead_form: LeadForm, is_active: bool) -> LeadForm:
        lead_form.is_active = is_active
        await self._db.flush()
        return lead_form

    async def rotate_token(self, *, lead_form: LeadForm) -> LeadForm:
        lead_form.public_token = generate_public_token()
        await self._db.flush()
        return lead_form
