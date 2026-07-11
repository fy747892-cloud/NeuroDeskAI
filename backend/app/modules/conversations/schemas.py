from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ConversationParticipantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    display_name: str
    participant_type: str


class CallTranscriptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    call_id: UUID
    language: str | None
    status: str
    transcript_text: str
    created_at: datetime


class CallOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID
    call_direction: str | None
    phone_number: str | None
    started_at: datetime | None
    duration_seconds: int | None
    status: str
    created_at: datetime
    transcriptions: list[CallTranscriptionOut] = []


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    organization_id: UUID
    user_id: UUID
    source_type: str
    title: str
    status: str
    created_at: datetime


class ConversationDetailOut(ConversationOut):
    participants: list[ConversationParticipantOut] = []
    calls: list[CallOut] = []


class ConversationCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    source_type: str = Field(default="manual", min_length=1, max_length=50)
    participant_names: list[str] = Field(default_factory=list, max_length=20)


class ConversationUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    status: str | None = Field(default=None, min_length=1, max_length=50)


class ConversationParticipantCreate(BaseModel):
    display_name: str = Field(min_length=1, max_length=255)
    participant_type: str = Field(default="manual", min_length=1, max_length=50)
    participant_id: UUID | None = None


class CallTextCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    transcript_text: str = Field(min_length=1, max_length=200_000)
    participant_names: list[str] = Field(default_factory=list, max_length=20)
    call_direction: str | None = Field(default=None, max_length=50)
    phone_number: str | None = Field(default=None, max_length=64)
    started_at: datetime | None = None
    duration_seconds: int | None = Field(default=None, ge=0)
    language: str | None = Field(default=None, max_length=20)


class CallTextOut(BaseModel):
    conversation: ConversationOut
    call: CallOut
    transcription: CallTranscriptionOut


class CallUpdate(BaseModel):
    call_direction: str | None = Field(default=None, max_length=50)
    phone_number: str | None = Field(default=None, max_length=64)
    started_at: datetime | None = None
    duration_seconds: int | None = Field(default=None, ge=0)
    status: str | None = Field(default=None, max_length=50)
