import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai.repository import AIRepository
from app.modules.appointments.repository import AppointmentRepository
from app.modules.conversations.repository import ConversationRepository
from app.modules.dashboard.schemas import DashboardOut, DashboardSummaryOut
from app.modules.tasks.repository import TaskRepository

UPCOMING_APPOINTMENTS_WINDOW = timedelta(days=7)
RECENT_CONVERSATIONS_LIMIT = 5


class DashboardService:
    def __init__(self, db: AsyncSession):
        self._tasks = TaskRepository(db)
        self._appointments = AppointmentRepository(db)
        self._conversations = ConversationRepository(db)
        self._ai = AIRepository(db)

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
