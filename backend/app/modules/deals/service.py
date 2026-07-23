import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, ValidationAppError
from app.modules.ai.repository import AIRepository
from app.modules.contacts.repository import ContactRepository
from app.modules.deals.models import Deal
from app.modules.deals.repository import DealRepository

VALID_STAGES = {"lead", "proposal_sent", "negotiation", "invoiced", "won", "lost"}


class DealService:
    def __init__(self, db: AsyncSession):
        self._db = db
        self._deals = DealRepository(db)
        self._ai = AIRepository(db)
        self._contacts = ContactRepository(db)

    async def create_manual_deal(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        owner_user_id: uuid.UUID,
        title: str,
        description: str | None = None,
        value: float | None = None,
        currency: str = "TRY",
        stage: str = "lead",
        expected_close_date: datetime | None = None,
        contact_id: uuid.UUID | None = None,
    ) -> Deal:
        self._validate_stage(stage)
        await self._ensure_contact_exists(
            tenant_id=tenant_id, organization_id=organization_id, contact_id=contact_id
        )
        return await self._deals.create_deal(
            tenant_id=tenant_id,
            organization_id=organization_id,
            owner_user_id=owner_user_id,
            title=title,
            description=description,
            value=value,
            currency=currency,
            stage=stage,
            expected_close_date=expected_close_date,
            contact_id=contact_id,
            source_type="manual",
        )

    async def create_deal_from_approval(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        owner_user_id: uuid.UUID,
        approval_id: uuid.UUID,
    ) -> Deal:
        approval = await self._ai.get_action_approval(
            tenant_id=tenant_id, organization_id=organization_id, approval_id=approval_id
        )
        if approval is None:
            raise NotFoundError("AI action approval not found.")
        if approval.action_type not in {"deal", "create_deal"}:
            raise ValidationAppError("Only deal approvals can create deals.")
        if approval.status != "approved":
            raise ValidationAppError("Only approved AI deal suggestions can create deals.")

        existing_deal = await self._deals.get_deal_by_approval(
            tenant_id=tenant_id, organization_id=organization_id, approval_id=approval.id
        )
        if existing_deal is not None:
            return existing_deal

        payload = approval.approved_payload or approval.suggested_payload
        title = payload.get("title")
        if not title:
            raise ValidationAppError("Approved deal payload must include a title.")

        stage = payload.get("stage") or "lead"
        if stage not in VALID_STAGES:
            stage = "lead"
        contact_id = payload.get("contact_id")
        await self._ensure_contact_exists(
            tenant_id=tenant_id, organization_id=organization_id, contact_id=contact_id
        )

        return await self._deals.create_deal(
            tenant_id=tenant_id,
            organization_id=organization_id,
            owner_user_id=owner_user_id,
            title=title,
            description=payload.get("description"),
            value=self._parse_value(payload.get("value")),
            stage=stage,
            contact_id=contact_id,
            source_type="ai_action_approval",
            source_id=approval.source_id,
            ai_action_approval_id=approval.id,
        )

    async def update_deal(
        self,
        *,
        deal: Deal,
        title: str | None = None,
        description: str | None = None,
        value: float | None = None,
        currency: str | None = None,
        stage: str | None = None,
        expected_close_date: datetime | None = None,
        contact_id: uuid.UUID | None = None,
    ) -> Deal:
        if stage is not None:
            self._validate_stage(stage)
        await self._ensure_contact_exists(
            tenant_id=deal.tenant_id, organization_id=deal.organization_id, contact_id=contact_id
        )
        return await self._deals.update_deal(
            deal=deal,
            title=title,
            description=description,
            value=value,
            currency=currency,
            stage=stage,
            expected_close_date=expected_close_date,
            contact_id=contact_id,
        )

    async def delete_deal(self, *, deal: Deal) -> None:
        await self._deals.soft_delete_deal(deal=deal)

    def _validate_stage(self, stage: str) -> None:
        if stage not in VALID_STAGES:
            raise ValidationAppError("Deal stage is not supported.")

    def _parse_value(self, value) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    async def _ensure_contact_exists(self, *, tenant_id, organization_id, contact_id) -> None:
        if contact_id is None:
            return
        if isinstance(contact_id, str):
            try:
                contact_id = uuid.UUID(contact_id)
            except ValueError as exc:
                raise ValidationAppError("contact_id must be a valid UUID.") from exc
        contact = await self._contacts.get_by_id(
            tenant_id=tenant_id, organization_id=organization_id, contact_id=contact_id
        )
        if contact is None:
            raise NotFoundError("Contact not found.")
