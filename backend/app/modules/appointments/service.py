import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, NotFoundError, ValidationAppError
from app.modules.ai.repository import AIRepository
from app.modules.appointments.models import Appointment
from app.modules.appointments.repository import AppointmentRepository
from app.modules.contacts.repository import ContactRepository

DEFAULT_DURATION = timedelta(minutes=30)


class AppointmentService:
    VALID_STATUSES = {"confirmed", "cancelled", "completed", "rescheduled"}

    def __init__(self, db: AsyncSession):
        self._db = db
        self._appointments = AppointmentRepository(db)
        self._ai = AIRepository(db)
        self._contacts = ContactRepository(db)

    async def create_manual_appointment(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        title: str,
        start_at: datetime,
        end_at: datetime,
        description: str | None = None,
        location: str | None = None,
        appointment_timezone: str | None = None,
        contact_id: uuid.UUID | None = None,
        force: bool = False,
    ) -> Appointment:
        await self._ensure_contact_exists(
            tenant_id=tenant_id,
            organization_id=organization_id,
            contact_id=contact_id,
        )
        if not force:
            await self._ensure_no_conflicts(
                tenant_id=tenant_id,
                organization_id=organization_id,
                user_id=user_id,
                start_at=start_at,
                end_at=end_at,
            )
        return await self._appointments.create_appointment(
            tenant_id=tenant_id,
            organization_id=organization_id,
            user_id=user_id,
            title=title,
            start_at=start_at,
            end_at=end_at,
            contact_id=contact_id,
            description=description,
            location=location,
            appointment_timezone=appointment_timezone,
            source_type="manual",
        )

    async def create_appointment_from_approval(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        approval_id: uuid.UUID,
        force: bool = False,
    ) -> Appointment:
        approval = await self._ai.get_action_approval(
            tenant_id=tenant_id,
            organization_id=organization_id,
            approval_id=approval_id,
        )
        if approval is None:
            raise NotFoundError("AI action approval not found.")
        if approval.action_type not in {"appointment", "create_appointment", "appointment/create_appointment"}:
            raise ValidationAppError("Only appointment approvals can create appointments.")
        if approval.status != "approved":
            raise ValidationAppError("Only approved AI appointment suggestions can create appointments.")

        existing = await self._appointments.get_appointment_by_approval(
            tenant_id=tenant_id,
            organization_id=organization_id,
            approval_id=approval.id,
        )
        if existing is not None:
            return existing

        payload = approval.approved_payload or approval.suggested_payload
        title = payload.get("title")
        if not title:
            raise ValidationAppError("Approved appointment payload must include a title.")

        start_at = self._parse_datetime(payload.get("proposed_datetime"))
        if start_at is None:
            raise ValidationAppError("Approved appointment payload must include proposed_datetime.")
        end_at = self._parse_datetime(payload.get("end_datetime")) or (start_at + DEFAULT_DURATION)
        contact_id = payload.get("contact_id")
        await self._ensure_contact_exists(
            tenant_id=tenant_id,
            organization_id=organization_id,
            contact_id=contact_id,
        )

        if not force:
            await self._ensure_no_conflicts(
                tenant_id=tenant_id,
                organization_id=organization_id,
                user_id=user_id,
                start_at=start_at,
                end_at=end_at,
            )

        return await self._appointments.create_appointment(
            tenant_id=tenant_id,
            organization_id=organization_id,
            user_id=user_id,
            title=title,
            start_at=start_at,
            end_at=end_at,
            contact_id=contact_id,
            description=payload.get("description"),
            location=payload.get("location"),
            source_type="ai_action_approval",
            source_id=approval.source_id,
            ai_action_approval_id=approval.id,
        )

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
        force: bool = False,
    ) -> Appointment:
        if status is not None:
            self._validate_status(status)
        await self._ensure_contact_exists(
            tenant_id=appointment.tenant_id,
            organization_id=appointment.organization_id,
            contact_id=contact_id,
        )

        if start_at is not None or end_at is not None:
            new_start = start_at or appointment.start_at
            new_end = end_at or appointment.end_at
            if new_end <= new_start:
                raise ValidationAppError("end_at must be after start_at.")
            if not force:
                await self._ensure_no_conflicts(
                    tenant_id=appointment.tenant_id,
                    organization_id=appointment.organization_id,
                    user_id=appointment.user_id,
                    start_at=new_start,
                    end_at=new_end,
                    exclude_appointment_id=appointment.id,
                )

        return await self._appointments.update_appointment(
            appointment=appointment,
            title=title,
            description=description,
            location=location,
            start_at=start_at,
            end_at=end_at,
            appointment_timezone=appointment_timezone,
            status=status,
            contact_id=contact_id,
        )

    async def cancel_appointment(self, *, appointment: Appointment) -> Appointment:
        return await self._appointments.update_appointment(appointment=appointment, status="cancelled")

    async def check_conflicts(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        start_at: datetime,
        end_at: datetime,
        exclude_appointment_id: uuid.UUID | None = None,
    ) -> list[Appointment]:
        return await self._appointments.find_overlapping(
            tenant_id=tenant_id,
            organization_id=organization_id,
            user_id=user_id,
            start_at=start_at,
            end_at=end_at,
            exclude_appointment_id=exclude_appointment_id,
        )

    async def _ensure_no_conflicts(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        start_at: datetime,
        end_at: datetime,
        exclude_appointment_id: uuid.UUID | None = None,
    ) -> None:
        conflicts = await self.check_conflicts(
            tenant_id=tenant_id,
            organization_id=organization_id,
            user_id=user_id,
            start_at=start_at,
            end_at=end_at,
            exclude_appointment_id=exclude_appointment_id,
        )
        if conflicts:
            raise ConflictError(
                "This time range overlaps with an existing appointment. Pass force=true to override."
            )

    def _validate_status(self, status: str) -> None:
        if status not in self.VALID_STATUSES:
            raise ValidationAppError("Appointment status is not supported.")

    async def _ensure_contact_exists(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        contact_id: uuid.UUID | str | None,
    ) -> None:
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

    def _parse_datetime(self, value) -> datetime | None:
        if value is None or isinstance(value, datetime):
            return value
        if isinstance(value, str):
            normalized = value.replace("Z", "+00:00")
            try:
                parsed = datetime.fromisoformat(normalized)
            except ValueError as exc:
                raise ValidationAppError("Approved appointment datetime must be ISO 8601.") from exc
            return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)
        raise ValidationAppError("Approved appointment datetime must be ISO 8601.")
