import httpx
import pytest

from app.core.config import settings
from app.modules.ai.diarization import PyannoteAIHostedDiarizationProvider, SpeakerTurn


class _FakeResponse:
    def __init__(self, json_data: dict, status_code: int = 200):
        self._json = json_data
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = httpx.Request("POST", "https://api.pyannote.ai/v1/diarize")
            response = httpx.Response(self.status_code, request=request)
            raise httpx.HTTPStatusError("error", request=request, response=response)

    def json(self) -> dict:
        return self._json


class _FakeStorage:
    def __init__(self) -> None:
        self.deleted_keys: list[str] = []
        self.put_called = False

    async def put_object(self, *, storage_key: str, data: bytes, content_type: str) -> None:
        self.put_called = True

    async def generate_download_url(self, *, storage_key: str) -> str:
        return f"https://storage.example.com/{storage_key}"

    async def delete_object(self, *, storage_key: str) -> None:
        self.deleted_keys.append(storage_key)


def _make_provider(monkeypatch: pytest.MonkeyPatch) -> tuple[PyannoteAIHostedDiarizationProvider, _FakeStorage]:
    monkeypatch.setattr(settings, "pyannoteai_api_key", "test-key")
    monkeypatch.setattr(settings, "pyannoteai_poll_interval_seconds", 0.0)
    monkeypatch.setattr(settings, "pyannoteai_poll_timeout_seconds", 0.05)
    provider = PyannoteAIHostedDiarizationProvider()
    fake_storage = _FakeStorage()
    provider._storage = fake_storage  # type: ignore[assignment]
    return provider, fake_storage


async def test_diarize_returns_turns_on_success(monkeypatch: pytest.MonkeyPatch):
    provider, fake_storage = _make_provider(monkeypatch)

    async def fake_post(self, url, **kwargs):
        return _FakeResponse({"jobId": "job-1", "status": "created"})

    async def fake_get(self, url, **kwargs):
        return _FakeResponse(
            {
                "jobId": "job-1",
                "status": "succeeded",
                "output": {
                    "diarization": [
                        {"start": 0.0, "end": 2.0, "speaker": "SPEAKER_00"},
                        {"start": 2.0, "end": 4.5, "speaker": "SPEAKER_01"},
                    ]
                },
            }
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    turns = await provider.diarize(audio_bytes=b"fake-audio", filename="call.m4a")

    assert turns == [
        SpeakerTurn(start=0.0, end=2.0, speaker="SPEAKER_00"),
        SpeakerTurn(start=2.0, end=4.5, speaker="SPEAKER_01"),
    ]
    assert fake_storage.put_called is True
    assert len(fake_storage.deleted_keys) == 1


async def test_diarize_parses_alternate_field_names(monkeypatch: pytest.MonkeyPatch):
    provider, _ = _make_provider(monkeypatch)

    async def fake_post(self, url, **kwargs):
        return _FakeResponse({"jobId": "job-2", "status": "created"})

    async def fake_get(self, url, **kwargs):
        return _FakeResponse(
            {
                "jobId": "job-2",
                "status": "succeeded",
                "output": {
                    "diarization": [
                        {"startTime": 0.0, "endTime": 1.0, "speakerLabel": "SPEAKER_00"},
                    ]
                },
            }
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    turns = await provider.diarize(audio_bytes=b"fake-audio", filename="call.m4a")

    assert turns == [SpeakerTurn(start=0.0, end=1.0, speaker="SPEAKER_00")]


async def test_diarize_raises_and_cleans_up_on_failed_job(monkeypatch: pytest.MonkeyPatch):
    provider, fake_storage = _make_provider(monkeypatch)

    async def fake_post(self, url, **kwargs):
        return _FakeResponse({"jobId": "job-3", "status": "created"})

    async def fake_get(self, url, **kwargs):
        return _FakeResponse({"jobId": "job-3", "status": "failed"})

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    with pytest.raises(RuntimeError, match="failed"):
        await provider.diarize(audio_bytes=b"fake-audio", filename="call.m4a")

    assert len(fake_storage.deleted_keys) == 1


async def test_diarize_times_out_and_cleans_up(monkeypatch: pytest.MonkeyPatch):
    provider, fake_storage = _make_provider(monkeypatch)

    async def fake_post(self, url, **kwargs):
        return _FakeResponse({"jobId": "job-4", "status": "created"})

    async def fake_get(self, url, **kwargs):
        return _FakeResponse({"jobId": "job-4", "status": "running"})

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    with pytest.raises(RuntimeError, match="timed out"):
        await provider.diarize(audio_bytes=b"fake-audio", filename="call.m4a")

    assert len(fake_storage.deleted_keys) == 1


async def test_diarize_requires_api_key(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "pyannoteai_api_key", "")
    provider = PyannoteAIHostedDiarizationProvider()
    provider._storage = _FakeStorage()  # type: ignore[assignment]

    with pytest.raises(RuntimeError, match="PYANNOTEAI_API_KEY"):
        await provider.diarize(audio_bytes=b"fake-audio", filename="call.m4a")
