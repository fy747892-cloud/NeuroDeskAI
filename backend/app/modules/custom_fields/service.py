import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, NotFoundError, ValidationAppError
from app.modules.custom_fields.models import CustomFieldDefinition
from app.modules.custom_fields.repository import CustomFieldRepository


class CustomFieldService:
    def __init__(self, db: AsyncSession):
        self._definitions = CustomFieldRepository(db)

    async def list_for_entity(
        self, *, tenant_id: uuid.UUID, organization_id: uuid.UUID, entity_type: str
    ) -> list[CustomFieldDefinition]:
        return await self._definitions.list_for_entity(
            tenant_id=tenant_id, organization_id=organization_id, entity_type=entity_type
        )

    async def create_definition(
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
        if field_type == "select" and not options:
            raise ValidationAppError("Select fields require at least one option.")

        existing = await self._definitions.list_for_entity(
            tenant_id=tenant_id, organization_id=organization_id, entity_type=entity_type
        )
        if any(definition.field_key == field_key for definition in existing):
            raise ConflictError(f"A custom field with key '{field_key}' already exists.")

        return await self._definitions.create(
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

    async def update_definition(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        definition_id: uuid.UUID,
        label: str | None,
        options: list[str] | None,
        is_required: bool | None,
        display_order: int | None,
    ) -> CustomFieldDefinition:
        definition = await self._definitions.get_by_id(
            tenant_id=tenant_id, organization_id=organization_id, definition_id=definition_id
        )
        if definition is None:
            raise NotFoundError("Custom field definition not found.")
        if definition.field_type == "select" and options is not None and not options:
            raise ValidationAppError("Select fields require at least one option.")
        return await self._definitions.update(
            definition=definition,
            label=label,
            options=options,
            is_required=is_required,
            display_order=display_order,
        )

    async def delete_definition(
        self, *, tenant_id: uuid.UUID, organization_id: uuid.UUID, definition_id: uuid.UUID
    ) -> None:
        definition = await self._definitions.get_by_id(
            tenant_id=tenant_id, organization_id=organization_id, definition_id=definition_id
        )
        if definition is None:
            raise NotFoundError("Custom field definition not found.")
        await self._definitions.soft_delete(definition=definition)
