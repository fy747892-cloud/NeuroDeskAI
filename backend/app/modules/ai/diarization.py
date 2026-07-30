import asyncio
import io
import logging
from dataclasses import dataclass
from typing import Any, Protocol

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SpeakerTurn:
    start: float
    end: float
    speaker: str


class DiarizationProvider(Protocol):
    async def diarize(self, *, audio_bytes: bytes, filename: str) -> list[SpeakerTurn]: ...


class MockDiarizationProvider:
    """Deterministic two-speaker split, used in dev/tests without pyannote."""

    async def diarize(self, *, audio_bytes: bytes, filename: str) -> list[SpeakerTurn]:
        return [
            SpeakerTurn(start=0.0, end=2.0, speaker="SPEAKER_00"),
            SpeakerTurn(start=2.0, end=4.0, speaker="SPEAKER_01"),
        ]


class PyannoteDiarizationProvider:
    _pipeline: Any = None

    async def diarize(self, *, audio_bytes: bytes, filename: str) -> list[SpeakerTurn]:
        return await asyncio.to_thread(self._diarize_sync, audio_bytes)

    def _get_pipeline(self) -> Any:
        if PyannoteDiarizationProvider._pipeline is None:
            if not settings.hf_token:
                raise RuntimeError(
                    "HF_TOKEN is required when DIARIZATION_PROVIDER is pyannote."
                )
            from pyannote.audio import Pipeline

            PyannoteDiarizationProvider._pipeline = Pipeline.from_pretrained(
                settings.diarization_model, token=settings.hf_token
            )
        return PyannoteDiarizationProvider._pipeline

    def _diarize_sync(self, audio_bytes: bytes) -> list[SpeakerTurn]:
        import torchaudio

        pipeline = self._get_pipeline()
        waveform, sample_rate = torchaudio.load(io.BytesIO(audio_bytes))
        output = pipeline({"waveform": waveform, "sample_rate": sample_rate})
        # pyannote.audio >=4 wraps the classic Annotation in a DiarizeOutput;
        # speaker_diarization is the pyannote.core.Annotation with itertracks().
        annotation = getattr(output, "speaker_diarization", output)
        return [
            SpeakerTurn(start=turn.start, end=turn.end, speaker=speaker)
            for turn, _track, speaker in annotation.itertracks(yield_label=True)
        ]


def get_diarization_provider() -> DiarizationProvider | None:
    mode = settings.diarization_provider.lower()
    if mode == "disabled":
        return None
    if mode == "mock":
        return MockDiarizationProvider()
    if mode == "pyannote":
        return PyannoteDiarizationProvider()
    raise RuntimeError(f"Unsupported diarization provider: {settings.diarization_provider}")


def build_diarized_transcript(
    segments: list[dict[str, Any]],
    turns: list[SpeakerTurn],
    *,
    participant_names: list[str] | None = None,
) -> str:
    """Merge Whisper segments with diarization turns into "Name: text" lines.

    Returns an empty string if no speaker could be matched (e.g. a single
    speaker or an empty diarization result) so callers can fall back to the
    plain transcript instead of emitting a transcript with no speaker labels.
    """
    if not turns:
        return ""

    labeled: list[tuple[str | None, str]] = []
    for segment in segments:
        text = str(segment.get("text") or "").strip()
        if not text:
            continue
        seg_start = float(segment.get("start") or 0.0)
        seg_end = float(segment.get("end") or seg_start)
        labeled.append((_best_matching_speaker(seg_start, seg_end, turns), text))

    if not labeled:
        return ""

    speaker_order: list[str] = []
    for speaker_id, _text in labeled:
        if speaker_id and speaker_id not in speaker_order:
            speaker_order.append(speaker_id)

    if not speaker_order:
        return ""

    label_map: dict[str, str] = {}
    for index, speaker_id in enumerate(speaker_order):
        if participant_names and index < len(participant_names):
            label_map[speaker_id] = participant_names[index]
        else:
            label_map[speaker_id] = f"Konuşmacı {index + 1}"

    fallback_label = label_map[speaker_order[0]]
    lines: list[str] = []
    current_label: str | None = None
    current_parts: list[str] = []
    for speaker_id, text in labeled:
        label = label_map.get(speaker_id, "") if speaker_id else (current_label or fallback_label)
        if label != current_label:
            if current_label is not None and current_parts:
                lines.append(f"{current_label}: {' '.join(current_parts)}")
            current_label = label
            current_parts = [text]
        else:
            current_parts.append(text)
    if current_label is not None and current_parts:
        lines.append(f"{current_label}: {' '.join(current_parts)}")

    return "\n".join(lines)


def _best_matching_speaker(seg_start: float, seg_end: float, turns: list[SpeakerTurn]) -> str | None:
    best_speaker: str | None = None
    best_overlap = 0.0
    for turn in turns:
        overlap = min(seg_end, turn.end) - max(seg_start, turn.start)
        if overlap > best_overlap:
            best_overlap = overlap
            best_speaker = turn.speaker
    return best_speaker
