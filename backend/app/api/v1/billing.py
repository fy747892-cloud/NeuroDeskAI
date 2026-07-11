from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import require_permission
from app.core.permissions import Permission
from app.db.session import get_db
from app.modules.audit.repository import AuditRepository
from app.modules.billing.schemas import PlanOut, PlanSwitchIn, SubscriptionOut, UsageSummaryOut
from app.modules.billing.service import BillingService
from app.modules.users.models import User

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/plans", response_model=list[PlanOut])
async def list_plans(
    current_user: User = Depends(require_permission(Permission.BILLING_READ)),
    db: AsyncSession = Depends(get_db),
) -> list[PlanOut]:
    plans = await BillingService(db).list_plans()
    return [PlanOut.model_validate(plan) for plan in plans]


@router.get("/subscription", response_model=SubscriptionOut)
async def get_subscription(
    current_user: User = Depends(require_permission(Permission.BILLING_READ)),
    db: AsyncSession = Depends(get_db),
) -> SubscriptionOut:
    subscription, plan = await BillingService(db).get_subscription_with_plan(
        tenant_id=current_user.tenant_id
    )
    return SubscriptionOut(
        tenant_id=subscription.tenant_id,
        status=subscription.status,
        current_period_end=subscription.current_period_end,
        plan=PlanOut.model_validate(plan),
    )


@router.patch("/subscription", response_model=SubscriptionOut)
async def switch_subscription_plan(
    body: PlanSwitchIn,
    request: Request,
    current_user: User = Depends(require_permission(Permission.BILLING_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> SubscriptionOut:
    service = BillingService(db)
    await service.switch_plan(tenant_id=current_user.tenant_id, plan_code=body.plan_code)
    subscription, plan = await service.get_subscription_with_plan(
        tenant_id=current_user.tenant_id
    )
    await AuditRepository(db).record(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action="billing.plan_switched",
        entity_type="subscription",
        entity_id=subscription.id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata={"plan_code": plan.code},
    )
    await db.commit()
    return SubscriptionOut(
        tenant_id=subscription.tenant_id,
        status=subscription.status,
        current_period_end=subscription.current_period_end,
        plan=PlanOut.model_validate(plan),
    )


@router.get("/usage", response_model=UsageSummaryOut)
async def get_usage(
    current_user: User = Depends(require_permission(Permission.BILLING_READ)),
    db: AsyncSession = Depends(get_db),
) -> UsageSummaryOut:
    summary = await BillingService(db).get_usage_summary(tenant_id=current_user.tenant_id)
    return UsageSummaryOut(**summary)
