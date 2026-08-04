import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, ValidationAppError
from app.modules.ai.repository import AIRepository
from app.modules.contacts.repository import ContactRepository
from app.modules.custom_fields.repository import CustomFieldRepository
from app.modules.custom_fields.validation import validate_custom_field_values
from app.modules.deals.models import Deal, DealLineItem
from app.modules.deals.repository import DealLineItemRepository, DealRepository

VALID_STAGES = {"lead", "proposal_sent", "negotiation", "invoiced", "won", "lost"}


class DealService:
    def __init__(self, db: AsyncSession):
        self._db = db
        self._deals = DealRepository(db)
        self._line_items = DealLineItemRepository(db)
        self._ai = AIRepository(db)
        self._contacts = ContactRepository(db)
        self._custom_fields = CustomFieldRepository(db)

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
        custom_fields: dict | None = None,
    ) -> Deal:
        self._validate_stage(stage)
        await self._ensure_contact_exists(
            tenant_id=tenant_id, organization_id=organization_id, contact_id=contact_id
        )
        # Always validate on create (not just when values are provided) so
        # required custom fields are actually enforced for new deals.
        definitions = await self._custom_fields.list_for_entity(
            tenant_id=tenant_id, organization_id=organization_id, entity_type="deal"
        )
        validate_custom_field_values(definitions=definitions, values=custom_fields or {})
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
            custom_fields=custom_fields,
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
        if approval.action_type not in {"deal", "create_deal", "deal/create_deal"}:
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
        custom_fields: dict | None = None,
    ) -> Deal:
        if stage is not None:
            self._validate_stage(stage)
        await self._ensure_contact_exists(
            tenant_id=deal.tenant_id, organization_id=deal.organization_id, contact_id=contact_id
        )
        if custom_fields is not None:
            definitions = await self._custom_fields.list_for_entity(
                tenant_id=deal.tenant_id, organization_id=deal.organization_id, entity_type="deal"
            )
            validate_custom_field_values(definitions=definitions, values=custom_fields)
        return await self._deals.update_deal(
            deal=deal,
            title=title,
            description=description,
            value=value,
            currency=currency,
            stage=stage,
            expected_close_date=expected_close_date,
            contact_id=contact_id,
            custom_fields=custom_fields,
        )

    async def delete_deal(self, *, deal: Deal) -> None:
        await self._deals.soft_delete_deal(deal=deal)

    async def list_line_items(self, *, deal: Deal) -> list[DealLineItem]:
        return await self._line_items.list_for_deal(
            tenant_id=deal.tenant_id, organization_id=deal.organization_id, deal_id=deal.id
        )

    async def add_line_item(
        self,
        *,
        deal: Deal,
        product_name: str,
        quantity: float,
        unit_price: float,
        display_order: int,
    ) -> DealLineItem:
        item = await self._line_items.create(
            tenant_id=deal.tenant_id,
            organization_id=deal.organization_id,
            deal_id=deal.id,
            product_name=product_name,
            quantity=quantity,
            unit_price=unit_price,
            display_order=display_order,
        )
        await self._sync_deal_value(deal=deal)
        return item

    async def update_line_item(
        self,
        *,
        deal: Deal,
        item: DealLineItem,
        product_name: str | None = None,
        quantity: float | None = None,
        unit_price: float | None = None,
        display_order: int | None = None,
    ) -> DealLineItem:
        item = await self._line_items.update(
            item=item,
            product_name=product_name,
            quantity=quantity,
            unit_price=unit_price,
            display_order=display_order,
        )
        await self._sync_deal_value(deal=deal)
        return item

    async def delete_line_item(self, *, deal: Deal, item: DealLineItem) -> None:
        await self._line_items.soft_delete(item=item)
        await self._sync_deal_value(deal=deal)

    async def _sync_deal_value(self, *, deal: Deal) -> None:
        deal.value = await self._line_items.sum_for_deal(
            tenant_id=deal.tenant_id, organization_id=deal.organization_id, deal_id=deal.id
        )
        await self._db.flush()

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
