import uuid

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import RedirectResponse
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import require_permission
from app.core.config import settings
from app.core.errors import NotFoundError
from app.core.permissions import Permission
from app.core.rate_limit import RateLimiter
from app.db.redis import get_redis
from app.db.session import get_db
from app.modules.audit.repository import AuditRepository
from app.modules.calendar.models import CalendarAccount
from app.modules.calendar.repository import CalendarAccountRepository
from app.modules.calendar.schemas import (
    CalendarAccountOut,
    CalendarConnectStartOut,
    CalendarSyncSummaryOut,
)
from app.modules.calendar.service import CalendarService
from app.modules.users.models import User

router = APIRouter(prefix="/calendar", tags=["calendar"])


def _wants_html(request: Request) -> bool:
    return "text/html" in request.headers.get("accept", "")


def _callback_response(
    request: Request, account: CalendarAccount
) -> CalendarAccount | RedirectResponse:
    if _wants_html(request):
        return RedirectResponse(f"{settings.frontend_base_url}/ayarlar?connected=google_calendar")
    return account


@router.get("/accounts", response_model=list[CalendarAccountOut])
async def list_calendar_accounts(
    current_user: User = Depends(require_permission(Permission.CALENDAR_READ)),
    db: AsyncSession = Depends(get_db),
) -> list[CalendarAccount]:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")
    return await CalendarAccountRepository(db).list_accounts(
        tenant_id=current_user.tenant_id, organization_id=current_user.organization_id
    )


@router.post("/google/connect", response_model=CalendarConnectStartOut)
async def start_google_calendar_connect(
    return_to: str | None = Query(default=None),
    current_user: User = Depends(require_permission(Permission.CALENDAR_CONNECT)),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> CalendarConnectStartOut:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    result = await CalendarService(db, redis).start_connect(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        provider="google",
        return_to=return_to,
    )
    await db.commit()
    return CalendarConnectStartOut(**result)


@router.get("/google/callback", response_model=CalendarAccountOut)
async def google_calendar_callback(
    request: Request,
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> CalendarAccount | RedirectResponse:
    account, _return_to = await CalendarService(db, redis).complete_connect(
        provider="google", state=state, code=code
    )
    await AuditRepository(db).record(
        tenant_id=account.tenant_id,
        actor_id=account.user_id,
        action="calendar.connected",
        entity_type="calendar_account",
        entity_id=account.id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata={"provider": account.provider},
    )
    await db.commit()
    return _callback_response(request, account)


@router.post("/accounts/{account_id}/revoke", response_model=CalendarAccountOut)
async def revoke_calendar_account(
    account_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_permission(Permission.CALENDAR_CONNECT)),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> CalendarAccount:
    account = await _get_current_account(db, current_user, account_id)
    account = await CalendarService(db, redis).revoke(account=account)
    await AuditRepository(db).record(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action="calendar.revoked",
        entity_type="calendar_account",
        entity_id=account.id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    return account


@router.post("/accounts/{account_id}/sync", response_model=CalendarSyncSummaryOut)
async def sync_calendar_account(
    account_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_permission(Permission.CALENDAR_CONNECT)),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> CalendarSyncSummaryOut:
    account = await _get_current_account(db, current_user, account_id)

    await RateLimiter(redis).check(
        key=f"calendar_sync:{current_user.tenant_id}:{account.provider}", limit=5, window_seconds=60
    )

    summary = await CalendarService(db, redis).sync_events(account=account)
    await AuditRepository(db).record(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action="calendar.sync_run",
        entity_type="calendar_account",
        entity_id=account.id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata=summary,
    )
    await db.commit()
    return CalendarSyncSummaryOut(**summary)


async def _get_current_account(
    db: AsyncSession, current_user: User, account_id: uuid.UUID
) -> CalendarAccount:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")
    account = await CalendarAccountRepository(db).get_by_id(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        account_id=account_id,
    )
    if account is None:
        raise NotFoundError("Calendar account not found.")
    return account
