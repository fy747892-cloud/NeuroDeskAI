import uuid
from datetime import timedelta

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import require_permission
from app.core.errors import NotFoundError
from app.core.permissions import Permission
from app.db.session import get_db
from app.modules.audit.repository import AuditRepository
from app.modules.notifications.models import Notification
from app.modules.notifications.schemas import NotificationOut, ReminderCreate
from app.modules.notifications.service import NotificationService
from app.modules.tasks.models import Task
from app.modules.tasks.repository import TaskRepository
from app.modules.tasks.schemas import TaskCreate, TaskCreateFromApproval, TaskOut, TaskUpdate
from app.modules.tasks.service import TaskService
from app.modules.users.models import User

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskOut])
async def list_tasks(
    status_filter: str | None = None,
    current_user: User = Depends(require_permission(Permission.TASKS_READ)),
    db: AsyncSession = Depends(get_db),
) -> list[Task]:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")
    return await TaskRepository(db).list_tasks(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        status=status_filter,
    )


@router.get("/overdue", response_model=list[TaskOut])
async def list_overdue_tasks(
    current_user: User = Depends(require_permission(Permission.TASKS_READ)),
    db: AsyncSession = Depends(get_db),
) -> list[Task]:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")
    return await TaskRepository(db).list_overdue_tasks(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
    )


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
async def create_task(
    body: TaskCreate,
    request: Request,
    current_user: User = Depends(require_permission(Permission.TASKS_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> Task:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    task = await TaskService(db).create_manual_task(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        title=body.title,
        description=body.description,
        priority=body.priority,
        due_at=body.due_at,
        contact_id=body.contact_id,
    )
    await _record_task_audit(db, request, current_user, "task.created", task)

    if body.repeat_count and body.due_at is not None:
        interval = timedelta(days=body.repeat_interval_days)
        for occurrence in range(1, body.repeat_count):
            recurring_task = await TaskService(db).create_manual_task(
                tenant_id=current_user.tenant_id,
                organization_id=current_user.organization_id,
                user_id=current_user.id,
                title=body.title,
                description=body.description,
                priority=body.priority,
                due_at=body.due_at + interval * occurrence,
                contact_id=body.contact_id,
            )
            await _record_task_audit(db, request, current_user, "task.created", recurring_task)

    await db.commit()
    return task


@router.post("/from-approval", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
async def create_task_from_approval(
    body: TaskCreateFromApproval,
    request: Request,
    current_user: User = Depends(require_permission(Permission.TASKS_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> Task:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    task = await TaskService(db).create_task_from_approval(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        approval_id=body.approval_id,
    )
    await _record_task_audit(db, request, current_user, "task.created_from_ai_approval", task)
    await db.commit()
    return task


@router.get("/{task_id}", response_model=TaskOut)
async def get_task(
    task_id: uuid.UUID,
    current_user: User = Depends(require_permission(Permission.TASKS_READ)),
    db: AsyncSession = Depends(get_db),
) -> Task:
    task = await _get_current_task(db, current_user, task_id)
    return task


@router.patch("/{task_id}", response_model=TaskOut)
async def update_task(
    task_id: uuid.UUID,
    body: TaskUpdate,
    request: Request,
    current_user: User = Depends(require_permission(Permission.TASKS_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> Task:
    task = await _get_current_task(db, current_user, task_id)
    task = await TaskService(db).update_task(
        task=task,
        title=body.title,
        description=body.description,
        status=body.status,
        priority=body.priority,
        due_at=body.due_at,
        contact_id=body.contact_id,
    )
    await _record_task_audit(db, request, current_user, "task.updated", task)
    await db.commit()
    return task


@router.post("/{task_id}/complete", response_model=TaskOut)
async def complete_task(
    task_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_permission(Permission.TASKS_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> Task:
    task = await _get_current_task(db, current_user, task_id)
    task = await TaskService(db).complete_task(task=task)
    await _record_task_audit(db, request, current_user, "task.completed", task)
    await db.commit()
    return task


@router.post(
    "/{task_id}/reminders", response_model=NotificationOut, status_code=status.HTTP_201_CREATED
)
async def create_task_reminder(
    task_id: uuid.UUID,
    body: ReminderCreate,
    request: Request,
    current_user: User = Depends(require_permission(Permission.TASKS_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> Notification:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")
    task = await _get_current_task(db, current_user, task_id)

    reminder = await NotificationService(db).create_reminder(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        source_type="task",
        source_id=task.id,
        notification_type="task_reminder",
        title=f"Reminder: {task.title}",
        body=task.description or task.title,
        due_at=task.due_at,
        offset_minutes=body.offset_minutes,
        remind_at=body.remind_at,
        channel=body.channel,
    )
    await AuditRepository(db).record(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action="reminder.created",
        entity_type="task",
        entity_id=task.id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    return reminder


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_permission(Permission.TASKS_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> None:
    task = await _get_current_task(db, current_user, task_id)
    await TaskRepository(db).soft_delete_task(task=task)
    await _record_task_audit(db, request, current_user, "task.deleted", task)
    await db.commit()


async def _get_current_task(db: AsyncSession, current_user: User, task_id: uuid.UUID) -> Task:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")
    task = await TaskRepository(db).get_task(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        task_id=task_id,
    )
    if task is None:
        raise NotFoundError("Task not found.")
    return task


async def _record_task_audit(
    db: AsyncSession,
    request: Request,
    current_user: User,
    action: str,
    task: Task,
) -> None:
    await AuditRepository(db).record(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action=action,
        entity_type="task",
        entity_id=task.id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
