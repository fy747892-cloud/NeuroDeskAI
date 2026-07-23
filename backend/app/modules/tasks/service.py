import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, ValidationAppError
from app.modules.ai.repository import AIRepository
from app.modules.contacts.repository import ContactRepository
from app.modules.tasks.models import Task
from app.modules.tasks.repository import TaskRepository


class TaskService:
    VALID_STATUSES = {"pending", "in_progress", "completed", "cancelled", "overdue"}
    VALID_PRIORITIES = {"low", "medium", "high"}

    def __init__(self, db: AsyncSession):
        self._db = db
        self._tasks = TaskRepository(db)
        self._ai = AIRepository(db)
        self._contacts = ContactRepository(db)

    async def create_manual_task(
        self,
        *,
        tenant_id,
        organization_id,
        user_id,
        title: str,
        description: str | None = None,
        priority: str = "medium",
        due_at: datetime | None = None,
        contact_id=None,
    ) -> Task:
        self._validate_priority(priority)
        await self._ensure_contact_exists(
            tenant_id=tenant_id,
            organization_id=organization_id,
            contact_id=contact_id,
        )
        return await self._tasks.create_task(
            tenant_id=tenant_id,
            organization_id=organization_id,
            user_id=user_id,
            title=title,
            description=description,
            priority=priority,
            due_at=due_at,
            contact_id=contact_id,
            source_type="manual",
        )

    async def create_task_from_approval(
        self,
        *,
        tenant_id,
        organization_id,
        user_id,
        approval_id,
    ) -> Task:
        approval = await self._ai.get_action_approval(
            tenant_id=tenant_id,
            organization_id=organization_id,
            approval_id=approval_id,
        )
        if approval is None:
            raise NotFoundError("AI action approval not found.")
        if approval.action_type not in {"task", "create_task", "task/create_task"}:
            raise ValidationAppError("Only task approvals can create tasks.")
        if approval.status != "approved":
            raise ValidationAppError("Only approved AI task suggestions can create tasks.")

        existing_task = await self._tasks.get_task_by_approval(
            tenant_id=tenant_id,
            organization_id=organization_id,
            approval_id=approval.id,
        )
        if existing_task is not None:
            return existing_task

        payload = approval.approved_payload or approval.suggested_payload
        title = payload.get("title")
        if not title:
            raise ValidationAppError("Approved task payload must include a title.")

        priority = payload.get("priority", "medium")
        self._validate_priority(priority)
        contact_id = payload.get("contact_id")
        await self._ensure_contact_exists(
            tenant_id=tenant_id,
            organization_id=organization_id,
            contact_id=contact_id,
        )
        return await self._tasks.create_task(
            tenant_id=tenant_id,
            organization_id=organization_id,
            user_id=user_id,
            title=title,
            description=payload.get("description"),
            priority=priority,
            due_at=self._parse_due_at(payload.get("due_at") or payload.get("due_date")),
            contact_id=contact_id,
            source_type="ai_action_approval",
            source_id=approval.source_id,
            ai_action_approval_id=approval.id,
        )

    async def update_task(
        self,
        *,
        task: Task,
        title: str | None = None,
        description: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        due_at: datetime | None = None,
        contact_id=None,
    ) -> Task:
        if status is not None:
            self._validate_status(status)
        if priority is not None:
            self._validate_priority(priority)
        await self._ensure_contact_exists(
            tenant_id=task.tenant_id,
            organization_id=task.organization_id,
            contact_id=contact_id,
        )
        return await self._tasks.update_task(
            task=task,
            title=title,
            description=description,
            status=status,
            priority=priority,
            due_at=due_at,
            contact_id=contact_id,
        )

    async def complete_task(self, *, task: Task) -> Task:
        return await self._tasks.update_task(task=task, status="completed")

    def _validate_status(self, status: str) -> None:
        if status not in self.VALID_STATUSES:
            raise ValidationAppError("Task status is not supported.")

    def _validate_priority(self, priority: str) -> None:
        if priority not in self.VALID_PRIORITIES:
            raise ValidationAppError("Task priority is not supported.")

    async def _ensure_contact_exists(self, *, tenant_id, organization_id, contact_id) -> None:
        if contact_id is None:
            return
        if isinstance(contact_id, str):
            try:
                contact_id = uuid.UUID(contact_id)
            except ValueError as exc:
                raise ValidationAppError("contact_id must be a valid UUID.") from exc
        contact = await self._contacts.get_by_id(
            tenant_id=tenant_id,
            organization_id=organization_id,
            contact_id=contact_id,
        )
        if contact is None:
            raise NotFoundError("Contact not found.")

    def _parse_due_at(self, value) -> datetime | None:
        if value is None or isinstance(value, datetime):
            return value
        if isinstance(value, str):
            normalized = value.replace("Z", "+00:00")
            try:
                return datetime.fromisoformat(normalized)
            except ValueError as exc:
                raise ValidationAppError("Approved task due date must be ISO 8601.") from exc
        raise ValidationAppError("Approved task due date must be ISO 8601.")
