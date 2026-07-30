import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import require_permission
from app.core.errors import NotFoundError
from app.core.permissions import Permission
from app.db.session import get_db
from app.modules.appointments.models import Appointment
from app.modules.appointments.repository import AppointmentRepository
from app.modules.appointments.schemas import (
    AppointmentCreate,
    AppointmentCreateFromApproval,
    AppointmentOut,
    AppointmentUpdate,
    ConflictCheckOut,
    ConflictCheckRequest,
)
from app.modules.appointments.service import AppointmentService
from app.modules.audit.repository import AuditRepository
from app.modules.notifications.models import Notification
from app.modules.notifications.schemas import NotificationOut, ReminderCreate
from app.modules.notifications.service import NotificationService
from app.modules.users.models import User

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.get("", response_model=list[AppointmentOut])
async def list_appointments(
    status_filter: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    current_user: User = Depends(require_permission(Permission.APPOINTMENTS_READ)),
    db: AsyncSession = Depends(get_db),
) -> list[Appointment]:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")
    return await AppointmentRepository(db).list_appointments(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        status=status_filter,
        start_date=start_date,
        end_date=end_date,
    )


@router.post("", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    body: AppointmentCreate,
    request: Request,
    current_user: User = Depends(require_permission(Permission.APPOINTMENTS_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> Appointment:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    appointment = await AppointmentService(db).create_manual_appointment(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        title=body.title,
        start_at=body.start_at,
        end_at=body.end_at,
        description=body.description,
        location=body.location,
        appointment_timezone=body.timezone,
        contact_id=body.contact_id,
        force=body.force,
    )
    await _record_appointment_audit(db, request, current_user, "appointment.created", appointment)
    await db.commit()
    return appointment


@router.post("/check-conflicts", response_model=ConflictCheckOut)
async def check_conflicts(
    body: ConflictCheckRequest,
    current_user: User = Depends(require_permission(Permission.APPOINTMENTS_READ)),
    db: AsyncSession = Depends(get_db),
) -> ConflictCheckOut:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    conflicts = await AppointmentService(db).check_conflicts(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        start_at=body.start_at,
        end_at=body.end_at,
        exclude_appointment_id=body.exclude_appointment_id,
    )
    return ConflictCheckOut(has_conflicts=bool(conflicts), conflicts=list(conflicts))


@router.post("/from-approval", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
async def create_appointment_from_approval(
    body: AppointmentCreateFromApproval,
    request: Request,
    current_user: User = Depends(require_permission(Permission.APPOINTMENTS_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> Appointment:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    appointment = await AppointmentService(db).create_appointment_from_approval(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        approval_id=body.approval_id,
        force=body.force,
    )
    await _record_appointment_audit(
        db, request, current_user, "appointment.created_from_ai_approval", appointment
    )
    await db.commit()
    return appointment


@router.get("/{appointment_id}", response_model=AppointmentOut)
async def get_appointment(
    appointment_id: uuid.UUID,
    current_user: User = Depends(require_permission(Permission.APPOINTMENTS_READ)),
    db: AsyncSession = Depends(get_db),
) -> Appointment:
    return await _get_current_appointment(db, current_user, appointment_id)


@router.patch("/{appointment_id}", response_model=AppointmentOut)
async def update_appointment(
    appointment_id: uuid.UUID,
    body: AppointmentUpdate,
    request: Request,
    current_user: User = Depends(require_permission(Permission.APPOINTMENTS_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> Appointment:
    appointment = await _get_current_appointment(db, current_user, appointment_id)
    appointment = await AppointmentService(db).update_appointment(
        appointment=appointment,
        title=body.title,
        description=body.description,
        location=body.location,
        start_at=body.start_at,
        end_at=body.end_at,
        appointment_timezone=body.timezone,
        status=body.status,
        contact_id=body.contact_id,
        force=body.force,
    )
    await _record_appointment_audit(db, request, current_user, "appointment.updated", appointment)
    await db.commit()
    return appointment


@router.post("/{appointment_id}/cancel", response_model=AppointmentOut)
async def cancel_appointment(
    appointment_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_permission(Permission.APPOINTMENTS_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> Appointment:
    appointment = await _get_current_appointment(db, current_user, appointment_id)
    appointment = await AppointmentService(db).cancel_appointment(appointment=appointment)
    await _record_appointment_audit(db, request, current_user, "appointment.cancelled", appointment)
    await db.commit()
    return appointment


@router.post(
    "/{appointment_id}/reminders",
    response_model=NotificationOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_appointment_reminder(
    appointment_id: uuid.UUID,
    body: ReminderCreate,
    request: Request,
    current_user: User = Depends(require_permission(Permission.APPOINTMENTS_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> Notification:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")
    appointment = await _get_current_appointment(db, current_user, appointment_id)

    reminder = await NotificationService(db).create_reminder(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        source_type="appointment",
        source_id=appointment.id,
        notification_type="appointment_reminder",
        title=f"Reminder: {appointment.title}",
        body=appointment.description or appointment.title,
        due_at=appointment.start_at,
        offset_minutes=body.offset_minutes,
        remind_at=body.remind_at,
        channel=body.channel,
    )
    await _record_appointment_audit(db, request, current_user, "reminder.created", appointment)
    await db.commit()
    return reminder


@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_appointment(
    appointment_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_permission(Permission.APPOINTMENTS_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> None:
    appointment = await _get_current_appointment(db, current_user, appointment_id)
    await AppointmentRepository(db).soft_delete_appointment(appointment=appointment)
    await _record_appointment_audit(db, request, current_user, "appointment.deleted", appointment)
    await db.commit()


async def _get_current_appointment(
    db: AsyncSession, current_user: User, appointment_id: uuid.UUID
) -> Appointment:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")
    appointment = await AppointmentRepository(db).get_appointment(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        appointment_id=appointment_id,
    )
    if appointment is None:
        raise NotFoundError("Appointment not found.")
    return appointment


async def _record_appointment_audit(
    db: AsyncSession,
    request: Request,
    current_user: User,
    action: str,
    appointment: Appointment,
) -> None:
    await AuditRepository(db).record(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action=action,
        entity_type="appointment",
        entity_id=appointment.id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
