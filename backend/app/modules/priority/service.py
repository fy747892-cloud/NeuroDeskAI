import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.appointments.models import Appointment
from app.modules.appointments.repository import AppointmentRepository
from app.modules.priority.schemas import PriorityFactor, PrioritizedItemOut, PriorityQueueOut
from app.modules.tasks.models import Task
from app.modules.tasks.repository import TaskRepository

URGENT_TERMS = (
    "urgent",
    "asap",
    "critical",
    "blocked",
    "deadline",
    "acil",
    "hemen",
    "kritik",
    "bugun",
    "bugün",
)


class PriorityService:
    TASK_PRIORITY_WEIGHTS = {"high": 30, "medium": 15, "low": 5}
    STATUS_WEIGHTS = {"pending": 8, "in_progress": 12, "confirmed": 6, "rescheduled": 4}

    def __init__(self, db: AsyncSession):
        self._tasks = TaskRepository(db)
        self._appointments = AppointmentRepository(db)

    async def build_queue(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        now: datetime | None = None,
        limit: int = 25,
    ) -> PriorityQueueOut:
        generated_at = now or datetime.now(timezone.utc)
        tasks = await self._tasks.list_open_tasks(
            tenant_id=tenant_id,
            organization_id=organization_id,
        )
        appointments = await self._appointments.list_appointments(
            tenant_id=tenant_id,
            organization_id=organization_id,
            status=None,
            start_date=generated_at,
            end_date=generated_at + timedelta(days=14),
        )

        items = [
            self._score_task(task, now=generated_at)
            for task in tasks
        ] + [
            self._score_appointment(appointment, now=generated_at)
            for appointment in appointments
            if appointment.status in {"confirmed", "rescheduled"}
        ]
        max_datetime = datetime.max.replace(tzinfo=timezone.utc)
        items.sort(key=lambda item: (-item.score, item.due_at or max_datetime))
        return PriorityQueueOut(generated_at=generated_at, items=items[:limit])

    def _score_task(self, task: Task, *, now: datetime) -> PrioritizedItemOut:
        factors: list[PriorityFactor] = []
        self._add_factor(
            factors,
            "explicit_priority",
            f"Task priority is {task.priority}.",
            self.TASK_PRIORITY_WEIGHTS.get(task.priority, 10),
        )
        self._add_factor(
            factors,
            "status",
            f"Task status is {task.status}.",
            self.STATUS_WEIGHTS.get(task.status, 0),
        )
        self._add_due_factor(factors, due_at=task.due_at, now=now, label="Task due date")
        self._add_contact_factor(factors, contact_id=task.contact_id)
        self._add_urgency_terms(factors, text=f"{task.title} {task.description or ''}")
        score = self._normalize_score(factors)
        return PrioritizedItemOut(
            item_type="task",
            item_id=task.id,
            title=task.title,
            status=task.status,
            score=score,
            priority=self._score_to_priority(score),
            due_at=task.due_at,
            contact_id=task.contact_id,
            factors=factors,
        )

    def _score_appointment(self, appointment: Appointment, *, now: datetime) -> PrioritizedItemOut:
        factors: list[PriorityFactor] = []
        self._add_factor(
            factors,
            "status",
            f"Appointment status is {appointment.status}.",
            self.STATUS_WEIGHTS.get(appointment.status, 0),
        )
        self._add_due_factor(
            factors,
            due_at=appointment.start_at,
            now=now,
            label="Appointment start time",
        )
        self._add_contact_factor(factors, contact_id=appointment.contact_id)
        self._add_urgency_terms(
            factors,
            text=(
                f"{appointment.title} "
                f"{appointment.description or ''} "
                f"{appointment.location or ''}"
            ),
        )
        score = self._normalize_score(factors)
        return PrioritizedItemOut(
            item_type="appointment",
            item_id=appointment.id,
            title=appointment.title,
            status=appointment.status,
            score=score,
            priority=self._score_to_priority(score),
            due_at=appointment.start_at,
            contact_id=appointment.contact_id,
            factors=factors,
        )

    def _add_due_factor(
        self,
        factors: list[PriorityFactor],
        *,
        due_at: datetime | None,
        now: datetime,
        label: str,
    ) -> None:
        if due_at is None:
            return
        delta = due_at - now
        if delta.total_seconds() < 0:
            self._add_factor(factors, "overdue", f"{label} has passed.", 35)
        elif delta <= timedelta(hours=24):
            self._add_factor(factors, "due_soon", f"{label} is within 24 hours.", 28)
        elif delta <= timedelta(days=3):
            self._add_factor(factors, "upcoming", f"{label} is within 3 days.", 18)
        elif delta <= timedelta(days=7):
            self._add_factor(factors, "planned", f"{label} is within 7 days.", 10)

    def _add_contact_factor(
        self, factors: list[PriorityFactor], *, contact_id: uuid.UUID | None
    ) -> None:
        if contact_id is not None:
            self._add_factor(factors, "contact_linked", "Linked to customer memory.", 8)

    def _add_urgency_terms(self, factors: list[PriorityFactor], *, text: str) -> None:
        normalized = text.casefold()
        if any(term in normalized for term in URGENT_TERMS):
            self._add_factor(factors, "urgent_language", "Urgent language detected.", 14)

    def _add_factor(
        self, factors: list[PriorityFactor], key: str, label: str, weight: int
    ) -> None:
        if weight > 0:
            factors.append(PriorityFactor(key=key, label=label, weight=weight))

    def _normalize_score(self, factors: list[PriorityFactor]) -> int:
        return min(100, sum(factor.weight for factor in factors))

    def _score_to_priority(self, score: int) -> str:
        if score >= 70:
            return "urgent"
        if score >= 45:
            return "high"
        if score >= 25:
            return "medium"
        return "low"
