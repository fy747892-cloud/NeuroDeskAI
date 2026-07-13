import uuid
from datetime import date as date_type

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics.models import (
    AICostLog,
    AnalyticsAIMetric,
    AnalyticsAppointmentMetric,
    AnalyticsCallMetric,
    AnalyticsDailyUserStat,
    AnalyticsTaskMetric,
)

MOCK_COST_PER_1K_TOKENS = 0.002

# (provider, model) -> (input $/1K tokens, output $/1K tokens).
# OpenAI rates as published at integration time — prices change over time,
# update here if the account's actual billing rates drift from this table.
# whisper-1/tts-1 are actually billed per audio minute/character, not per token —
# these rates are a rough character-count-based proxy (same spirit as the
# len(text)//4 token estimate used elsewhere), not exact OpenAI billing.
PRICING_TABLE: dict[tuple[str, str], tuple[float, float]] = {
    ("openai", "gpt-4o-mini"): (0.00015, 0.0006),
    ("openai", "text-embedding-3-small"): (0.00002, 0.00002),
    ("openai", "whisper-1"): (0.0, 0.0006),
    ("openai", "tts-1"): (0.0015, 0.0),
}


def _cost_for(*, provider: str, model: str, input_tokens: int, output_tokens: int) -> float:
    rates = PRICING_TABLE.get((provider, model))
    if rates is None:
        return (input_tokens + output_tokens) / 1000 * MOCK_COST_PER_1K_TOKENS
    input_rate, output_rate = rates
    return (input_tokens / 1000 * input_rate) + (output_tokens / 1000 * output_rate)


class AICostLogRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def record(
        self,
        *,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        provider: str,
        model: str,
        source_type: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: int,
    ) -> AICostLog:
        cost_amount = _cost_for(
            provider=provider, model=model, input_tokens=input_tokens, output_tokens=output_tokens
        )
        log = AICostLog(
            tenant_id=tenant_id,
            user_id=user_id,
            provider=provider,
            model=model,
            source_type=source_type,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_amount=cost_amount,
            latency_ms=latency_ms,
        )
        self._db.add(log)
        await self._db.flush()
        return log

    async def summarize_for_date(self, *, tenant_id: uuid.UUID, date: date_type) -> dict:
        result = await self._db.execute(
            select(
                func.count(AICostLog.id),
                func.coalesce(func.sum(AICostLog.cost_amount), 0.0),
                func.coalesce(func.avg(AICostLog.latency_ms), 0.0),
            ).where(AICostLog.tenant_id == tenant_id, func.date(AICostLog.created_at) == date)
        )
        request_count, cost_amount, avg_latency_ms = result.one()
        return {
            "request_count": request_count,
            "cost_amount": float(cost_amount),
            "avg_latency_ms": float(avg_latency_ms),
        }

    async def summarize_per_user_for_date(
        self, *, tenant_id: uuid.UUID, date: date_type
    ) -> dict[uuid.UUID, dict]:
        result = await self._db.execute(
            select(
                AICostLog.user_id,
                func.count(AICostLog.id),
                func.coalesce(func.sum(AICostLog.cost_amount), 0.0),
            )
            .where(AICostLog.tenant_id == tenant_id, func.date(AICostLog.created_at) == date)
            .group_by(AICostLog.user_id)
        )
        return {
            user_id: {"ai_requests": count, "ai_cost_amount": float(cost)}
            for user_id, count, cost in result.all()
        }


class AnalyticsMetricsRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def upsert_task_metric(
        self,
        *,
        tenant_id: uuid.UUID,
        date: date_type,
        created_count: int,
        completed_count: int,
        overdue_count: int,
    ) -> AnalyticsTaskMetric:
        result = await self._db.execute(
            select(AnalyticsTaskMetric).where(
                AnalyticsTaskMetric.tenant_id == tenant_id, AnalyticsTaskMetric.date == date
            )
        )
        metric = result.scalar_one_or_none()
        if metric is None:
            metric = AnalyticsTaskMetric(tenant_id=tenant_id, date=date)
            self._db.add(metric)
        metric.created_count = created_count
        metric.completed_count = completed_count
        metric.overdue_count = overdue_count
        await self._db.flush()
        return metric

    async def list_task_metrics(
        self, *, tenant_id: uuid.UUID, date_from: date_type, date_to: date_type
    ) -> list[AnalyticsTaskMetric]:
        result = await self._db.execute(
            select(AnalyticsTaskMetric)
            .where(
                AnalyticsTaskMetric.tenant_id == tenant_id,
                AnalyticsTaskMetric.date >= date_from,
                AnalyticsTaskMetric.date <= date_to,
            )
            .order_by(AnalyticsTaskMetric.date.asc())
        )
        return list(result.scalars().all())

    async def upsert_call_metric(
        self, *, tenant_id: uuid.UUID, date: date_type, call_count: int, analyzed_count: int
    ) -> AnalyticsCallMetric:
        result = await self._db.execute(
            select(AnalyticsCallMetric).where(
                AnalyticsCallMetric.tenant_id == tenant_id, AnalyticsCallMetric.date == date
            )
        )
        metric = result.scalar_one_or_none()
        if metric is None:
            metric = AnalyticsCallMetric(tenant_id=tenant_id, date=date)
            self._db.add(metric)
        metric.call_count = call_count
        metric.analyzed_count = analyzed_count
        await self._db.flush()
        return metric

    async def list_call_metrics(
        self, *, tenant_id: uuid.UUID, date_from: date_type, date_to: date_type
    ) -> list[AnalyticsCallMetric]:
        result = await self._db.execute(
            select(AnalyticsCallMetric)
            .where(
                AnalyticsCallMetric.tenant_id == tenant_id,
                AnalyticsCallMetric.date >= date_from,
                AnalyticsCallMetric.date <= date_to,
            )
            .order_by(AnalyticsCallMetric.date.asc())
        )
        return list(result.scalars().all())

    async def upsert_appointment_metric(
        self, *, tenant_id: uuid.UUID, date: date_type, completed_count: int, upcoming_count: int
    ) -> AnalyticsAppointmentMetric:
        result = await self._db.execute(
            select(AnalyticsAppointmentMetric).where(
                AnalyticsAppointmentMetric.tenant_id == tenant_id,
                AnalyticsAppointmentMetric.date == date,
            )
        )
        metric = result.scalar_one_or_none()
        if metric is None:
            metric = AnalyticsAppointmentMetric(tenant_id=tenant_id, date=date)
            self._db.add(metric)
        metric.completed_count = completed_count
        metric.upcoming_count = upcoming_count
        await self._db.flush()
        return metric

    async def list_appointment_metrics(
        self, *, tenant_id: uuid.UUID, date_from: date_type, date_to: date_type
    ) -> list[AnalyticsAppointmentMetric]:
        result = await self._db.execute(
            select(AnalyticsAppointmentMetric)
            .where(
                AnalyticsAppointmentMetric.tenant_id == tenant_id,
                AnalyticsAppointmentMetric.date >= date_from,
                AnalyticsAppointmentMetric.date <= date_to,
            )
            .order_by(AnalyticsAppointmentMetric.date.asc())
        )
        return list(result.scalars().all())

    async def upsert_ai_metric(
        self,
        *,
        tenant_id: uuid.UUID,
        date: date_type,
        request_count: int,
        cost_amount: float,
        avg_latency_ms: float,
    ) -> AnalyticsAIMetric:
        result = await self._db.execute(
            select(AnalyticsAIMetric).where(
                AnalyticsAIMetric.tenant_id == tenant_id, AnalyticsAIMetric.date == date
            )
        )
        metric = result.scalar_one_or_none()
        if metric is None:
            metric = AnalyticsAIMetric(tenant_id=tenant_id, date=date)
            self._db.add(metric)
        metric.request_count = request_count
        metric.cost_amount = cost_amount
        metric.avg_latency_ms = avg_latency_ms
        await self._db.flush()
        return metric

    async def list_ai_metrics(
        self, *, tenant_id: uuid.UUID, date_from: date_type, date_to: date_type
    ) -> list[AnalyticsAIMetric]:
        result = await self._db.execute(
            select(AnalyticsAIMetric)
            .where(
                AnalyticsAIMetric.tenant_id == tenant_id,
                AnalyticsAIMetric.date >= date_from,
                AnalyticsAIMetric.date <= date_to,
            )
            .order_by(AnalyticsAIMetric.date.asc())
        )
        return list(result.scalars().all())

    async def upsert_user_stat(
        self, *, tenant_id: uuid.UUID, user_id: uuid.UUID, date: date_type, metrics: dict
    ) -> AnalyticsDailyUserStat:
        result = await self._db.execute(
            select(AnalyticsDailyUserStat).where(
                AnalyticsDailyUserStat.tenant_id == tenant_id,
                AnalyticsDailyUserStat.user_id == user_id,
                AnalyticsDailyUserStat.date == date,
            )
        )
        stat = result.scalar_one_or_none()
        if stat is None:
            stat = AnalyticsDailyUserStat(tenant_id=tenant_id, user_id=user_id, date=date)
            self._db.add(stat)
        stat.metrics = metrics
        await self._db.flush()
        return stat
