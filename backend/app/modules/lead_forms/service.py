import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, ValidationAppError
from app.modules.contacts.repository import ContactRepository
from app.modules.deals.repository import DealRepository
from app.modules.lead_forms.models import LeadForm
from app.modules.lead_forms.repository import LeadFormRepository


class LeadFormService:
    def __init__(self, db: AsyncSession):
        self._db = db
        self._lead_forms = LeadFormRepository(db)
        self._contacts = ContactRepository(db)
        self._deals = DealRepository(db)

    async def create_for_organization(
        self, *, tenant_id: uuid.UUID, organization_id: uuid.UUID, owner_user_id: uuid.UUID
    ) -> LeadForm:
        existing = await self._lead_forms.get_by_organization(
            tenant_id=tenant_id, organization_id=organization_id
        )
        if existing is not None:
            raise ConflictError("This organization already has a lead form.")
        return await self._lead_forms.create(
            tenant_id=tenant_id, organization_id=organization_id, owner_user_id=owner_user_id
        )

    async def set_active(self, *, lead_form: LeadForm, is_active: bool) -> LeadForm:
        return await self._lead_forms.update_active(lead_form=lead_form, is_active=is_active)

    async def rotate_token(self, *, lead_form: LeadForm) -> LeadForm:
        return await self._lead_forms.rotate_token(lead_form=lead_form)

    async def submit_lead(
        self,
        *,
        lead_form: LeadForm,
        full_name: str,
        email: str | None,
        phone: str | None,
        company: str | None,
        message: str | None,
        website: str | None,
    ) -> None:
        # Honeypot: real visitors never see/fill this field. Silently succeed
        # so bots get no signal that they were caught.
        if website:
            return

        if not full_name.strip():
            raise ValidationAppError("full_name is required.")
        if not email and not phone:
            raise ValidationAppError("Either email or phone is required.")

        existing_contact = None
        if email:
            existing_contact = await self._contacts.get_by_email(
                tenant_id=lead_form.tenant_id, organization_id=lead_form.organization_id, email=email
            )

        if existing_contact is not None:
            contact = existing_contact
        else:
            # Public form submissions don't collect org-defined custom fields,
            # so we write through the repository directly (custom_fields={})
            # rather than ContactService.create_contact, which would enforce
            # any org-required custom field and break every submission.
            contact = await self._contacts.create(
                tenant_id=lead_form.tenant_id,
                organization_id=lead_form.organization_id,
                owner_user_id=lead_form.owner_user_id,
                full_name=full_name.strip(),
                email=email,
                phone=phone,
                company=company,
            )

        await self._contacts.add_timeline_event(
            tenant_id=lead_form.tenant_id,
            contact_id=contact.id,
            event_type="lead_captured",
            source_type="web_form",
            source_id=lead_form.id,
            event_metadata={"message": message} if message else None,
        )
        if message:
            await self._contacts.add_note(
                tenant_id=lead_form.tenant_id,
                contact_id=contact.id,
                user_id=lead_form.owner_user_id,
                note_text=message,
            )

        # Same reasoning as above: bypass DealService.create_manual_deal's
        # custom-field validation for this auto-created lead deal.
        await self._deals.create_deal(
            tenant_id=lead_form.tenant_id,
            organization_id=lead_form.organization_id,
            owner_user_id=lead_form.owner_user_id,
            contact_id=contact.id,
            title=f"{full_name.strip()} - Web Formu",
            description=message,
            stage="lead",
            source_type="web_form",
            source_id=lead_form.id,
        )
