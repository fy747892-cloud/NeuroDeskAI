from uuid import UUID

from pydantic import BaseModel, Field


class SemanticSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1_000)
    limit: int = Field(default=10, ge=1, le=50)


class SearchResultOut(BaseModel):
    source_type: str
    source_id: UUID
    title: str
    snippet: str
    score: float


class ReindexSummaryOut(BaseModel):
    processed: int
    created: int
    updated: int
    skipped: int
