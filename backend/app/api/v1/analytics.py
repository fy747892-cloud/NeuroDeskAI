from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import require_permission
from app.core.errors import NotFoundError
from app.core.permissions import Permission
from app.db.session import get_db
from app.modules.analytics.schemas import (
    AggregateIn,
    AggregateSummaryOut,
    AIMetricOut,
    AnalyticsOverviewOut,
    AppointmentMetricOut,
    CallMetricOut,
    TaskMetricOut,
)
from app.modules.analytics.service import AnalyticsService
from app.modules.audit.repository import AuditRepository
from app.modules.users.models import User

router = APIRouter(prefix="/analytics", tags=["analytics"])

DEFAULT_RANGE_DAYS = 7


def _default_date_range(date_from: date | None, date_to: date | None) -> tuple[date, date]:
    today = datetime.now(timezone.utc).date()
    resolved_to = date_to or today
    resolved_from = date_from or (resolved_to - timedelta(days=DEFAULT_RANGE_DAYS - 1))
    return resolved_from, resolved_to


@router.post("/aggregate", response_model=AggregateSummaryOut)
async def aggregate_analytics(
    body: AggregateIn,
    request: Request,
    current_user: User = Depends(require_permission(Permission.ANALYTICS_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> AggregateSummaryOut:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    target_date = body.date or datetime.now(timezone.utc).date()
    summary = await AnalyticsService(db).aggregate_for_date(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        date=target_date,
    )
    await AuditRepository(db).record(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action="analytics.aggregate_run",
        entity_type="analytics",
        entity_id=current_user.organization_id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata={"date": target_date.isoformat()},
    )
    await db.commit()
    return AggregateSummaryOut(**summary)


@router.get("/overview", response_model=AnalyticsOverviewOut)
async def get_analytics_overview(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    current_user: User = Depends(require_permission(Permission.ANALYTICS_READ)),
    db: AsyncSession = Depends(get_db),
) -> AnalyticsOverviewOut:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    resolved_from, resolved_to = _default_date_range(date_from, date_to)
    overview = await AnalyticsService(db).get_overview(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        date_from=resolved_from,
        date_to=resolved_to,
    )
    return AnalyticsOverviewOut(**overview)


@router.get("/tasks", response_model=list[TaskMetricOut])
async def get_task_analytics(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    current_user: User = Depends(require_permission(Permission.ANALYTICS_READ)),
    db: AsyncSession = Depends(get_db),
):
    resolved_from, resolved_to = _default_date_range(date_from, date_to)
    return await AnalyticsService(db).get_task_metrics(
        tenant_id=current_user.tenant_id, date_from=resolved_from, date_to=resolved_to
    )


@router.get("/calls", response_model=list[CallMetricOut])
async def get_call_analytics(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    current_user: User = Depends(require_permission(Permission.ANALYTICS_READ)),
    db: AsyncSession = Depends(get_db),
):
    resolved_from, resolved_to = _default_date_range(date_from, date_to)
    return await AnalyticsService(db).get_call_metrics(
        tenant_id=current_user.tenant_id, date_from=resolved_from, date_to=resolved_to
    )


@router.get("/appointments", response_model=list[AppointmentMetricOut])
async def get_appointment_analytics(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    current_user: User = Depends(require_permission(Permission.ANALYTICS_READ)),
    db: AsyncSession = Depends(get_db),
):
    resolved_from, resolved_to = _default_date_range(date_from, date_to)
    return await AnalyticsService(db).get_appointment_metrics(
        tenant_id=current_user.tenant_id, date_from=resolved_from, date_to=resolved_to
    )


@router.get("/ai", response_model=list[AIMetricOut])
async def get_ai_analytics(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    current_user: User = Depends(require_permission(Permission.ANALYTICS_READ)),
    db: AsyncSession = Depends(get_db),
):
    resolved_from, resolved_to = _default_date_range(date_from, date_to)
    return await AnalyticsService(db).get_ai_metrics(
        tenant_id=current_user.tenant_id, date_from=resolved_from, date_to=resolved_to
    )
