from datetime import datetime

from pydantic import BaseModel

from app.modules.ai.schemas import AIActionApprovalOut
from app.modules.appointments.schemas import AppointmentOut
from app.modules.conversations.schemas import ConversationOut
from app.modules.tasks.schemas import TaskOut


class DashboardSummaryOut(BaseModel):
    open_tasks_count: int
    overdue_tasks_count: int
    upcoming_appointments_count: int
    pending_ai_approvals_count: int


class DashboardOut(BaseModel):
    summary: DashboardSummaryOut
    open_tasks: list[TaskOut]
    overdue_tasks: list[TaskOut]
    upcoming_appointments: list[AppointmentOut]
    recent_conversations: list[ConversationOut]
    pending_ai_approvals: list[AIActionApprovalOut]
    generated_at: datetime


class DigestOut(BaseModel):
    period: str
    period_label: str
    appointments_count: int
    calls_count: int
    contacts_awaiting_reply_count: int
    unanswered_emails_count: int
    open_deals_count: int
    narrative: str
    generated_at: datetime
