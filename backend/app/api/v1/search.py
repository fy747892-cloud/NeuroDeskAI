from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import require_permission
from app.core.errors import NotFoundError
from app.core.permissions import Permission
from app.db.session import get_db
from app.modules.audit.repository import AuditRepository
from app.modules.search.schemas import ReindexSummaryOut, SearchResultOut, SemanticSearchRequest
from app.modules.search.service import SearchService
from app.modules.users.models import User

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/semantic", response_model=list[SearchResultOut])
async def semantic_search(
    body: SemanticSearchRequest,
    current_user: User = Depends(require_permission(Permission.SEARCH_USE)),
    db: AsyncSession = Depends(get_db),
) -> list[SearchResultOut]:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    return await SearchService(db).semantic_search(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        query=body.query,
        limit=body.limit,
    )


@router.post("/reindex", response_model=ReindexSummaryOut)
async def reindex(
    request: Request,
    current_user: User = Depends(require_permission(Permission.SEARCH_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> ReindexSummaryOut:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    summary = await SearchService(db).reindex(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
    )
    await AuditRepository(db).record(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action="search.reindex_run",
        entity_type="embedding_batch",
        entity_id=current_user.organization_id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata=summary,
    )
    await db.commit()
    return ReindexSummaryOut(**summary)
