import uuid
from datetime import datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.appointments.models import Appointment

ACTIVE_STATUSES = ("confirmed", "rescheduled")


class AppointmentRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def create_appointment(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        title: str,
        start_at: datetime,
        end_at: datetime,
        contact_id: uuid.UUID | None = None,
        description: str | None = None,
        location: str | None = None,
        appointment_timezone: str | None = None,
        source_type: str = "manual",
        source_id: uuid.UUID | None = None,
        external_event_id: str | None = None,
        ai_action_approval_id: uuid.UUID | None = None,
    ) -> Appointment:
        appointment = Appointment(
            tenant_id=tenant_id,
            organization_id=organization_id,
            user_id=user_id,
            contact_id=contact_id,
            title=title,
            description=description,
            location=location,
            start_at=start_at,
            end_at=end_at,
            timezone=appointment_timezone,
            status="confirmed",
            source_type=source_type,
            source_id=source_id,
            external_event_id=external_event_id,
            ai_action_approval_id=ai_action_approval_id,
        )
        self._db.add(appointment)
        await self._db.flush()
        return appointment

    async def get_by_external_event_id(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        external_event_id: str,
    ) -> Appointment | None:
        result = await self._db.execute(
            select(Appointment).where(
                Appointment.tenant_id == tenant_id,
                Appointment.organization_id == organization_id,
                Appointment.external_event_id == external_event_id,
                Appointment.is_deleted.is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def list_appointments(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        status: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        search: str | None = None,
    ) -> list[Appointment]:
        statement = select(Appointment).where(
            Appointment.tenant_id == tenant_id,
            Appointment.organization_id == organization_id,
            Appointment.is_deleted.is_(False),
        )
        if status is not None:
            statement = statement.where(Appointment.status == status)
        if start_date is not None:
            statement = statement.where(Appointment.end_at >= start_date)
        if end_date is not None:
            statement = statement.where(Appointment.start_at <= end_date)
        if search is not None:
            term = f"%{search}%"
            statement = statement.where(
                or_(Appointment.title.ilike(term), Appointment.description.ilike(term))
            )
        result = await self._db.execute(statement.order_by(Appointment.start_at.asc()))
        return list(result.scalars().all())

    async def get_next_by_contact(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        contact_id: uuid.UUID,
        now: datetime | None = None,
    ) -> Appointment | None:
        cutoff = now or datetime.now(timezone.utc)
        result = await self._db.execute(
            select(Appointment)
            .where(
                Appointment.tenant_id == tenant_id,
                Appointment.organization_id == organization_id,
                Appointment.contact_id == contact_id,
                Appointment.is_deleted.is_(False),
                Appointment.status.in_(ACTIVE_STATUSES),
                Appointment.start_at > cutoff,
            )
            .order_by(Appointment.start_at.asc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_appointment(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        appointment_id: uuid.UUID,
    ) -> Appointment | None:
        result = await self._db.execute(
            select(Appointment).where(
                Appointment.tenant_id == tenant_id,
                Appointment.organization_id == organization_id,
                Appointment.id == appointment_id,
                Appointment.is_deleted.is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def get_appointment_by_approval(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        approval_id: uuid.UUID,
    ) -> Appointment | None:
        result = await self._db.execute(
            select(Appointment).where(
                Appointment.tenant_id == tenant_id,
                Appointment.organization_id == organization_id,
                Appointment.ai_action_approval_id == approval_id,
                Appointment.is_deleted.is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def find_overlapping(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        start_at: datetime,
        end_at: datetime,
        exclude_appointment_id: uuid.UUID | None = None,
    ) -> list[Appointment]:
        statement = select(Appointment).where(
            Appointment.tenant_id == tenant_id,
            Appointment.organization_id == organization_id,
            Appointment.user_id == user_id,
            Appointment.is_deleted.is_(False),
            Appointment.status.in_(ACTIVE_STATUSES),
            Appointment.start_at < end_at,
            Appointment.end_at > start_at,
        )
        if exclude_appointment_id is not None:
            statement = statement.where(Appointment.id != exclude_appointment_id)
        result = await self._db.execute(statement.order_by(Appointment.start_at.asc()))
        return list(result.scalars().all())

    async def update_appointment(
        self,
        *,
        appointment: Appointment,
        title: str | None = None,
        description: str | None = None,
        location: str | None = None,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        appointment_timezone: str | None = None,
        status: str | None = None,
        contact_id: uuid.UUID | None = None,
    ) -> Appointment:
        if title is not None:
            appointment.title = title
        if description is not None:
            appointment.description = description
        if location is not None:
            appointment.location = location
        if start_at is not None:
            appointment.start_at = start_at
        if end_at is not None:
            appointment.end_at = end_at
        if appointment_timezone is not None:
            appointment.timezone = appointment_timezone
        if status is not None:
            appointment.status = status
        if contact_id is not None:
            appointment.contact_id = contact_id
        await self._db.flush()
        return appointment

    async def soft_delete_appointment(self, *, appointment: Appointment) -> None:
        appointment.is_deleted = True
        appointment.deleted_at = datetime.now(timezone.utc)
        appointment.status = "cancelled"
        await self._db.flush()
