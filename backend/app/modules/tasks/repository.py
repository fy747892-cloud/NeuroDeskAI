import uuid
from datetime import datetime, timezone

from sqlalchemy import func, nulls_last, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.tasks.models import Task


class TaskRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def create_task(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        title: str,
        description: str | None = None,
        priority: str = "medium",
        due_at: datetime | None = None,
        contact_id: uuid.UUID | None = None,
        source_type: str = "manual",
        source_id: uuid.UUID | None = None,
        ai_action_approval_id: uuid.UUID | None = None,
    ) -> Task:
        task = Task(
            tenant_id=tenant_id,
            organization_id=organization_id,
            user_id=user_id,
            contact_id=contact_id,
            title=title,
            description=description,
            status="pending",
            priority=priority,
            due_at=due_at,
            source_type=source_type,
            source_id=source_id,
            ai_action_approval_id=ai_action_approval_id,
        )
        self._db.add(task)
        await self._db.flush()
        return task

    async def list_tasks(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        status: str | None = None,
        search: str | None = None,
    ) -> list[Task]:
        statement = select(Task).where(
            Task.tenant_id == tenant_id,
            Task.organization_id == organization_id,
            Task.is_deleted.is_(False),
        )
        if status is not None:
            statement = statement.where(Task.status == status)
        if search is not None:
            term = f"%{search}%"
            statement = statement.where(
                or_(Task.title.ilike(term), Task.description.ilike(term))
            )
        result = await self._db.execute(statement.order_by(Task.created_at.desc()))
        return list(result.scalars().all())

    async def list_open_tasks(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
    ) -> list[Task]:
        result = await self._db.execute(
            select(Task)
            .where(
                Task.tenant_id == tenant_id,
                Task.organization_id == organization_id,
                Task.is_deleted.is_(False),
                Task.status.in_(("pending", "in_progress")),
            )
            .order_by(nulls_last(Task.due_at.asc()))
        )
        return list(result.scalars().all())

    async def list_overdue_tasks(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        now: datetime | None = None,
    ) -> list[Task]:
        cutoff = now or datetime.now(timezone.utc)
        result = await self._db.execute(
            select(Task)
            .where(
                Task.tenant_id == tenant_id,
                Task.organization_id == organization_id,
                Task.is_deleted.is_(False),
                Task.status.in_(("pending", "in_progress")),
                Task.due_at.is_not(None),
                Task.due_at < cutoff,
            )
            .order_by(Task.due_at.asc())
        )
        return list(result.scalars().all())

    async def count_open_by_contact(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        contact_id: uuid.UUID,
    ) -> int:
        result = await self._db.execute(
            select(func.count(Task.id)).where(
                Task.tenant_id == tenant_id,
                Task.organization_id == organization_id,
                Task.contact_id == contact_id,
                Task.is_deleted.is_(False),
                Task.status.in_(("pending", "in_progress")),
            )
        )
        return result.scalar_one()

    async def get_task(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        task_id: uuid.UUID,
    ) -> Task | None:
        result = await self._db.execute(
            select(Task).where(
                Task.tenant_id == tenant_id,
                Task.organization_id == organization_id,
                Task.id == task_id,
                Task.is_deleted.is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def get_task_by_approval(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        approval_id: uuid.UUID,
    ) -> Task | None:
        result = await self._db.execute(
            select(Task).where(
                Task.tenant_id == tenant_id,
                Task.organization_id == organization_id,
                Task.ai_action_approval_id == approval_id,
                Task.is_deleted.is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def update_task(
        self,
        *,
        task: Task,
        title: str | None = None,
        description: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        due_at: datetime | None = None,
        contact_id: uuid.UUID | None = None,
    ) -> Task:
        if title is not None:
            task.title = title
        if description is not None:
            task.description = description
        if status is not None:
            task.status = status
        if priority is not None:
            task.priority = priority
        if due_at is not None:
            task.due_at = due_at
        if contact_id is not None:
            task.contact_id = contact_id
        await self._db.flush()
        return task

    async def soft_delete_task(self, *, task: Task) -> None:
        task.is_deleted = True
        task.deleted_at = datetime.now(timezone.utc)
        task.status = "cancelled"
        await self._db.flush()
