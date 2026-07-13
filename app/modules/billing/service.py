import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, QuotaExceededError, ValidationAppError
from app.modules.billing.models import Plan, Subscription
from app.modules.billing.repository import (
    PlanRepository,
    SubscriptionRepository,
    UsageQuotaRepository,
    UsageRecordRepository,
)
from app.modules.organizations.models import Tenant

AI_REQUESTS_QUOTA_TYPE = "ai_requests"
SUBSCRIPTION_PERIOD_DAYS = 30

PLAN_QUOTA_DEFAULTS: dict[str, int] = {
    "free": 5,
    "pro": 50,
    "enterprise": 500,
}

PLAN_SEED_DATA: list[tuple[str, str, float, str]] = [
    ("free", "Free", 0.0, "monthly"),
    ("pro", "Pro", 29.0, "monthly"),
    ("enterprise", "Enterprise", 199.0, "monthly"),
]


class BillingService:
    def __init__(self, db: AsyncSession):
        self._db = db
        self._plans = PlanRepository(db)
        self._subscriptions = SubscriptionRepository(db)
        self._quotas = UsageQuotaRepository(db)
        self._usage = UsageRecordRepository(db)

    async def ensure_plans_seeded(self) -> None:
        created_any = False
        for code, name, price, billing_period in PLAN_SEED_DATA:
            existing = await self._plans.get_by_code(code=code)
            if existing is None:
                await self._plans.create(
                    code=code, name=name, price=price, billing_period=billing_period
                )
                created_any = True
        if created_any:
            await self._db.commit()

    async def _get_or_create_plan(self, *, code: str) -> Plan:
        plan = await self._plans.get_by_code(code=code)
        if plan is not None:
            return plan
        seed = next((entry for entry in PLAN_SEED_DATA if entry[0] == code), None)
        if seed is None:
            raise NotFoundError(f"Unknown plan code '{code}'.")
        _, name, price, billing_period = seed
        return await self._plans.create(
            code=code, name=name, price=price, billing_period=billing_period
        )

    async def create_default_subscription(self, *, tenant_id: uuid.UUID) -> Subscription:
        plan = await self._get_or_create_plan(code="free")
        period_end = datetime.now(timezone.utc) + timedelta(days=SUBSCRIPTION_PERIOD_DAYS)
        subscription = await self._subscriptions.create(
            tenant_id=tenant_id, plan_id=plan.id, current_period_end=period_end
        )
        await self._quotas.upsert(
            tenant_id=tenant_id,
            quota_type=AI_REQUESTS_QUOTA_TYPE,
            limit_value=PLAN_QUOTA_DEFAULTS[plan.code],
        )
        return subscription

    async def switch_plan(self, *, tenant_id: uuid.UUID, plan_code: str) -> Subscription:
        if plan_code not in PLAN_QUOTA_DEFAULTS:
            raise ValidationAppError(f"Unknown plan code '{plan_code}'.")

        subscription = await self._subscriptions.get_by_tenant(tenant_id=tenant_id)
        if subscription is None:
            raise NotFoundError("No subscription found for this tenant.")

        plan = await self._get_or_create_plan(code=plan_code)
        period_end = datetime.now(timezone.utc) + timedelta(days=SUBSCRIPTION_PERIOD_DAYS)
        subscription = await self._subscriptions.update_plan(
            subscription=subscription, plan_id=plan.id, current_period_end=period_end
        )
        await self._quotas.upsert(
            tenant_id=tenant_id,
            quota_type=AI_REQUESTS_QUOTA_TYPE,
            limit_value=PLAN_QUOTA_DEFAULTS[plan.code],
        )

        tenant = await self._db.get(Tenant, tenant_id)
        if tenant is not None:
            tenant.plan_type = plan.code
            await self._db.flush()

        return subscription

    async def get_subscription_with_plan(self, *, tenant_id: uuid.UUID) -> tuple[Subscription, Plan]:
        subscription = await self._subscriptions.get_by_tenant(tenant_id=tenant_id)
        if subscription is None:
            raise NotFoundError("No subscription found for this tenant.")
        plan = await self._db.get(Plan, subscription.plan_id)
        if plan is None:
            raise NotFoundError("Subscription plan not found.")
        return subscription, plan

    async def list_plans(self) -> list[Plan]:
        await self.ensure_plans_seeded()
        return await self._plans.list_all()

    async def enforce_ai_usage_guard(self, *, tenant_id: uuid.UUID) -> None:
        quota = await self._quotas.get(tenant_id=tenant_id, quota_type=AI_REQUESTS_QUOTA_TYPE)
        if quota is None:
            return
        used = await self._usage.count_for_today(
            tenant_id=tenant_id, usage_type=AI_REQUESTS_QUOTA_TYPE
        )
        if used >= quota.limit_value:
            raise QuotaExceededError(
                f"Daily AI usage quota ({quota.limit_value} requests) has been reached."
            )

    async def record_ai_usage(self, *, tenant_id: uuid.UUID, user_id: uuid.UUID) -> None:
        await self._usage.record(
            tenant_id=tenant_id, user_id=user_id, usage_type=AI_REQUESTS_QUOTA_TYPE
        )

    async def get_usage_summary(self, *, tenant_id: uuid.UUID) -> dict:
        quota = await self._quotas.get(tenant_id=tenant_id, quota_type=AI_REQUESTS_QUOTA_TYPE)
        used = await self._usage.count_for_today(
            tenant_id=tenant_id, usage_type=AI_REQUESTS_QUOTA_TYPE
        )
        limit_value = quota.limit_value if quota is not None else 0
        return {
            "quota_type": AI_REQUESTS_QUOTA_TYPE,
            "period": quota.period if quota is not None else "daily",
            "limit_value": limit_value,
            "used": used,
            "remaining": max(0, limit_value - used),
        }
