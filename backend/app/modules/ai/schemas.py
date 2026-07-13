from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AIAnalysisResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_id: UUID
    result_type: str
    result_payload: dict
    prompt_version_id: UUID
    model_config_data: dict | None = Field(default=None, alias="model_config")
    created_at: datetime


class AIAnalysisJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    organization_id: UUID
    requested_by: UUID
    source_type: str
    source_id: UUID
    status: str
    attempts: int
    error_message: str | None
    queued_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    results: list[AIAnalysisResultOut] = []


class AIActionApprovalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    organization_id: UUID
    requested_by: UUID
    decided_by: UUID | None
    analysis_result_id: UUID
    action_type: str
    source_type: str
    source_id: UUID
    status: str
    suggested_payload: dict
    approved_payload: dict | None
    confidence_score: float | None
    expires_at: datetime | None
    decided_at: datetime | None
    created_at: datetime


class AIActionApproveIn(BaseModel):
    approved_payload: dict | None = None
