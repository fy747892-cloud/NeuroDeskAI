import json
import logging
import re
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import settings
from app.core.llm_retry import with_retry

logger = logging.getLogger(__name__)


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

        try:
            transcript = await with_retry(
                lambda: self._post_transcription(
                    audio_bytes=audio_bytes,
                    filename=filename,
                    content_type=content_type,
                    language=language,
                    include_guidance=True,
                )
            )
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code not in {400, 415, 422}:
                raise
            logger.warning(
                "STT provider rejected guided request; retrying minimal request. "
                "status=%s body=%s",
                exc.response.status_code,
                _safe_response_preview(exc.response),
            )
            transcript = await with_retry(
                lambda: self._post_transcription(
                    audio_bytes=audio_bytes,
                    filename=filename,
                    content_type=content_type,
                    language=None,
                    include_guidance=False,
                )
            )
        return _validate_transcript_text(transcript)

    async def _post_transcription(
        self,
        *,
        audio_bytes: bytes,
        filename: str,
        content_type: str,
        language: str | None,
        include_guidance: bool,
    ) -> str:
        headers = {"Authorization": f"Bearer {self._api_key}"}
        data = {
            "model": self.stt_model_name,
            "response_format": "text",
            "temperature": "0",
        }
        if include_guidance:
            data["prompt"] = (
                "This is a Turkish phone call recording. Transcribe only "
                "speech that is actually audible. Write clear Turkish with "
                "normal punctuation and sentence breaks. If speakers are "
                "clearly distinguishable, use short labels such as Müşteri: "
                "and Temsilci:. Do not invent subtitles, credits, signatures, "
                "music, or inaudible sections."
            )
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
                        "\u00f6nerileri \u00e7\u0131kar\u0131rs\u0131n. Yaln\u0131zca ge\u00e7erli JSON d\u00f6nd\u00fcr ve "
                        "anahtarlar summary, tasks, appointments, deals olsun. "
                        "Kullan\u0131c\u0131ya g\u00f6sterilecek b\u00fct\u00fcn metin alanlar\u0131 T\u00fcrk\u00e7e "
                        "olmak zorunda: summary_text, title, description, reason, "
                        "time_hint, source_excerpt, evidence, notes. \u0130ngilizce ba\u015fl\u0131k, "
                        "a\u00e7\u0131klama veya gerek\u00e7e yazma. tasks.items g\u00f6rev listesine gider; "
                        "her item title, description, reason, priority ve confidence i\u00e7ersin. "
                        "appointments.items takvime gider; her item title, description, "
                        "proposed_datetime, end_datetime veya time_hint ve confidence i\u00e7ersin. "
                        "deals.items f\u0131rsatlara gider; her item title, description, stage, "
                        "value/currency varsa onlar ve confidence i\u00e7ersin. stage teknik enumdur "
                        "ve sadece lead, proposal_sent, negotiation, invoiced, won, lost olabilir. "
                        "priority teknik enumdur ve sadece low, medium, high olabilir. "
                        "Kesin bilgi yoksa kullan\u0131c\u0131ya a\u00e7\u0131k bir kontrol/takip \u00f6nerisi yaz; "
                        "ham transkript veya anlams\u0131z OCR metni kopyalama."
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
        tasks = _normalize_items_payload(data.get("tasks"), action_type="task")
        appointments = _normalize_items_payload(
            data.get("appointments"), action_type="appointment"
        )
        deals = _normalize_items_payload(data.get("deals"), action_type="deal")

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


def _safe_response_preview(response: httpx.Response, *, max_length: int = 500) -> str:
    text = response.text.replace("\n", " ").strip()
    return text[:max_length]


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
    summary_text = _to_turkish_display_text(summary_text)
    return {
        "summary_text": summary_text,
        "summary_type": str(payload.get("summary_type") or "conversation_summary"),
        "confidence": _normalize_confidence(payload.get("confidence"), default=0.7),
    }


def _normalize_items_payload(payload: Any, *, action_type: str) -> dict:
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
        item["title"] = _to_turkish_display_text(str(title).strip())
        if item["title"]:
            _normalize_display_fields(item, action_type=action_type)
            normalized.append(item)
    for item in normalized:
        item["confidence"] = _normalize_confidence(item.get("confidence"), default=0.6)
    return {"items": normalized}


def _normalize_display_fields(item: dict, *, action_type: str) -> None:
    for key in ("description", "reason", "time_hint", "source_excerpt", "evidence", "notes"):
        value = item.get(key)
        if isinstance(value, str):
            item[key] = _to_turkish_display_text(value)

    if action_type == "task":
        item["priority"] = _normalize_priority(item.get("priority"))
        item.setdefault("description", "Görüşmeden çıkarılan takip adımını kontrol et.")
        item.setdefault("reason", "Bu görev görüşme içeriğinde geçen aksiyon ihtiyacından çıkarıldı.")
    elif action_type == "appointment":
        item.setdefault("description", "Görüşmeden çıkarılan randevu önerisini kontrol et.")
        item.setdefault("reason", "Bu randevu önerisi görüşmede geçen tarih veya takip ihtiyacından çıkarıldı.")
    elif action_type == "deal":
        item["stage"] = _normalize_deal_stage(item.get("stage"))
        item.setdefault("description", "Görüşmeden çıkarılan fırsat bilgisini kontrol et.")
        item.setdefault("reason", "Bu fırsat görüşmede geçen satış, teklif veya iş ihtimalinden çıkarıldı.")


def _normalize_priority(value: Any) -> str:
    normalized = str(value or "medium").strip().lower()
    return normalized if normalized in {"low", "medium", "high"} else "medium"


def _normalize_deal_stage(value: Any) -> str:
    normalized = str(value or "lead").strip().lower()
    return normalized if normalized in {
        "lead",
        "proposal_sent",
        "negotiation",
        "invoiced",
        "won",
        "lost",
    } else "lead"


def _normalize_confidence(value: Any, *, default: float) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        confidence = default
    return max(0.0, min(1.0, confidence))


_DISPLAY_TRANSLATIONS = {
    "follow up": "Takip et",
    "follow up later": "Daha sonra takip et",
    "review meeting": "Toplantıyı gözden geçir",
    "prepare quarterly report": "Çeyrek raporu hazırla",
    "schedule follow-up": "Takip randevusu planla",
    "schedule a follow-up": "Takip randevusu planla",
    "study for the exam": "Sınava çalış",
    "conversation": "Görüşme",
    "ai analysis did not produce actions; review the conversation and decide next steps.": (
        "AI analizi net aksiyon üretmedi; görüşmeyi kontrol edip sonraki adımı belirle."
    ),
    "review the conversation and clarify next steps.": (
        "Görüşmeyi incele ve sonraki adımları netleştir."
    ),
    "extracted from conversation analysis.": "Görüşme analizinden çıkarıldı.",
    "extracted from file analysis.": "Dosya analizinden çıkarıldı.",
    "next steps": "sonraki adımlar",
}


def _to_turkish_display_text(value: str) -> str:
    cleaned = " ".join(value.split()).strip()
    if not cleaned:
        return cleaned

    exact = _DISPLAY_TRANSLATIONS.get(cleaned.lower())
    if exact:
        return exact

    replacements = {
        r"\bfollow up:\s*": "Takip et: ",
        r"\bschedule follow-up for\s+": "",
        r"\bschedule a follow-up for\s+": "",
        r"\bfor follow-up\b": "için takip",
        r"\bfor\s+": "için ",
        r"\bmeeting\b": "toplantı",
        r"\bcall\b": "çağrı",
        r"\bconversation\b": "görüşme",
        r"\bproposal\b": "teklif",
        r"\bopportunity\b": "fırsat",
        r"\blead\b": "potansiyel müşteri",
    }
    translated = cleaned
    for pattern, replacement in replacements.items():
        translated = re.sub(pattern, replacement, translated, flags=re.IGNORECASE)
    return translated.strip()


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
    return _format_transcript_text(cleaned)


def _format_transcript_text(transcript: str) -> str:
    transcript = re.sub(r"\s+([,.!?;:])", r"\1", transcript)
    transcript = re.sub(r"([.!?])\s+(?=[A-ZÇĞİÖŞÜ0-9])", r"\1\n", transcript)
    transcript = re.sub(
        r"\s+(?=(Müşteri|Temsilci|Musteri|Temsilci|Konuşmacı|Kisi|Kişi)\s*:)",
        "\n",
        transcript,
        flags=re.IGNORECASE,
    )
    lines = [" ".join(line.split()) for line in transcript.splitlines()]
    return "\n".join(line for line in lines if line).strip()
