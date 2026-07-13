from typing import Any

import httpx

from app.core.config import settings
from app.core.llm_retry import with_retry

DAILY_TEMPLATE = "Bugün {appointments} toplantın var. Dün {calls} görüşme yaptın."
WEEKLY_TEMPLATE = "Bu hafta {appointments} toplantın var. Geçen hafta {calls} görüşme yaptın."


class MockDigestNarrativeProvider:
    """Deterministic template phrasing — no LLM. The numbers are always computed
    upstream by the caller; this provider (and its real counterpart) only ever
    formats them into a sentence, never generates them (CILT_5 §47: 'LLM
    yalnızca doğal dil formatlamada kullanılır')."""

    provider_name = "mock"
    model_name = "mock-digest-v1"

    async def narrate(
        self,
        *,
        period: str,
        appointments_count: int,
        calls_count: int,
        contacts_awaiting_reply_count: int,
        unanswered_emails_count: int,
    ) -> str:
        template = DAILY_TEMPLATE if period == "daily" else WEEKLY_TEMPLATE
        opening = template.format(appointments=appointments_count, calls=calls_count)
        return (
            f"{opening} {contacts_awaiting_reply_count} müşteri geri dönüş bekliyor. "
            f"{unanswered_emails_count} e-postaya henüz cevap verilmedi."
        )


class OpenAICompatibleDigestNarrativeProvider:
    """Real LLM phrasing via OpenAI-compatible Chat Completions — same
    LLM_PROVIDER/LLM_BASE_URL convention as the other real providers. The
    model is given the already-computed counts and asked only to phrase them
    naturally; it is explicitly instructed not to change the numbers."""

    provider_name = "openai"

    def __init__(self) -> None:
        self.model_name = settings.llm_analysis_model
        self._base_url = settings.llm_base_url.rstrip("/")
        self._api_key = settings.llm_api_key
        self._timeout = settings.llm_timeout_seconds

    async def narrate(
        self,
        *,
        period: str,
        appointments_count: int,
        calls_count: int,
        contacts_awaiting_reply_count: int,
        unanswered_emails_count: int,
    ) -> str:
        if not self._api_key:
            raise RuntimeError("LLM_API_KEY is required when LLM_PROVIDER is openai.")

        period_label = "bugün/dün" if period == "daily" else "bu hafta/geçen hafta"
        payload = {
            "model": self.model_name,
            "temperature": 0.3,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You write a short, warm 2-4 sentence Turkish daily-briefing digest "
                        "from the given counts. Use the exact numbers given — never invent, "
                        "round, or change them. Do not add any information not present in "
                        "the counts."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Period: {period_label}\n"
                        f"appointments_count={appointments_count}\n"
                        f"calls_count={calls_count}\n"
                        f"contacts_awaiting_reply_count={contacts_awaiting_reply_count}\n"
                        f"unanswered_emails_count={unanswered_emails_count}"
                    ),
                },
            ],
        }
        response = await with_retry(lambda: self._post_chat_completion(payload))
        return response["choices"][0]["message"]["content"].strip()

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


def get_digest_narrative_provider():
    provider = settings.llm_provider.lower()
    if provider in {"mock", "local"}:
        return MockDigestNarrativeProvider()
    if provider in {"openai", "openai-compatible"}:
        return OpenAICompatibleDigestNarrativeProvider()
    raise RuntimeError(f"Unsupported LLM provider: {settings.llm_provider}")