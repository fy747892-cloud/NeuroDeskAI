import time
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai.repository import AIRepository
from app.modules.analytics.repository import AICostLogRepository
from app.modules.appointments.repository import AppointmentRepository
from app.modules.billing.service import BillingService
from app.modules.conversations.repository import ConversationRepository
from app.modules.dashboard.provider import get_digest_narrative_provider
from app.modules.dashboard.schemas import DashboardOut, DashboardSummaryOut, DigestOut
from app.modules.deals.repository import DealRepository
from app.modules.email.repository import EmailMessageRepository
from app.modules.tasks.repository import TaskRepository

UPCOMING_APPOINTMENTS_WINDOW = timedelta(days=7)
RECENT_CONVERSATIONS_LIMIT = 5

DAILY_UNREPLIED_WINDOW = timedelta(days=3)
WEEKLY_UNREPLIED_WINDOW = timedelta(days=7)
WEEKLY_WINDOW = timedelta(days=7)


class DashboardService:
    def __init__(self, db: AsyncSession):
        self._tasks = TaskRepository(db)
        self._appointments = AppointmentRepository(db)
        self._conversations = ConversationRepository(db)
        self._ai = AIRepository(db)
        self._email_messages = EmailMessageRepository(db)
        self._deals = DealRepository(db)
        self._cost_logs = AICostLogRepository(db)
        self._billing = BillingService(db)
        self._narrative_provider = get_digest_narrative_provider()

    async def build(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
    ) -> DashboardOut:
        now = datetime.now(timezone.utc)

        open_tasks = await self._tasks.list_open_tasks(
            tenant_id=tenant_id, organization_id=organization_id
        )
        overdue_tasks = await self._tasks.list_overdue_tasks(
            tenant_id=tenant_id, organization_id=organization_id, now=now
        )
        upcoming_appointments = await self._appointments.list_appointments(
            tenant_id=tenant_id,
            organization_id=organization_id,
            status="confirmed",
            start_date=now,
            end_date=now + UPCOMING_APPOINTMENTS_WINDOW,
        )
        recent_conversations = await self._conversations.list_conversations(
            tenant_id=tenant_id,
            organization_id=organization_id,
            limit=RECENT_CONVERSATIONS_LIMIT,
        )
        pending_ai_approvals = await self._ai.list_action_approvals(
            tenant_id=tenant_id,
            organization_id=organization_id,
            status="pending",
        )

        return DashboardOut(
            summary=DashboardSummaryOut(
                open_tasks_count=len(open_tasks),
                overdue_tasks_count=len(overdue_tasks),
                upcoming_appointments_count=len(upcoming_appointments),
                pending_ai_approvals_count=len(pending_ai_approvals),
            ),
            open_tasks=list(open_tasks),
            overdue_tasks=list(overdue_tasks),
            upcoming_appointments=list(upcoming_appointments),
            recent_conversations=list(recent_conversations),
            pending_ai_approvals=list(pending_ai_approvals),
            generated_at=now,
        )

    async def build_digest(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        period: str,
    ) -> DigestOut:
        now = datetime.now(timezone.utc)

        if period == "weekly":
            appointments_start, appointments_end = now, now + WEEKLY_WINDOW
            calls_start, calls_end = now - WEEKLY_WINDOW, now
            unreplied_since = now - WEEKLY_UNREPLIED_WINDOW
            period_label = "Bu hafta"
        else:
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            appointments_start, appointments_end = today_start, today_start + timedelta(days=1)
            calls_start, calls_end = today_start - timedelta(days=1), today_start
            unreplied_since = now - DAILY_UNREPLIED_WINDOW
            period_label = "Bugün"

        appointments = await self._appointments.list_appointments(
            tenant_id=tenant_id,
            organization_id=organization_id,
            status="confirmed",
            start_date=appointments_start,
            end_date=appointments_end,
        )
        appointments_count = len(appointments)

        calls_count = await self._conversations.count_calls_between(
            tenant_id=tenant_id,
            organization_id=organization_id,
            start=calls_start,
            end=calls_end,
        )

        overdue_tasks = await self._tasks.list_overdue_tasks(
            tenant_id=tenant_id, organization_id=organization_id, now=now
        )
        contacts_awaiting_reply_count = len(
            {task.contact_id for task in overdue_tasks if task.contact_id is not None}
        )

        unanswered_emails_count = await self._email_messages.count_unreplied_since(
            tenant_id=tenant_id, organization_id=organization_id, since=unreplied_since
        )

        open_deals_count = await self._deals.count_open(
            tenant_id=tenant_id, organization_id=organization_id
        )

        await self._billing.enforce_ai_usage_guard(tenant_id=tenant_id)

        start_time = time.monotonic()
        narrative = await self._narrative_provider.narrate(
            period=period,
            appointments_count=appointments_count,
            calls_count=calls_count,
            contacts_awaiting_reply_count=contacts_awaiting_reply_count,
            unanswered_emails_count=unanswered_emails_count,
        )
        latency_ms = int((time.monotonic() - start_time) * 1000)

        await self._cost_logs.record(
            tenant_id=tenant_id,
            user_id=user_id,
            provider=self._narrative_provider.provider_name,
            model=self._narrative_provider.model_name,
            source_type=f"{period}_digest",
            input_tokens=10,
            output_tokens=max(1, len(narrative) // 4),
            latency_ms=latency_ms,
        )
        await self._billing.record_ai_usage(tenant_id=tenant_id, user_id=user_id)

        return DigestOut(
            period=period,
            period_label=period_label,
            appointments_count=appointments_count,
            calls_count=calls_count,
            contacts_awaiting_reply_count=contacts_awaiting_reply_count,
            unanswered_emails_count=unanswered_emails_count,
            open_deals_count=open_deals_count,
            narrative=narrative,
            generated_at=now,
        )