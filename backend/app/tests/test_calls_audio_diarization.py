import pytest
from httpx import AsyncClient

from app.api.v1 import calls as calls_module
from app.modules.ai.diarization import SpeakerTurn, build_diarized_transcript


async def _auth_headers(client: AsyncClient, email: str) -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "SuperSecret123", "display_name": "Test User"},
    )
    assert response.status_code == 201
    tokens = response.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


class _TwoSegmentProvider:
    """Mimics OpenAICompatibleAIProvider.transcribe_audio_with_timestamps with
    two speaker turns worth of segments, so diarization alignment can be
    exercised without a real Whisper/pyannote call."""

    provider_name = "two-segment-test-provider"

    async def transcribe_audio_with_timestamps(self, **_kwargs):
        return (
            "Merhaba nasilsiniz iyiyim tesekkurler",
            [
                {"start": 0.0, "end": 1.5, "text": "Merhaba nasilsiniz"},
                {"start": 2.5, "end": 4.0, "text": "iyiyim tesekkurler"},
            ],
        )


class _FixedTurnsDiarizationProvider:
    async def diarize(self, *, audio_bytes: bytes, filename: str):
        return [
            SpeakerTurn(start=0.0, end=2.0, speaker="SPEAKER_00"),
            SpeakerTurn(start=2.0, end=4.5, speaker="SPEAKER_01"),
        ]


async def test_create_call_from_audio_uses_diarized_transcript_when_enabled(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(calls_module, "get_ai_provider", lambda: _TwoSegmentProvider())
    monkeypatch.setattr(
        calls_module, "get_diarization_provider", lambda: _FixedTurnsDiarizationProvider()
    )

    headers = await _auth_headers(client, "diarized-call@example.com")
    response = await client.post(
        "/api/v1/calls/audio",
        headers=headers,
        data={"title": "Diarized call", "participant_names": "Ahmet, Ayse"},
        files={"audio": ("recording.m4a", b"fake-audio-bytes", "audio/mp4")},
    )

    assert response.status_code == 201
    transcript_text = response.json()["transcription"]["transcript_text"]
    assert transcript_text == "Ahmet: Merhaba nasilsiniz\nAyse: iyiyim tesekkurler"


async def test_create_call_from_audio_falls_back_when_diarization_fails(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
):
    class _FailingDiarizationProvider:
        async def diarize(self, *, audio_bytes: bytes, filename: str):
            raise RuntimeError("model unavailable")

    monkeypatch.setattr(calls_module, "get_ai_provider", lambda: _TwoSegmentProvider())
    monkeypatch.setattr(
        calls_module, "get_diarization_provider", lambda: _FailingDiarizationProvider()
    )

    headers = await _auth_headers(client, "diarized-call-fallback@example.com")
    response = await client.post(
        "/api/v1/calls/audio",
        headers=headers,
        data={"title": "Diarization fails"},
        files={"audio": ("recording.m4a", b"fake-audio-bytes", "audio/mp4")},
    )

    assert response.status_code == 201
    transcript_text = response.json()["transcription"]["transcript_text"]
    assert "Merhaba nasilsiniz" in transcript_text
    assert "iyiyim tesekkurler" in transcript_text


def test_build_diarized_transcript_merges_consecutive_same_speaker_segments():
    segments = [
        {"start": 0.0, "end": 1.0, "text": "Merhaba"},
        {"start": 1.0, "end": 2.0, "text": "ben Ahmet"},
        {"start": 3.0, "end": 4.0, "text": "Merhaba Ahmet"},
    ]
    turns = [
        SpeakerTurn(start=0.0, end=2.0, speaker="SPEAKER_00"),
        SpeakerTurn(start=2.5, end=4.5, speaker="SPEAKER_01"),
    ]

    result = build_diarized_transcript(segments, turns, participant_names=["Temsilci", "Musteri"])

    assert result == "Temsilci: Merhaba ben Ahmet\nMusteri: Merhaba Ahmet"


def test_build_diarized_transcript_falls_back_to_generic_labels_without_participant_names():
    segments = [{"start": 0.0, "end": 1.0, "text": "Selam"}]
    turns = [SpeakerTurn(start=0.0, end=1.0, speaker="SPEAKER_00")]

    result = build_diarized_transcript(segments, turns)

    assert result == "Konuşmacı 1: Selam"


def test_build_diarized_transcript_returns_empty_when_no_speaker_matches():
    segments = [{"start": 0.0, "end": 1.0, "text": "Selam"}]

    assert build_diarized_transcript(segments, turns=[]) == ""
    assert build_diarized_transcript(segments, turns=[SpeakerTurn(5.0, 6.0, "SPEAKER_00")]) == ""
