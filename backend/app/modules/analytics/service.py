import uuid
from datetime import date as date_type
from datetime import datetime, timezone

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai.models import AIAnalysisJob
from app.modules.analytics.models import (
    AnalyticsAIMetric,
    AnalyticsAppointmentMetric,
    AnalyticsCallMetric,
    AnalyticsTaskMetric,
)
from app.modules.analytics.repository import AICostLogRepository, AnalyticsMetricsRepository
from app.modules.appointments.models import Appointment
from app.modules.conversations.models import Call, Conversation
from app.modules.tasks.models import Task


class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self._db = db
        self._metrics = AnalyticsMetricsRepository(db)
        self._cost_logs = AICostLogRepository(db)

    async def aggregate_for_date(
        self, *, tenant_id: uuid.UUID, organization_id: uuid.UUID, date: date_type
    ) -> dict:
        task_counts = await self._aggregate_tasks(tenant_id, organization_id, date)
        call_counts = await self._aggregate_calls(tenant_id, organization_id, date)
        appointment_counts = await self._aggregate_appointments(tenant_id, organization_id, date)
        ai_counts = await self._cost_logs.summarize_for_date(tenant_id=tenant_id, date=date)

        await self._metrics.upsert_task_metric(tenant_id=tenant_id, date=date, **task_counts)
        await self._metrics.upsert_call_metric(tenant_id=tenant_id, date=date, **call_counts)
        await self._metrics.upsert_appointment_metric(
            tenant_id=tenant_id, date=date, **appointment_counts
        )
        await self._metrics.upsert_ai_metric(tenant_id=tenant_id, date=date, **ai_counts)
        await self._aggregate_user_stats(tenant_id, organization_id, date)

        return {
            "date": date,
            "tasks": task_counts,
            "calls": call_counts,
            "appointments": appointment_counts,
            "ai": ai_counts,
        }

    async def get_overview(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        date_from: date_type,
        date_to: date_type,
    ) -> dict:
        task_metrics = await self._metrics.list_task_metrics(
            tenant_id=tenant_id, date_from=date_from, date_to=date_to
        )
        call_metrics = await self._metrics.list_call_metrics(
            tenant_id=tenant_id, date_from=date_from, date_to=date_to
        )
        appointment_metrics = await self._metrics.list_appointment_metrics(
            tenant_id=tenant_id, date_from=date_from, date_to=date_to
        )
        ai_metrics = await self._metrics.list_ai_metrics(
            tenant_id=tenant_id, date_from=date_from, date_to=date_to
        )

        return {
            "date_from": date_from,
            "date_to": date_to,
            "tasks_created": sum(m.created_count for m in task_metrics),
            "tasks_completed": sum(m.completed_count for m in task_metrics),
            "tasks_overdue": max((m.overdue_count for m in task_metrics), default=0),
            "calls_total": sum(m.call_count for m in call_metrics),
            "calls_analyzed": sum(m.analyzed_count for m in call_metrics),
            "appointments_completed": sum(m.completed_count for m in appointment_metrics),
            "appointments_upcoming": max(
                (m.upcoming_count for m in appointment_metrics), default=0
            ),
            "ai_requests": sum(m.request_count for m in ai_metrics),
            "ai_cost_amount": sum(m.cost_amount for m in ai_metrics),
        }

    async def get_task_metrics(
        self, *, tenant_id: uuid.UUID, date_from: date_type, date_to: date_type
    ) -> list[AnalyticsTaskMetric]:
        return await self._metrics.list_task_metrics(
            tenant_id=tenant_id, date_from=date_from, date_to=date_to
        )

    async def get_call_metrics(
        self, *, tenant_id: uuid.UUID, date_from: date_type, date_to: date_type
    ) -> list[AnalyticsCallMetric]:
        return await self._metrics.list_call_metrics(
            tenant_id=tenant_id, date_from=date_from, date_to=date_to
        )

    async def get_appointment_metrics(
        self, *, tenant_id: uuid.UUID, date_from: date_type, date_to: date_type
    ) -> list[AnalyticsAppointmentMetric]:
        return await self._metrics.list_appointment_metrics(
            tenant_id=tenant_id, date_from=date_from, date_to=date_to
        )

    async def get_ai_metrics(
        self, *, tenant_id: uuid.UUID, date_from: date_type, date_to: date_type
    ) -> list[AnalyticsAIMetric]:
        return await self._metrics.list_ai_metrics(
            tenant_id=tenant_id, date_from=date_from, date_to=date_to
        )

    async def _count(self, statement: Select) -> int:
        result = await self._db.execute(statement)
        return result.scalar_one()

    async def _aggregate_tasks(
        self, tenant_id: uuid.UUID, organization_id: uuid.UUID, date: date_type
    ) -> dict:
        now = datetime.now(timezone.utc)
        created_count = await self._count(
            select(func.count(Task.id)).where(
                Task.tenant_id == tenant_id,
                Task.organization_id == organization_id,
                Task.is_deleted.is_(False),
                func.date(Task.created_at) == date,
            )
        )
        completed_count = await self._count(
            select(func.count(Task.id)).where(
                Task.tenant_id == tenant_id,
                Task.organization_id == organization_id,
                Task.is_deleted.is_(False),
                Task.status == "completed",
                func.date(Task.updated_at) == date,
            )
        )
        overdue_count = await self._count(
            select(func.count(Task.id)).where(
                Task.tenant_id == tenant_id,
                Task.organization_id == organization_id,
                Task.is_deleted.is_(False),
                Task.status.in_(("pending", "in_progress")),
                Task.due_at.is_not(None),
                Task.due_at < now,
            )
        )
        return {
            "created_count": created_count,
            "completed_count": completed_count,
            "overdue_count": overdue_count,
        }

    async def _aggregate_calls(
        self, tenant_id: uuid.UUID, organization_id: uuid.UUID, date: date_type
    ) -> dict:
        call_count = await self._count(
            select(func.count(Call.id))
            .join(Conversation, Conversation.id == Call.conversation_id)
            .where(
                Call.tenant_id == tenant_id,
                Conversation.organization_id == organization_id,
                Call.is_deleted.is_(False),
                func.date(Call.created_at) == date,
            )
        )
        analyzed_conversations = (
            select(AIAnalysisJob.source_id)
            .where(
                AIAnalysisJob.tenant_id == tenant_id,
                AIAnalysisJob.organization_id == organization_id,
                AIAnalysisJob.source_type == "conversation",
                AIAnalysisJob.status == "completed",
            )
            .distinct()
        )
        analyzed_count = await self._count(
            select(func.count(Call.id))
            .join(Conversation, Conversation.id == Call.conversation_id)
            .where(
                Call.tenant_id == tenant_id,
                Conversation.organization_id == organization_id,
                Call.is_deleted.is_(False),
                func.date(Call.created_at) == date,
                Conversation.id.in_(analyzed_conversations),
            )
        )
        return {"call_count": call_count, "analyzed_count": analyzed_count}

    async def _aggregate_appointments(
        self, tenant_id: uuid.UUID, organization_id: uuid.UUID, date: date_type
    ) -> dict:
        now = datetime.now(timezone.utc)
        completed_count = await self._count(
            select(func.count(Appointment.id)).where(
                Appointment.tenant_id == tenant_id,
                Appointment.organization_id == organization_id,
                Appointment.is_deleted.is_(False),
                Appointment.status == "completed",
                func.date(Appointment.updated_at) == date,
            )
        )
        upcoming_count = await self._count(
            select(func.count(Appointment.id)).where(
                Appointment.tenant_id == tenant_id,
                Appointment.organization_id == organization_id,
                Appointment.is_deleted.is_(False),
                Appointment.status == "confirmed",
                Appointment.start_at > now,
            )
        )
        return {"completed_count": completed_count, "upcoming_count": upcoming_count}

    async def _aggregate_user_stats(
        self, tenant_id: uuid.UUID, organization_id: uuid.UUID, date: date_type
    ) -> None:
        task_result = await self._db.execute(
            select(Task.user_id, func.count(Task.id))
            .where(
                Task.tenant_id == tenant_id,
                Task.organization_id == organization_id,
                Task.is_deleted.is_(False),
                Task.status == "completed",
                func.date(Task.updated_at) == date,
            )
            .group_by(Task.user_id)
        )
        tasks_completed_by_user = {user_id: count for user_id, count in task_result.all()}

        appointment_result = await self._db.execute(
            select(Appointment.user_id, func.count(Appointment.id))
            .where(
                Appointment.tenant_id == tenant_id,
                Appointment.organization_id == organization_id,
                Appointment.is_deleted.is_(False),
                Appointment.status == "completed",
                func.date(Appointment.updated_at) == date,
            )
            .group_by(Appointment.user_id)
        )
        appointments_completed_by_user = {
            user_id: count for user_id, count in appointment_result.all()
        }

        ai_stats_by_user = await self._cost_logs.summarize_per_user_for_date(
            tenant_id=tenant_id, date=date
        )

        user_ids = (
            set(tasks_completed_by_user)
            | set(appointments_completed_by_user)
            | set(ai_stats_by_user)
        )
        for user_id in user_ids:
            ai_stats = ai_stats_by_user.get(user_id, {"ai_requests": 0, "ai_cost_amount": 0.0})
            metrics = {
                "tasks_completed": tasks_completed_by_user.get(user_id, 0),
                "appointments_completed": appointments_completed_by_user.get(user_id, 0),
                "ai_requests": ai_stats["ai_requests"],
                "ai_cost_amount": ai_stats["ai_cost_amount"],
            }
            await self._metrics.upsert_user_stat(
                tenant_id=tenant_id, user_id=user_id, date=date, metrics=metrics
            )
