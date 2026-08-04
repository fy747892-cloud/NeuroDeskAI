from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field


class DealOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    organization_id: UUID
    owner_user_id: UUID
    contact_id: UUID | None
    title: str
    description: str | None
    value: float | None
    currency: str
    stage: str
    expected_close_date: datetime | None
    source_type: str
    source_id: UUID | None
    ai_action_approval_id: UUID | None
    custom_fields: dict[str, Any]
    created_at: datetime


class DealCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=20_000)
    value: float | None = Field(default=None, ge=0)
    currency: str = Field(default="TRY", min_length=1, max_length=10)
    stage: str = Field(default="lead", min_length=1, max_length=50)
    expected_close_date: datetime | None = None
    contact_id: UUID | None = None
    custom_fields: dict[str, Any] | None = None


class DealUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=20_000)
    value: float | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=1, max_length=10)
    stage: str | None = Field(default=None, min_length=1, max_length=50)
    expected_close_date: datetime | None = None
    contact_id: UUID | None = None
    custom_fields: dict[str, Any] | None = None


class DealCreateFromApproval(BaseModel):
    approval_id: UUID


class DealStageBreakdownOut(BaseModel):
    stage: str
    currency: str
    total_value: float
    deal_count: int


class DealForecastMonthOut(BaseModel):
    month: str
    currency: str
    total_value: float
    deal_count: int


class DealPipelineReportOut(BaseModel):
    by_stage: list[DealStageBreakdownOut]
    by_expected_month: list[DealForecastMonthOut]
    open_stages: list[str]
    generated_at: datetime


class DealLineItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    deal_id: UUID
    product_name: str
    quantity: float
    unit_price: float
    display_order: int
    created_at: datetime

    @computed_field  # type: ignore[prop-decorator]
    @property
    def line_total(self) -> float:
        return self.quantity * self.unit_price


class DealLineItemCreate(BaseModel):
    product_name: str = Field(min_length=1, max_length=255)
    quantity: float = Field(default=1, gt=0)
    unit_price: float = Field(default=0, ge=0)
    display_order: int = Field(default=0)


class DealLineItemUpdate(BaseModel):
    product_name: str | None = Field(default=None, min_length=1, max_length=255)
    quantity: float | None = Field(default=None, gt=0)
    unit_price: float | None = Field(default=None, ge=0)
    display_order: int | None = None