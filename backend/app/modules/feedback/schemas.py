from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FeedbackCreate(BaseModel):
    category: Literal["bug", "idea", "other"]
    message: str = Field(min_length=1, max_length=4000)
    page_url: str | None = Field(default=None, max_length=2000)


class FeedbackOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    category: str
    message: str
    page_url: str | None
    created_at: datetime
