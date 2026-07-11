import base64
from dataclasses import dataclass

from app.core.errors import ValidationAppError


@dataclass(frozen=True)
class VoiceTranscript:
    text: str
    language: str
    provider: str
    confidence: float


class VoiceProvider:
    async def transcribe(
        self, *, text: str | None, audio_base64: str | None, locale: str
    ) -> VoiceTranscript:
        raise NotImplementedError

    async def synthesize(self, *, text: str, locale: str) -> str:
        raise NotImplementedError


class MockVoiceProvider(VoiceProvider):
    async def transcribe(
        self, *, text: str | None, audio_base64: str | None, locale: str
    ) -> VoiceTranscript:
        transcript_text = text
        if transcript_text is None and audio_base64 is not None:
            try:
                transcript_text = base64.b64decode(audio_base64).decode("utf-8")
            except (ValueError, UnicodeDecodeError) as exc:
                raise ValidationAppError(
                    "Mock voice audio must be base64 encoded UTF-8 text."
                ) from exc

        if transcript_text is None or not transcript_text.strip():
            raise ValidationAppError("Voice command requires text or audio_base64.")

        return VoiceTranscript(
            text=transcript_text.strip(),
            language=locale,
            provider="mock",
            confidence=0.86,
        )

    async def synthesize(self, *, text: str, locale: str) -> str:
        return text
