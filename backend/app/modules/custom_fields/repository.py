import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.custom_fields.models import CustomFieldDefinition

ENTITY_TYPES = ("contact", "deal")
FIELD_TYPES = ("text", "number", "date", "boolean", "select")


class CustomFieldRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def create(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        entity_type: str,
        field_key: str,
        label: str,
        field_type: str,
        options: list[str] | None,
        is_required: bool,
        display_order: int,
    ) -> CustomFieldDefinition:
        definition = CustomFieldDefinition(
            tenant_id=tenant_id,
            organization_id=organization_id,
            entity_type=entity_type,
            field_key=field_key,
            label=label,
            field_type=field_type,
            options=options,
            is_required=is_required,
            display_order=display_order,
        )
        self._db.add(definition)
        await self._db.flush()
        return definition

    async def list_for_entity(
        self, *, tenant_id: uuid.UUID, organization_id: uuid.UUID, entity_type: str
    ) -> list[CustomFieldDefinition]:
        result = await self._db.execute(
            select(CustomFieldDefinition)
            .where(
                CustomFieldDefinition.tenant_id == tenant_id,
                CustomFieldDefinition.organization_id == organization_id,
                CustomFieldDefinition.entity_type == entity_type,
                CustomFieldDefinition.is_deleted.is_(False),
            )
            .order_by(CustomFieldDefinition.display_order.asc(), CustomFieldDefinition.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_by_id(
        self, *, tenant_id: uuid.UUID, organization_id: uuid.UUID, definition_id: uuid.UUID
    ) -> CustomFieldDefinition | None:
        result = await self._db.execute(
            select(CustomFieldDefinition).where(
                CustomFieldDefinition.tenant_id == tenant_id,
                CustomFieldDefinition.organization_id == organization_id,
                CustomFieldDefinition.id == definition_id,
                CustomFieldDefinition.is_deleted.is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def update(
        self,
        *,
        definition: CustomFieldDefinition,
        label: str | None = None,
        options: list[str] | None = None,
        is_required: bool | None = None,
        display_order: int | None = None,
    ) -> CustomFieldDefinition:
        if label is not None:
            definition.label = label
        if options is not None:
            definition.options = options
        if is_required is not None:
            definition.is_required = is_required
        if display_order is not None:
            definition.display_order = display_order
        await self._db.flush()
        return definition

    async def soft_delete(self, *, definition: CustomFieldDefinition) -> None:
        definition.is_deleted = True
        definition.deleted_at = datetime.now(timezone.utc)
        await self._db.flush()
