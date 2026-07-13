from pydantic import BaseModel, Field


class VoiceCommandIn(BaseModel):
    text: str | None = Field(default=None, max_length=20_000)
    audio_base64: str | None = Field(default=None, max_length=2_000_000)
    locale: str = Field(default="tr-TR", max_length=16)


class VoiceTranscriptOut(BaseModel):
    text: str
    language: str
    provider: str
    confidence: float


class VoiceActionOut(BaseModel):
    intent: str
    action_type: str
    confidence: float
    suggested_payload: dict
    requires_approval: bool = True


class VoiceCommandOut(BaseModel):
    transcript: VoiceTranscriptOut
    action: VoiceActionOut
    spoken_response: str
    spoken_response_audio_base64: str | None = None
