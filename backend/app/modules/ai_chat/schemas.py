from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ChatSourceOut(BaseModel):
    source_type: str
    source_id: UUID
    title: str
    snippet: str


class ChatMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: UUID
    role: str
    content: str
    confidence: float | None
    sources: list[ChatSourceOut] | None
    created_at: datetime


class ChatSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    organization_id: UUID
    user_id: UUID
    title: str | None
    status: str
    created_at: datetime


class ChatSessionDetailOut(ChatSessionOut):
    messages: list[ChatMessageOut] = []


class ChatMessageRequest(BaseModel):
    session_id: UUID | None = None
    message: str = Field(min_length=1, max_length=4_000)


class ChatSessionUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
