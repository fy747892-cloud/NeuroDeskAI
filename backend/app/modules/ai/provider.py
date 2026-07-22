import json
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
        summary_text = preview if preview else f"Görüşme: {title}"

        tasks = {
            "items": [
                {
                    "title": f"Takip et: {title}",
                    "description": "Görüşmeyi incele ve sonraki adımları netleştir.",
                    "confidence": 0.72,
                }
            ]
        }
        appointments = {
            "items": [
                {
                    "title": f"{title} için takip randevusu planla",
                    "proposed_datetime": "2026-07-17T09:00:00+03:00",
                    "time_hint": "gelecek hafta",
                    "confidence": 0.61,
                }
            ]
        }
        deals = {
            "items": [
                {
                    "title": f"{title} kaynaklı fırsat",
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
        transcript = transcript.strip()
        if not transcript:
            raise RuntimeError("Transcription returned empty text.")
        return transcript

    async def _post_transcription(
        self, *, audio_bytes: bytes, filename: str, content_type: str, language: str | None
    ) -> str:
        headers = {"Authorization": f"Bearer {self._api_key}"}
        data = {"model": self.stt_model_name, "response_format": "text"}
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
                        "Sen Türkçe çalışan bir CRM asistanısın. Görüşme "
                        "transkriptlerinden özet, görev, randevu ve fırsat "
                        "önerileri çıkarırsın. Kullanıcıya gösterilecek tüm "
                        "metinleri Türkçe yaz: summary_text, title, description, "
                        "reason, time_hint ve benzeri alanlar İngilizce olmamalı. "
                        "Yalnızca geçerli JSON döndür ve anahtarlar summary, tasks, "
                        "appointments, deals olsun. tasks.items, appointments.items "
                        "ve deals.items dizi olmalı. Her item title ve 0-1 arasında "
                        "confidence içermeli. Randevu itemları mümkünse "
                        "proposed_datetime içermeli. Fırsat itemları görüşmede geçen "
                        "satış/teklif ihtimallerini temsil eder ve stage şu "
                        "değerlerden biri olmalı: lead, proposal_sent, negotiation, "
                        "invoiced, won, lost. Tutar geçtiyse value sayısal olmalı."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Görüşme başlığı: {title}\n\n"
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
        summary_text = f"Görüşme: {title}"
    return {
        "summary_text": summary_text,
        "summary_type": str(payload.get("summary_type") or "conversation_summary"),
        "confidence": _normalize_confidence(payload.get("confidence"), default=0.7),
    }


def _normalize_items_payload(payload: Any) -> dict:
    if not isinstance(payload, dict):
        return {"items": []}
    items = payload.get("items")
    if not isinstance(items, list):
        return {"items": []}
    normalized = [item for item in items if isinstance(item, dict) and item.get("title")]
    for item in normalized:
        item["confidence"] = _normalize_confidence(item.get("confidence"), default=0.6)
    return {"items": normalized}


def _normalize_confidence(value: Any, *, default: float) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        confidence = default
    return max(0.0, min(1.0, confidence))
