from unittest.mock import AsyncMock, patch

import pytest

from app.core.config import settings
from app.modules.dashboard.provider import (
    MockDigestNarrativeProvider,
    OpenAICompatibleDigestNarrativeProvider,
)


def _openai_settings():
    return patch.multiple(settings, llm_provider="openai", llm_api_key="test-key")


def _chat_completion_response(content: str) -> dict:
    return {
        "choices": [{"message": {"content": content}}],
        "usage": {"prompt_tokens": 20, "completion_tokens": 15},
    }


async def test_mock_provider_formats_daily_template_with_exact_counts():
    provider = MockDigestNarrativeProvider()
    narrative = await provider.narrate(
        period="daily",
        appointments_count=3,
        calls_count=8,
        contacts_awaiting_reply_count=2,
        unanswered_emails_count=5,
    )
    assert narrative == (
        "Bugün 3 toplantın var. Dün 8 görüşme yaptın. "
        "2 müşteri geri dönüş bekliyor. 5 e-postaya henüz cevap verilmedi."
    )


async def test_mock_provider_formats_weekly_template_with_exact_counts():
    provider = MockDigestNarrativeProvider()
    narrative = await provider.narrate(
        period="weekly",
        appointments_count=1,
        calls_count=4,
        contacts_awaiting_reply_count=0,
        unanswered_emails_count=0,
    )
    assert narrative == (
        "Bu hafta 1 toplantın var. Geçen hafta 4 görüşme yaptın. "
        "0 müşteri geri dönüş bekliyor. 0 e-postaya henüz cevap verilmedi."
    )


async def test_openai_provider_sends_exact_counts_and_maps_response():
    with _openai_settings():
        provider = OpenAICompatibleDigestNarrativeProvider()
        response = _chat_completion_response("Bugün 3 toplantın var, harika gidiyor!")
        with patch.object(
            OpenAICompatibleDigestNarrativeProvider,
            "_post_chat_completion",
            new=AsyncMock(return_value=response),
        ) as mocked:
            narrative = await provider.narrate(
                period="daily",
                appointments_count=3,
                calls_count=8,
                contacts_awaiting_reply_count=2,
                unanswered_emails_count=5,
            )

    mocked.assert_called_once()
    sent_payload = mocked.call_args.args[0]
    sent_content = sent_payload["messages"][1]["content"]
    assert "appointments_count=3" in sent_content
    assert "calls_count=8" in sent_content
    assert "contacts_awaiting_reply_count=2" in sent_content
    assert "unanswered_emails_count=5" in sent_content
    assert narrative == "Bugün 3 toplantın var, harika gidiyor!"


async def test_openai_provider_retries_then_raises_on_persistent_failure():
    with _openai_settings():
        provider = OpenAICompatibleDigestNarrativeProvider()
        with patch.object(
            OpenAICompatibleDigestNarrativeProvider,
            "_post_chat_completion",
            new=AsyncMock(side_effect=RuntimeError("network error")),
        ) as mocked:
            with pytest.raises(RuntimeError, match="network error"):
                await provider.narrate(
                    period="daily",
                    appointments_count=1,
                    calls_count=1,
                    contacts_awaiting_reply_count=1,
                    unanswered_emails_count=1,
                )

    assert mocked.call_count == 2