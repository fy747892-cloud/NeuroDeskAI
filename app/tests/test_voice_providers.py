import base64
from unittest.mock import AsyncMock, patch

import pytest

from app.core.config import settings
from app.modules.voice.provider import MockVoiceProvider, OpenAIVoiceProvider


def _openai_settings():
    return patch.multiple(settings, llm_provider="openai", llm_api_key="test-key")


async def test_transcribe_maps_successful_response():
    with _openai_settings():
        provider = OpenAIVoiceProvider()
        audio_base64 = base64.b64encode(b"fake wav bytes").decode()
        response = {"text": "Yarın acil görev ekle", "language": "tr"}
        with patch.object(
            OpenAIVoiceProvider, "_post_transcription", new=AsyncMock(return_value=response)
        ) as mocked:
            transcript = await provider.transcribe(
                text=None, audio_base64=audio_base64, locale="tr-TR"
            )

    mocked.assert_called_once()
    assert transcript.text == "Yarın acil görev ekle"
    assert transcript.language == "tr"
    assert transcript.provider == "openai"


async def test_transcribe_skips_stt_call_when_text_is_given():
    with _openai_settings():
        provider = OpenAIVoiceProvider()
        with patch.object(
            OpenAIVoiceProvider, "_post_transcription", new=AsyncMock()
        ) as mocked:
            transcript = await provider.transcribe(
                text="Bugün toplantı planla", audio_base64=None, locale="tr-TR"
            )

    mocked.assert_not_called()
    assert transcript.text == "Bugün toplantı planla"


async def test_transcribe_retries_then_raises_on_persistent_failure():
    with _openai_settings():
        provider = OpenAIVoiceProvider()
        audio_base64 = base64.b64encode(b"fake wav bytes").decode()
        with patch.object(
            OpenAIVoiceProvider,
            "_post_transcription",
            new=AsyncMock(side_effect=RuntimeError("network error")),
        ) as mocked:
            with pytest.raises(RuntimeError, match="network error"):
                await provider.transcribe(text=None, audio_base64=audio_base64, locale="tr-TR")

    assert mocked.call_count == 2


async def test_synthesize_audio_encodes_response_bytes_as_base64():
    with _openai_settings():
        provider = OpenAIVoiceProvider()
        with patch.object(
            OpenAIVoiceProvider, "_post_speech", new=AsyncMock(return_value=b"fake-mp3-bytes")
        ) as mocked:
            audio_base64 = await provider.synthesize_audio(text="hazir", locale="tr-TR")

    mocked.assert_called_once()
    assert audio_base64 == base64.b64encode(b"fake-mp3-bytes").decode("ascii")


async def test_synthesize_audio_retries_then_raises_on_persistent_failure():
    with _openai_settings():
        provider = OpenAIVoiceProvider()
        with patch.object(
            OpenAIVoiceProvider,
            "_post_speech",
            new=AsyncMock(side_effect=RuntimeError("network error")),
        ) as mocked:
            with pytest.raises(RuntimeError, match="network error"):
                await provider.synthesize_audio(text="hazir", locale="tr-TR")

    assert mocked.call_count == 2


async def test_mock_voice_provider_synthesize_audio_returns_none():
    provider = MockVoiceProvider()
    result = await provider.synthesize_audio(text="hazir", locale="tr-TR")
    assert result is None