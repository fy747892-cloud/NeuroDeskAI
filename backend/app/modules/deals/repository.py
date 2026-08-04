import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.deals.models import Deal

OPEN_STAGES = ("lead", "proposal_sent", "negotiation", "invoiced")


class DealRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def create_deal(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        owner_user_id: uuid.UUID,
        title: str,
        description: str | None = None,
        value: float | None = None,
        currency: str = "TRY",
        stage: str = "lead",
        expected_close_date: datetime | None = None,
        contact_id: uuid.UUID | None = None,
        source_type: str = "manual",
        source_id: uuid.UUID | None = None,
        ai_action_approval_id: uuid.UUID | None = None,
        custom_fields: dict | None = None,
    ) -> Deal:
        deal = Deal(
            tenant_id=tenant_id,
            organization_id=organization_id,
            owner_user_id=owner_user_id,
            contact_id=contact_id,
            title=title,
            description=description,
            value=value,
            currency=currency,
            stage=stage,
            expected_close_date=expected_close_date,
            source_type=source_type,
            source_id=source_id,
            ai_action_approval_id=ai_action_approval_id,
            custom_fields=custom_fields or {},
        )
        self._db.add(deal)
        await self._db.flush()
        return deal

    async def list_deals(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        stage: str | None = None,
        contact_id: uuid.UUID | None = None,
    ) -> list[Deal]:
        statement = select(Deal).where(
            Deal.tenant_id == tenant_id,
            Deal.organization_id == organization_id,
            Deal.is_deleted.is_(False),
        )
        if stage is not None:
            statement = statement.where(Deal.stage == stage)
        if contact_id is not None:
            statement = statement.where(Deal.contact_id == contact_id)
        result = await self._db.execute(statement.order_by(Deal.created_at.desc()))
        return list(result.scalars().all())

    async def get_deal(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
    ) -> Deal | None:
        result = await self._db.execute(
            select(Deal).where(
                Deal.tenant_id == tenant_id,
                Deal.organization_id == organization_id,
                Deal.id == deal_id,
                Deal.is_deleted.is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def get_deal_by_approval(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        approval_id: uuid.UUID,
    ) -> Deal | None:
        result = await self._db.execute(
            select(Deal).where(
                Deal.tenant_id == tenant_id,
                Deal.organization_id == organization_id,
                Deal.ai_action_approval_id == approval_id,
                Deal.is_deleted.is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def update_deal(
        self,
        *,
        deal: Deal,
        title: str | None = None,
        description: str | None = None,
        value: float | None = None,
        currency: str | None = None,
        stage: str | None = None,
        expected_close_date: datetime | None = None,
        contact_id: uuid.UUID | None = None,
        custom_fields: dict | None = None,
    ) -> Deal:
        if title is not None:
            deal.title = title
        if description is not None:
            deal.description = description
        if value is not None:
            deal.value = value
        if currency is not None:
            deal.currency = currency
        if stage is not None:
            deal.stage = stage
        if expected_close_date is not None:
            deal.expected_close_date = expected_close_date
        if contact_id is not None:
            deal.contact_id = contact_id
        if custom_fields is not None:
            deal.custom_fields = custom_fields
        await self._db.flush()
        return deal

    async def soft_delete_deal(self, *, deal: Deal) -> None:
        deal.is_deleted = True
        deal.deleted_at = datetime.now(timezone.utc)
        await self._db.flush()

    async def count_open_by_contact(
        self, *, tenant_id: uuid.UUID, organization_id: uuid.UUID, contact_id: uuid.UUID
    ) -> int:
        result = await self._db.execute(
            select(func.count(Deal.id)).where(
                Deal.tenant_id == tenant_id,
                Deal.organization_id == organization_id,
                Deal.contact_id == contact_id,
                Deal.is_deleted.is_(False),
                Deal.stage.in_(OPEN_STAGES),
            )
        )
        return result.scalar_one()

    async def sum_open_value_by_contact(
        self, *, tenant_id: uuid.UUID, organization_id: uuid.UUID, contact_id: uuid.UUID
    ) -> float:
        result = await self._db.execute(
            select(func.coalesce(func.sum(Deal.value), 0.0)).where(
                Deal.tenant_id == tenant_id,
                Deal.organization_id == organization_id,
                Deal.contact_id == contact_id,
                Deal.is_deleted.is_(False),
                Deal.stage.in_(OPEN_STAGES),
            )
        )
        return float(result.scalar_one() or 0.0)

    async def count_open(self, *, tenant_id: uuid.UUID, organization_id: uuid.UUID) -> int:
        result = await self._db.execute(
            select(func.count(Deal.id)).where(
                Deal.tenant_id == tenant_id,
                Deal.organization_id == organization_id,
                Deal.is_deleted.is_(False),
                Deal.stage.in_(OPEN_STAGES),
            )
        )
        return result.scalar_one()

    async def pipeline_by_stage(
        self, *, tenant_id: uuid.UUID, organization_id: uuid.UUID
    ) -> list[tuple[str, str, float, int]]:
        result = await self._db.execute(
            select(
                Deal.stage,
                Deal.currency,
                func.coalesce(func.sum(Deal.value), 0.0),
                func.count(Deal.id),
            )
            .where(
                Deal.tenant_id == tenant_id,
                Deal.organization_id == organization_id,
                Deal.is_deleted.is_(False),
            )
            .group_by(Deal.stage, Deal.currency)
        )
        return [(stage, currency, float(total), count) for stage, currency, total, count in result.all()]

    async def pipeline_by_expected_month(
        self, *, tenant_id: uuid.UUID, organization_id: uuid.UUID
    ) -> list[tuple[str, str, float, int]]:
        month = func.to_char(Deal.expected_close_date, "YYYY-MM")
        result = await self._db.execute(
            select(
                month,
                Deal.currency,
                func.coalesce(func.sum(Deal.value), 0.0),
                func.count(Deal.id),
            )
            .where(
                Deal.tenant_id == tenant_id,
                Deal.organization_id == organization_id,
                Deal.is_deleted.is_(False),
                Deal.stage.in_(OPEN_STAGES),
                Deal.expected_close_date.is_not(None),
            )
            .group_by(month, Deal.currency)
            .order_by(month)
        )
        return [(m, currency, float(total), count) for m, currency, total, count in result.all()]