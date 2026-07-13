import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.search.models import Embedding


class EmbeddingRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_by_source(
        self, *, tenant_id: uuid.UUID, source_type: str, source_id: uuid.UUID
    ) -> Embedding | None:
        result = await self._db.execute(
            select(Embedding).where(
                Embedding.tenant_id == tenant_id,
                Embedding.source_type == source_type,
                Embedding.source_id == source_id,
            )
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        source_type: str,
        source_id: uuid.UUID,
        embedding_vector: list[float],
        content_hash: str,
        embedding_model: str,
        metadata: dict | None = None,
    ) -> Embedding:
        existing = await self.get_by_source(
            tenant_id=tenant_id, source_type=source_type, source_id=source_id
        )
        if existing is not None:
            existing.embedding_vector = embedding_vector
            existing.content_hash = content_hash
            existing.embedding_model = embedding_model
            existing.embedding_metadata = metadata
            await self._db.flush()
            return existing

        embedding = Embedding(
            tenant_id=tenant_id,
            organization_id=organization_id,
            source_type=source_type,
            source_id=source_id,
            chunk_id=source_id,
            embedding_model=embedding_model,
            embedding_vector=embedding_vector,
            content_hash=content_hash,
            embedding_metadata=metadata,
        )
        self._db.add(embedding)
        await self._db.flush()
        return embedding

    async def search(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        query_vector: list[float],
        limit: int,
    ) -> list[tuple[Embedding, float]]:
        distance = Embedding.embedding_vector.cosine_distance(query_vector)
        result = await self._db.execute(
            select(Embedding, distance)
            .where(
                Embedding.tenant_id == tenant_id,
                Embedding.organization_id == organization_id,
            )
            .order_by(distance.asc())
            .limit(limit)
        )
        return [(row[0], row[1]) for row in result.all()]
