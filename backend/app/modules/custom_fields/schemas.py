from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CustomFieldDefinitionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    organization_id: UUID
    entity_type: str
    field_key: str
    label: str
    field_type: str
    options: list[str] | None
    is_required: bool
    display_order: int


class CustomFieldDefinitionCreate(BaseModel):
    entity_type: Literal["contact", "deal"]
    field_key: str = Field(min_length=1, max_length=100, pattern=r"^[a-z][a-z0-9_]*$")
    label: str = Field(min_length=1, max_length=255)
    field_type: Literal["text", "number", "date", "boolean", "select"]
    options: list[str] | None = None
    is_required: bool = False
    display_order: int = 0


class CustomFieldDefinitionUpdate(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=255)
    options: list[str] | None = None
    is_required: bool | None = None
    display_order: int | None = None
