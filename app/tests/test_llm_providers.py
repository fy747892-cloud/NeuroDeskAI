import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.core.config import settings
from app.core.llm_retry import with_retry
from app.modules.ai.provider import OpenAICompatibleAIProvider
from app.modules.ai_chat.provider import OpenAICompatibleChatProvider
from app.modules.ai_chat.retrieval import ContextItem
from app.modules.files.provider import OpenAICompatibleDocumentSummaryProvider
from app.modules.search.provider import OpenAICompatibleEmbeddingProvider

FAKE_UUID = uuid.uuid4()


def _openai_settings():
    return patch.multiple(settings, llm_provider="openai", llm_api_key="test-key")


def _chat_completion_response(content: str, *, prompt_tokens: int = 42, completion_tokens: int = 7) -> dict:
    return {
        "choices": [{"message": {"content": content}}],
        "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens},
    }


async def test_with_retry_succeeds_after_one_failure():
    call_count = 0

    async def flaky():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("transient failure")
        return "ok"

    result = await with_retry(flaky, attempts=2, backoff_seconds=(0.0, 0.0))
    assert result == "ok"
    assert call_count == 2


async def test_with_retry_raises_after_exhausting_attempts():
    call_count = 0

    async def always_fails():
        nonlocal call_count
        call_count += 1
        raise RuntimeError("permanent failure")

    with pytest.raises(RuntimeError, match="permanent failure"):
        await with_retry(always_fails, attempts=2, backoff_seconds=(0.0, 0.0))
    assert call_count == 2


async def test_ai_provider_maps_successful_response():
    with _openai_settings():
        provider = OpenAICompatibleAIProvider()
        response = _chat_completion_response(
            '{"summary": {"summary_text": "Discussed pricing", "confidence": 0.9}, '
            '"tasks": {"items": [{"title": "Send proposal", "confidence": 0.8}]}, '
            '"appointments": {"items": [{"title": "Follow-up call", "proposed_datetime": '
            '"2026-08-01T10:00:00+03:00", "confidence": 0.7}]}}'
        )
        with patch.object(
            OpenAICompatibleAIProvider, "_post_chat_completion", new=AsyncMock(return_value=response)
        ) as mocked:
            output = await provider.analyze_conversation(
                title="Client call", transcript_text="We discussed pricing and next steps."
            )

    mocked.assert_called_once()
    assert output.summary["summary_text"] == "Discussed pricing"
    assert output.tasks["items"][0]["title"] == "Send proposal"
    assert output.appointments["items"][0]["title"] == "Follow-up call"
    assert output.input_tokens == 42
    assert output.output_tokens == 7


async def test_ai_provider_retries_then_raises_on_persistent_failure():
    with _openai_settings():
        provider = OpenAICompatibleAIProvider()
        with patch.object(
            OpenAICompatibleAIProvider,
            "_post_chat_completion",
            new=AsyncMock(side_effect=RuntimeError("network error")),
        ) as mocked:
            with pytest.raises(RuntimeError, match="network error"):
                await provider.analyze_conversation(title="x", transcript_text="y")

    assert mocked.call_count == 2


async def test_chat_provider_maps_successful_response():
    with _openai_settings():
        provider = OpenAICompatibleChatProvider()
        response = _chat_completion_response("Your proposal was sent last week.")
        context_items = [
            ContextItem(source_type="task", source_id=FAKE_UUID, title="Send proposal", snippet="Proposal sent")
        ]
        with patch.object(
            OpenAICompatibleChatProvider, "_post_chat_completion", new=AsyncMock(return_value=response)
        ) as mocked:
            answer = await provider.generate_answer(
                question="Did we send the proposal?", context_items=context_items
            )

    mocked.assert_called_once()
    assert answer.answer_text.startswith("Your proposal was sent")
    assert answer.sources == context_items
    assert answer.input_tokens == 42
    assert answer.output_tokens == 7


async def test_chat_provider_skips_llm_call_when_context_is_empty():
    with _openai_settings():
        provider = OpenAICompatibleChatProvider()
        with patch.object(
            OpenAICompatibleChatProvider, "_post_chat_completion", new=AsyncMock()
        ) as mocked:
            answer = await provider.generate_answer(question="Anything?", context_items=[])

    mocked.assert_not_called()
    assert answer.confidence == 0.0
    assert answer.sources == []


async def test_embedding_provider_maps_successful_response():
    with _openai_settings():
        provider = OpenAICompatibleEmbeddingProvider()
        response = {"data": [{"embedding": [0.1, 0.2, 0.3]}]}
        with patch.object(
            OpenAICompatibleEmbeddingProvider, "_post_embedding", new=AsyncMock(return_value=response)
        ) as mocked:
            vector = await provider.embed("some text to embed")

    mocked.assert_called_once()
    assert vector == [0.1, 0.2, 0.3]


async def test_embedding_provider_retries_then_raises_on_persistent_failure():
    with _openai_settings():
        provider = OpenAICompatibleEmbeddingProvider()
        with patch.object(
            OpenAICompatibleEmbeddingProvider,
            "_post_embedding",
            new=AsyncMock(side_effect=RuntimeError("network error")),
        ) as mocked:
            with pytest.raises(RuntimeError, match="network error"):
                await provider.embed("text")

    assert mocked.call_count == 2


async def test_document_summary_provider_maps_successful_response():
    with _openai_settings():
        provider = OpenAICompatibleDocumentSummaryProvider()
        response = _chat_completion_response("  This document covers Q3 sales targets.  ")
        with patch.object(
            OpenAICompatibleDocumentSummaryProvider,
            "_post_chat_completion",
            new=AsyncMock(return_value=response),
        ) as mocked:
            summary = await provider.summarize("Some long document text about Q3 sales targets.")

    mocked.assert_called_once()
    assert summary == "This document covers Q3 sales targets."