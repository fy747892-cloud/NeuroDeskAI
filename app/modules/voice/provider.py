import base64
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import settings
from app.core.errors import ValidationAppError
from app.core.llm_retry import with_retry


@dataclass(frozen=True)
class VoiceTranscript:
    text: str
    language: str
    provider: str
    confidence: float


class VoiceProvider:
    provider_name = "unset"
    stt_model_name = "unset"
    tts_model_name = "unset"

    async def transcribe(
        self, *, text: str | None, audio_base64: str | None, locale: str
    ) -> VoiceTranscript:
        raise NotImplementedError

    async def synthesize(self, *, text: str, locale: str) -> str:
        raise NotImplementedError

    async def synthesize_audio(self, *, text: str, locale: str) -> str | None:
        raise NotImplementedError


class MockVoiceProvider(VoiceProvider):
    provider_name = "mock"
    stt_model_name = "mock-stt-v1"
    tts_model_name = "mock-tts-v1"

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

    async def synthesize_audio(self, *, text: str, locale: str) -> str | None:
        return None


class OpenAIVoiceProvider(VoiceProvider):
    """Real STT/TTS via OpenAI-compatible /audio endpoints — same LLM_BASE_URL/
    LLM_API_KEY convention as ai/provider.py, ai_chat/provider.py, etc.

    Clients are expected to send audio_base64 as a WAV file (fixed format,
    no content-sniffing of arbitrary codecs — an intentional MVP constraint)."""

    provider_name = "openai"

    def __init__(self) -> None:
        self.stt_model_name = settings.llm_stt_model
        self.tts_model_name = settings.llm_tts_model
        self._tts_voice = settings.llm_tts_voice
        self._base_url = settings.llm_base_url.rstrip("/")
        self._api_key = settings.llm_api_key
        self._timeout = settings.llm_timeout_seconds

    async def transcribe(
        self, *, text: str | None, audio_base64: str | None, locale: str
    ) -> VoiceTranscript:
        if text is not None and text.strip():
            return VoiceTranscript(
                text=text.strip(), language=locale, provider=self.provider_name, confidence=1.0
            )

        if audio_base64 is None:
            raise ValidationAppError("Voice command requires text or audio_base64.")
        if not self._api_key:
            raise RuntimeError("LLM_API_KEY is required when LLM_PROVIDER is openai.")

        try:
            audio_bytes = base64.b64decode(audio_base64)
        except ValueError as exc:
            raise ValidationAppError("audio_base64 must be valid base64.") from exc

        response = await with_retry(lambda: self._post_transcription(audio_bytes))
        transcript_text = str(response.get("text", "")).strip()
        if not transcript_text:
            raise ValidationAppError("Voice command requires text or audio_base64.")

        return VoiceTranscript(
            text=transcript_text,
            language=str(response.get("language") or locale),
            provider=self.provider_name,
            confidence=0.9,
        )

    async def synthesize(self, *, text: str, locale: str) -> str:
        return text

    async def synthesize_audio(self, *, text: str, locale: str) -> str | None:
        if not self._api_key:
            raise RuntimeError("LLM_API_KEY is required when LLM_PROVIDER is openai.")

        payload = {"model": self.tts_model_name, "voice": self._tts_voice, "input": text}
        audio_bytes = await with_retry(lambda: self._post_speech(payload))
        return base64.b64encode(audio_bytes).decode("ascii")

    async def _post_transcription(self, audio_bytes: bytes) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self._api_key}"}
        data = {"model": self.stt_model_name, "response_format": "verbose_json"}
        files = {"file": ("audio.wav", audio_bytes, "audio/wav")}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._base_url}/audio/transcriptions",
                headers=headers,
                data=data,
                files=files,
            )
        response.raise_for_status()
        return response.json()

    async def _post_speech(self, payload: dict[str, Any]) -> bytes:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._base_url}/audio/speech",
                headers=headers,
                json=payload,
            )
        response.raise_for_status()
        return response.content


def get_voice_provider() -> VoiceProvider:
    provider = settings.llm_provider.lower()
    if provider in {"mock", "local"}:
        return MockVoiceProvider()
    if provider in {"openai", "openai-compatible"}:
        return OpenAIVoiceProvider()
    raise RuntimeError(f"Unsupported LLM provider: {settings.llm_provider}")