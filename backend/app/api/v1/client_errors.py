import logging

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_optional_user
from app.core.rate_limit import RateLimiter
from app.db.redis import get_redis
from app.db.session import get_db
from app.modules.observability.models import ClientErrorReport
from app.modules.observability.repository import ObservabilityRepository
from app.modules.observability.schemas import ClientErrorReportIn, ClientErrorReportOut
from app.modules.users.models import User

logger = logging.getLogger("neurodesk.client_errors")

router = APIRouter(prefix="/client-errors", tags=["observability"])


@router.post("", status_code=status.HTTP_204_NO_CONTENT)
async def report_client_error(
    body: ClientErrorReportIn,
    request: Request,
    current_user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> None:
    client_ip = request.client.host if request.client else "unknown"
    # Generous but bounded: this endpoint has no auth requirement by design
    # (errors can happen on the login page), so it needs its own throttle
    # independent of any per-user quota.
    await RateLimiter(redis).check(key=f"client-error-report:{client_ip}", limit=30, window_seconds=60)

    logger.error(
        "client_error context=%s message=%s url=%s digest=%s user_id=%s",
        body.context,
        body.message,
        body.url,
        body.digest,
        current_user.id if current_user else None,
    )

    await ObservabilityRepository(db).create(
        tenant_id=current_user.tenant_id if current_user else None,
        user_id=current_user.id if current_user else None,
        message=body.message,
        stack=body.stack,
        digest=body.digest,
        url=body.url,
        context=body.context,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()


@router.get("", response_model=list[ClientErrorReportOut])
async def list_client_errors(
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ClientErrorReport]:
    return await ObservabilityRepository(db).list_recent(limit=min(limit, 500))
