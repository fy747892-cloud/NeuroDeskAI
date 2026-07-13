import hashlib
import re
from typing import Any

import httpx

from app.core.config import settings
from app.core.llm_retry import with_retry
from app.modules.search.models import EMBEDDING_DIMENSIONS


class MockEmbeddingProvider:
    """Deterministic hashing-trick bag-of-words embedding (no external API).

    Words are hashed into a fixed-size vector (feature hashing, the same
    technique behind scikit-learn's HashingVectorizer), so texts sharing
    distinctive words end up with genuinely higher cosine similarity than
    unrelated texts — unlike a purely random mock, this supports real
    relevance ranking.
    """

    provider_name = "mock"
    model_name = "mock-hashing-v1"

    async def embed(self, text: str) -> list[float]:
        vector = [0.0] * EMBEDDING_DIMENSIONS
        for word in re.findall(r"\w+", text.lower()):
            digest = hashlib.sha256(word.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % EMBEDDING_DIMENSIONS
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign

        norm = sum(component * component for component in vector) ** 0.5
        if norm == 0:
            return vector
        return [component / norm for component in vector]


class OpenAICompatibleEmbeddingProvider:
    provider_name = "openai"

    def __init__(self) -> None:
        self.model_name = settings.llm_embedding_model
        self._base_url = settings.llm_base_url.rstrip("/")
        self._api_key = settings.llm_api_key
        self._timeout = settings.llm_timeout_seconds

    async def embed(self, text: str) -> list[float]:
        if not self._api_key:
            raise RuntimeError("LLM_API_KEY is required when LLM_PROVIDER is openai.")

        payload = {
            "model": self.model_name,
            "input": text,
            "dimensions": EMBEDDING_DIMENSIONS,
        }
        response = await with_retry(lambda: self._post_embedding(payload))
        return response["data"][0]["embedding"]

    async def _post_embedding(self, payload: dict[str, Any]) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._base_url}/embeddings",
                headers=headers,
                json=payload,
            )
        response.raise_for_status()
        return response.json()


def get_embedding_provider():
    provider = settings.llm_provider.lower()
    if provider in {"mock", "local"}:
        return MockEmbeddingProvider()
    if provider in {"openai", "openai-compatible"}:
        return OpenAICompatibleEmbeddingProvider()
    raise RuntimeError(f"Unsupported LLM provider: {settings.llm_provider}")
