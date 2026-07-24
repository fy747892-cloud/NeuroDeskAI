import json
import re
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import settings
from app.core.llm_retry import with_retry


@dataclass(frozen=True)
class AnalysisOutput:
    summary: dict
    tasks: dict
    appointments: dict
    deals: dict
    input_tokens: int
    output_tokens: int


MockAnalysisOutput = AnalysisOutput


class MockAIProvider:
    provider_name = "mock"
    model_name = "mock-analysis-v1"
    stt_model_name = "mock-stt-v1"

    async def transcribe_audio(
        self, *, audio_bytes: bytes, filename: str, content_type: str, language: str | None
    ) -> str:
        if not audio_bytes:
            raise RuntimeError("Mock provider received empty audio.")
        return f"[mock transcript for {filename}, {len(audio_bytes)} bytes]"

    async def analyze_conversation(self, *, title: str, transcript_text: str) -> AnalysisOutput:
        if "[mock-fail]" in transcript_text.lower():
            raise RuntimeError("Mock provider failed to analyze conversation.")

        clean_text = " ".join(transcript_text.split())
        preview = clean_text[:240]
        summary_text = preview if preview else f"G\u00f6r\u00fc\u015fme: {title}"

        tasks = {
            "items": [
                {
                    "title": f"Takip et: {title}",
                    "description": "G\u00f6r\u00fc\u015fmeyi incele ve sonraki ad\u0131mlar\u0131 netle\u015ftir.",
                    "confidence": 0.72,
                }
            ]
        }
        appointments = {
            "items": [
                {
                    "title": f"{title} i\u00e7in takip randevusu planla",
                    "proposed_datetime": "2026-07-17T09:00:00+03:00",
                    "time_hint": "gelecek hafta",
                    "confidence": 0.61,
                }
            ]
        }
        deals = {
            "items": [
                {
                    "title": f"{title} kaynakl\u0131 f\u0131rsat",
                    "stage": "proposal_sent",
                    "confidence": 0.55,
                }
            ]
        }
        output_text = summary_text + str(tasks) + str(appointments) + str(deals)

        return MockAnalysisOutput(
            summary={
                "summary_text": summary_text,
                "summary_type": "conversation_summary",
                "confidence": 0.82,
            },
            tasks=tasks,
            appointments=appointments,
            deals=deals,
            input_tokens=max(1, len(transcript_text) // 4),
            output_tokens=max(1, len(output_text) // 4),
        )


class OpenAICompatibleAIProvider:
    provider_name = "openai"

    def __init__(self) -> None:
        self.model_name = settings.llm_analysis_model
        self.stt_model_name = settings.llm_stt_model
        self._base_url = settings.llm_base_url.rstrip("/")
        self._api_key = settings.llm_api_key
        self._timeout = settings.llm_timeout_seconds

    async def transcribe_audio(
        self, *, audio_bytes: bytes, filename: str, content_type: str, language: str | None
    ) -> str:
        if not self._api_key:
            raise RuntimeError("LLM_API_KEY is required when LLM_PROVIDER is openai.")

        transcript = await with_retry(
            lambda: self._post_transcription(
                audio_bytes=audio_bytes,
                filename=filename,
                content_type=content_type,
                language=language,
            )
        )
        return _validate_transcript_text(transcript)

    async def _post_transcription(
        self, *, audio_bytes: bytes, filename: str, content_type: str, language: str | None
    ) -> str:
        headers = {"Authorization": f"Bearer {self._api_key}"}
        data = {
            "model": self.stt_model_name,
            "response_format": "text",
            "temperature": "0",
            "prompt": (
                "This is a Turkish phone call recording. Transcribe only "
                "speech that is actually audible. Do not invent subtitles, "
                "credits, signatures, music, or inaudible sections."
            ),
        }
        if language:
            data["language"] = language
        files = {"file": (filename, audio_bytes, content_type)}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._base_url}/audio/transcriptions",
                headers=headers,
                data=data,
                files=files,
            )
        response.raise_for_status()
        return response.text

    async def analyze_conversation(self, *, title: str, transcript_text: str) -> AnalysisOutput:
        if not self._api_key:
            raise RuntimeError("LLM_API_KEY is required when LLM_PROVIDER is openai.")

        payload = {
            "model": self.model_name,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Sen T\u00fcrk\u00e7e \u00e7al\u0131\u015fan bir CRM asistan\u0131s\u0131n. G\u00f6r\u00fc\u015fme "
                        "transkriptlerinden \u00f6zet, g\u00f6rev, randevu ve f\u0131rsat "
                        "\u00f6nerileri \u00e7\u0131kar\u0131rs\u0131n. Kullan\u0131c\u0131ya g\u00f6sterilecek t\u00fcm "
                        "metinleri T\u00fcrk\u00e7e yaz: summary_text, title, description, "
                        "reason, time_hint ve benzeri alanlar \u0130ngilizce olmamal\u0131. "
                        "Yaln\u0131zca ge\u00e7erli JSON d\u00f6nd\u00fcr ve anahtarlar summary, tasks, "
                        "appointments, deals olsun. tasks.items, appointments.items "
                        "ve deals.items dizi olmal\u0131. Her item title ve 0-1 aras\u0131nda "
                        "confidence i\u00e7ermeli. Randevu itemlar\u0131 m\u00fcmk\u00fcnse "
                        "proposed_datetime i\u00e7ermeli. F\u0131rsat itemlar\u0131 g\u00f6r\u00fc\u015fmede ge\u00e7en "
                        "sat\u0131\u015f/teklif ihtimallerini temsil eder ve stage \u015fu "
                        "de\u011ferlerden biri olmal\u0131: lead, proposal_sent, negotiation, "
                        "invoiced, won, lost. Tutar ge\u00e7tiyse value say\u0131sal olmal\u0131."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"G\u00f6r\u00fc\u015fme ba\u015fl\u0131\u011f\u0131: {title}\n\n"
                        f"Transkript:\n{transcript_text}"
                    ),
                },
            ],
        }
        response = await with_retry(lambda: self._post_chat_completion(payload))
        content = response["choices"][0]["message"]["content"]
        data = _parse_json_object(content)
        usage = response.get("usage", {})

        summary = _normalize_summary(data.get("summary"), title=title)
        tasks = _normalize_items_payload(data.get("tasks"))
        appointments = _normalize_items_payload(data.get("appointments"))
        deals = _normalize_items_payload(data.get("deals"))

        return AnalysisOutput(
            summary=summary,
            tasks=tasks,
            appointments=appointments,
            deals=deals,
            input_tokens=int(usage.get("prompt_tokens") or max(1, len(transcript_text) // 4)),
            output_tokens=int(usage.get("completion_tokens") or max(1, len(content) // 4)),
        )

    async def _post_chat_completion(self, payload: dict[str, Any]) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
        response.raise_for_status()
        return response.json()


def get_ai_provider():
    provider = settings.llm_provider.lower()
    if provider in {"mock", "local"}:
        return MockAIProvider()
    if provider in {"openai", "openai-compatible"}:
        return OpenAICompatibleAIProvider()
    raise RuntimeError(f"Unsupported LLM provider: {settings.llm_provider}")


def _parse_json_object(content: str) -> dict[str, Any]:
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError("LLM response was not valid JSON.") from exc
    if not isinstance(data, dict):
        raise RuntimeError("LLM response must be a JSON object.")
    return data


def _normalize_summary(payload: Any, *, title: str) -> dict:
    if not isinstance(payload, dict):
        payload = {}
    summary_text = str(payload.get("summary_text") or payload.get("text") or "").strip()
    if not summary_text:
        summary_text = f"G\u00f6r\u00fc\u015fme: {title}"
    return {
        "summary_text": summary_text,
        "summary_type": str(payload.get("summary_type") or "conversation_summary"),
        "confidence": _normalize_confidence(payload.get("confidence"), default=0.7),
    }


def _normalize_items_payload(payload: Any) -> dict:
    if isinstance(payload, list):
        items = payload
    elif isinstance(payload, dict):
        items = (
            payload.get("items")
            or payload.get("actions")
            or payload.get("tasks")
            or payload.get("appointments")
            or payload.get("deals")
            or payload.get("suggestions")
        )
    else:
        items = None
    if not isinstance(items, list):
        return {"items": []}
    normalized = []
    for item in items:
        if not isinstance(item, dict):
            continue
        title = item.get("title") or item.get("name") or item.get("subject")
        if not title:
            continue
        item["title"] = str(title).strip()
        if item["title"]:
            normalized.append(item)
    for item in normalized:
        item["confidence"] = _normalize_confidence(item.get("confidence"), default=0.6)
    return {"items": normalized}


def _normalize_confidence(value: Any, *, default: float) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        confidence = default
    return max(0.0, min(1.0, confidence))


_BOGUS_TRANSCRIPT_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        "^altyaz",
        r"^subtitle[s]?\s*(by|:)",
        r"^caption[s]?\s*(by|:)",
        r"^abone ol",
        "^izlediginiz icin tesekkur",
        r"^thanks for watching",
        r"^\[?(music|silence|inaudible)\]?$",
    )
]


def _validate_transcript_text(transcript: str) -> str:
    cleaned = " ".join(transcript.split()).strip()
    if not cleaned:
        raise RuntimeError("Transcription returned empty text.")
    if len(cleaned) < 12:
        raise RuntimeError("Transcription did not contain enough speech.")
    if any(pattern.search(cleaned) for pattern in _BOGUS_TRANSCRIPT_PATTERNS):
        raise RuntimeError("Transcription looks like subtitle noise instead of speech.")
    words = re.findall(r"\w+", cleaned, flags=re.UNICODE)
    if len(words) < 3:
        raise RuntimeError("Transcription did not contain enough speech.")
    return cleaned
