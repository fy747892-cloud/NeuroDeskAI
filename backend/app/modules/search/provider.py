import hashlib
import re

from app.modules.search.models import EMBEDDING_DIMENSIONS


class MockEmbeddingProvider:
    """Deterministic hashing-trick bag-of-words embedding (no external API).

    Words are hashed into a fixed-size vector (feature hashing, the same
    technique behind scikit-learn's HashingVectorizer), so texts sharing
    distinctive words end up with genuinely higher cosine similarity than
    unrelated texts — unlike a purely random mock, this supports real
    relevance ranking.
    """

    model_name = "mock-hashing-v1"

    def embed(self, text: str) -> list[float]:
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
