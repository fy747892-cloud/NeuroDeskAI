from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PriorityFactor(BaseModel):
    key: str
    label: str
    weight: int


class PrioritizedItemOut(BaseModel):
    item_type: str
    item_id: UUID
    title: str
    status: str
    score: int = Field(ge=0, le=100)
    priority: str
    due_at: datetime | None = None
    contact_id: UUID | None = None
    factors: list[PriorityFactor]


class PriorityQueueOut(BaseModel):
    generated_at: datetime
    items: list[PrioritizedItemOut]
