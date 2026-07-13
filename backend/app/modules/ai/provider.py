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

    async def analyze_conversation(self, *, title: str, transcript_text: str) -> AnalysisOutput:
        if "[mock-fail]" in transcript_text.lower():
            raise RuntimeError("Mock provider failed to analyze conversation.")

        clean_text = " ".join(transcript_text.split())
        preview = clean_text[:240]
        summary_text = preview if preview else f"Conversation: {title}"

        tasks = {
            "items": [
                {
                    "title": f"Follow up: {title}",
                    "description": "Review the conversation and confirm next steps.",
                    "confidence": 0.72,
                }
            ]
        }
        appointments = {
            "items": [
                {
                    "title": f"Schedule follow-up for {title}",
                    "proposed_datetime": "2026-07-17T09:00:00+03:00",
                    "time_hint": "next week",
                    "confidence": 0.61,
                }
            ]
        }
        deals = {
            "items": [
                {
                    "title": f"Opportunity from {title}",
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
        self._base_url = settings.llm_base_url.rstrip("/")
        self._api_key = settings.llm_api_key
        self._timeout = settings.llm_timeout_seconds

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
                        "You extract structured CRM actions from call transcripts. "
                        "Return only valid JSON with keys summary, tasks, appointments, deals. "
                        "tasks.items, appointments.items, and deals.items must be arrays. "
                        "Each item should include title and confidence between 0 and 1. "
                        "Appointment items should include proposed_datetime when available. "
                        "Deal items represent sales opportunities/offers mentioned in the "
                        "conversation and should include stage, one of: lead, proposal_sent, "
                        "negotiation, invoiced, won, lost — and value (numeric) when a price "
                        "or amount was mentioned."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Conversation title: {title}\n\n"
                        f"Transcript:\n{transcript_text}"
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
        summary_text = f"Conversation: {title}"
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
