import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import require_permission
from app.core.errors import NotFoundError
from app.core.permissions import Permission
from app.db.session import get_db
from app.modules.audit.repository import AuditRepository
from app.modules.custom_fields.models import CustomFieldDefinition
from app.modules.custom_fields.schemas import (
    CustomFieldDefinitionCreate,
    CustomFieldDefinitionOut,
    CustomFieldDefinitionUpdate,
)
from app.modules.custom_fields.service import CustomFieldService
from app.modules.users.models import User

router = APIRouter(prefix="/custom-fields", tags=["custom-fields"])


@router.get("", response_model=list[CustomFieldDefinitionOut])
async def list_custom_fields(
    entity_type: str = Query(...),
    current_user: User = Depends(require_permission(Permission.ORGANIZATIONS_READ)),
    db: AsyncSession = Depends(get_db),
) -> list[CustomFieldDefinition]:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")
    return await CustomFieldService(db).list_for_entity(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        entity_type=entity_type,
    )


@router.post("", response_model=CustomFieldDefinitionOut, status_code=201)
async def create_custom_field(
    body: CustomFieldDefinitionCreate,
    request: Request,
    current_user: User = Depends(require_permission(Permission.ORGANIZATIONS_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> CustomFieldDefinition:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")
    definition = await CustomFieldService(db).create_definition(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        entity_type=body.entity_type,
        field_key=body.field_key,
        label=body.label,
        field_type=body.field_type,
        options=body.options,
        is_required=body.is_required,
        display_order=body.display_order,
    )
    await AuditRepository(db).record(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action="custom_field.created",
        entity_type="custom_field_definition",
        entity_id=definition.id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata={"entity_type": body.entity_type, "field_key": body.field_key},
    )
    await db.commit()
    return definition


@router.patch("/{definition_id}", response_model=CustomFieldDefinitionOut)
async def update_custom_field(
    definition_id: uuid.UUID,
    body: CustomFieldDefinitionUpdate,
    request: Request,
    current_user: User = Depends(require_permission(Permission.ORGANIZATIONS_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> CustomFieldDefinition:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")
    definition = await CustomFieldService(db).update_definition(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        definition_id=definition_id,
        label=body.label,
        options=body.options,
        is_required=body.is_required,
        display_order=body.display_order,
    )
    await AuditRepository(db).record(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action="custom_field.updated",
        entity_type="custom_field_definition",
        entity_id=definition.id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    return definition


@router.delete("/{definition_id}", status_code=204)
async def delete_custom_field(
    definition_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_permission(Permission.ORGANIZATIONS_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> None:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")
    await CustomFieldService(db).delete_definition(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        definition_id=definition_id,
    )
    await AuditRepository(db).record(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action="custom_field.deleted",
        entity_type="custom_field_definition",
        entity_id=definition_id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
