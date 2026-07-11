import uuid

from fastapi import APIRouter, Depends, Query, Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import require_permission
from app.core.errors import NotFoundError
from app.core.permissions import Permission
from app.core.rate_limit import RateLimiter
from app.db.redis import get_redis
from app.db.session import get_db
from app.modules.audit.repository import AuditRepository
from app.modules.email.models import EmailAccount, EmailMessageMetadata
from app.modules.email.repository import EmailAccountRepository, EmailMessageRepository
from app.modules.email.schemas import (
    ConnectStartOut,
    EmailAccountOut,
    EmailMessageOut,
    SyncSummaryOut,
)
from app.modules.email.service import EmailIntegrationService
from app.modules.users.models import User

router = APIRouter(prefix="/email", tags=["email"])


async def _start_connect(
    provider: str,
    current_user: User,
    db: AsyncSession,
    redis: Redis,
) -> ConnectStartOut:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    result = await EmailIntegrationService(db, redis).start_connect(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        provider=provider,
    )
    await db.commit()
    return ConnectStartOut(**result)


async def _complete_connect(
    provider: str,
    request: Request,
    code: str,
    state: str,
    db: AsyncSession,
    redis: Redis,
) -> EmailAccount:
    account = await EmailIntegrationService(db, redis).complete_connect(
        provider=provider, state=state, code=code
    )
    await AuditRepository(db).record(
        tenant_id=account.tenant_id,
        actor_id=account.user_id,
        action="email.connected",
        entity_type="email_account",
        entity_id=account.id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata={"provider": account.provider},
    )
    await db.commit()
    return account


@router.post("/gmail/connect", response_model=ConnectStartOut)
async def start_gmail_connect(
    current_user: User = Depends(require_permission(Permission.EMAIL_CONNECT)),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> ConnectStartOut:
    return await _start_connect("gmail", current_user, db, redis)


@router.get("/gmail/callback", response_model=EmailAccountOut)
async def gmail_callback(
    request: Request,
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> EmailAccount:
    return await _complete_connect("gmail", request, code, state, db, redis)


@router.post("/outlook/connect", response_model=ConnectStartOut)
async def start_outlook_connect(
    current_user: User = Depends(require_permission(Permission.EMAIL_CONNECT)),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> ConnectStartOut:
    return await _start_connect("outlook", current_user, db, redis)


@router.get("/outlook/callback", response_model=EmailAccountOut)
async def outlook_callback(
    request: Request,
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> EmailAccount:
    return await _complete_connect("outlook", request, code, state, db, redis)


@router.get("/accounts", response_model=list[EmailAccountOut])
async def list_email_accounts(
    current_user: User = Depends(require_permission(Permission.EMAIL_READ)),
    db: AsyncSession = Depends(get_db),
) -> list[EmailAccount]:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")
    return await EmailAccountRepository(db).list_accounts(
        tenant_id=current_user.tenant_id, organization_id=current_user.organization_id
    )


@router.post("/accounts/{account_id}/revoke", response_model=EmailAccountOut)
async def revoke_email_account(
    account_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_permission(Permission.EMAIL_CONNECT)),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> EmailAccount:
    account = await _get_current_account(db, current_user, account_id)
    account = await EmailIntegrationService(db, redis).revoke(account=account)
    await AuditRepository(db).record(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action="email.revoked",
        entity_type="email_account",
        entity_id=account.id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    return account


@router.post("/accounts/{account_id}/sync", response_model=SyncSummaryOut)
async def sync_email_account(
    account_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_permission(Permission.EMAIL_CONNECT)),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> SyncSummaryOut:
    account = await _get_current_account(db, current_user, account_id)

    await RateLimiter(redis).check(
        key=f"email_sync:{current_user.tenant_id}:{account.provider}", limit=5, window_seconds=60
    )

    summary = await EmailIntegrationService(db, redis).sync_messages(account=account)
    await AuditRepository(db).record(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action="email.sync_run",
        entity_type="email_account",
        entity_id=account.id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata=summary,
    )
    await db.commit()
    return SyncSummaryOut(**summary)


@router.post("/accounts/{account_id}/refresh-token", response_model=EmailAccountOut)
async def refresh_email_account_token(
    account_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_permission(Permission.EMAIL_CONNECT)),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> EmailAccount:
    account = await _get_current_account(db, current_user, account_id)
    account = await EmailIntegrationService(db, redis).refresh_access_token(account=account)
    await AuditRepository(db).record(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action="email.token_refreshed",
        entity_type="email_account",
        entity_id=account.id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    return account


@router.get("/accounts/{account_id}/messages", response_model=list[EmailMessageOut])
async def list_email_messages(
    account_id: uuid.UUID,
    current_user: User = Depends(require_permission(Permission.EMAIL_READ)),
    db: AsyncSession = Depends(get_db),
) -> list[EmailMessageMetadata]:
    account = await _get_current_account(db, current_user, account_id)
    return await EmailMessageRepository(db).list_for_account(email_account_id=account.id)


async def _get_current_account(
    db: AsyncSession, current_user: User, account_id: uuid.UUID
) -> EmailAccount:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")
    account = await EmailAccountRepository(db).get_by_id(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        account_id=account_id,
    )
    if account is None:
        raise NotFoundError("Email account not found.")
    return account
