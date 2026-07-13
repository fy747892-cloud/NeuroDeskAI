import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.billing.models import Plan, Subscription, UsageQuota, UsageRecord


class PlanRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_by_code(self, *, code: str) -> Plan | None:
        result = await self._db.execute(select(Plan).where(Plan.code == code))
        return result.scalar_one_or_none()

    async def create(
        self, *, code: str, name: str, price: float, billing_period: str
    ) -> Plan:
        plan = Plan(code=code, name=name, price=price, billing_period=billing_period, status="active")
        self._db.add(plan)
        await self._db.flush()
        return plan

    async def list_all(self) -> list[Plan]:
        result = await self._db.execute(select(Plan).where(Plan.status == "active").order_by(Plan.price.asc()))
        return list(result.scalars().all())


class SubscriptionRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_by_tenant(self, *, tenant_id: uuid.UUID) -> Subscription | None:
        result = await self._db.execute(
            select(Subscription).where(Subscription.tenant_id == tenant_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self, *, tenant_id: uuid.UUID, plan_id: uuid.UUID, current_period_end: datetime
    ) -> Subscription:
        subscription = Subscription(
            tenant_id=tenant_id,
            plan_id=plan_id,
            status="active",
            current_period_end=current_period_end,
        )
        self._db.add(subscription)
        await self._db.flush()
        return subscription

    async def update_plan(
        self, *, subscription: Subscription, plan_id: uuid.UUID, current_period_end: datetime
    ) -> Subscription:
        subscription.plan_id = plan_id
        subscription.current_period_end = current_period_end
        await self._db.flush()
        return subscription


class UsageQuotaRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def get(self, *, tenant_id: uuid.UUID, quota_type: str) -> UsageQuota | None:
        result = await self._db.execute(
            select(UsageQuota).where(
                UsageQuota.tenant_id == tenant_id, UsageQuota.quota_type == quota_type
            )
        )
        return result.scalar_one_or_none()

    async def upsert(
        self, *, tenant_id: uuid.UUID, quota_type: str, limit_value: int, period: str = "daily"
    ) -> UsageQuota:
        existing = await self.get(tenant_id=tenant_id, quota_type=quota_type)
        if existing is not None:
            existing.limit_value = limit_value
            existing.period = period
            await self._db.flush()
            return existing

        quota = UsageQuota(
            tenant_id=tenant_id, quota_type=quota_type, limit_value=limit_value, period=period
        )
        self._db.add(quota)
        await self._db.flush()
        return quota


class UsageRecordRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def record(
        self, *, tenant_id: uuid.UUID, user_id: uuid.UUID, usage_type: str, quantity: int = 1
    ) -> UsageRecord:
        usage_record = UsageRecord(
            tenant_id=tenant_id,
            user_id=user_id,
            usage_type=usage_type,
            quantity=quantity,
            occurred_at=datetime.now(timezone.utc),
        )
        self._db.add(usage_record)
        await self._db.flush()
        return usage_record

    async def count_for_today(self, *, tenant_id: uuid.UUID, usage_type: str) -> int:
        today = datetime.now(timezone.utc).date()
        result = await self._db.execute(
            select(func.coalesce(func.sum(UsageRecord.quantity), 0)).where(
                UsageRecord.tenant_id == tenant_id,
                UsageRecord.usage_type == usage_type,
                func.date(UsageRecord.occurred_at) == today,
            )
        )
        return int(result.scalar_one())
