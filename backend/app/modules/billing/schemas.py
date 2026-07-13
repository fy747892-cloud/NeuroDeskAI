from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    price: float
    billing_period: str
    status: str


class SubscriptionOut(BaseModel):
    tenant_id: UUID
    status: str
    current_period_end: datetime
    plan: PlanOut


class PlanSwitchIn(BaseModel):
    plan_code: str = Field(min_length=1, max_length=50)


class UsageSummaryOut(BaseModel):
    quota_type: str
    period: str
    limit_value: int
    used: int
    remaining: int
