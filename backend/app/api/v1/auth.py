import uuid

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import RedirectResponse
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.core.config import settings
from app.core.errors import AuthError, ForbiddenError, NotFoundError
from app.core.rate_limit import RateLimiter
from app.db.redis import get_redis
from app.db.session import get_db
from app.modules.auth import google_login
from app.modules.auth.google_login_state import GoogleLoginStateStore
from app.modules.auth.repository import AuthRepository
from app.modules.auth.schemas import (
    AcceptInviteRequest,
    ForgotPasswordRequest,
    GoogleExchangeRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    TotpDisableRequest,
    TotpSetupOut,
    TotpStatusOut,
    TotpVerifyOut,
    TotpVerifyRequest,
    UserSessionOut,
)
from app.modules.auth.service import AuthService, DeviceContext
from app.modules.users.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


def _device_context(request: Request) -> DeviceContext:
    return DeviceContext(
        device_id=request.headers.get("x-device-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    body: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    service = AuthService(db)
    return await service.register_user(
        email=body.email,
        password=body.password,
        display_name=body.display_name,
        device=_device_context(request),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> TokenResponse:
    limiter = RateLimiter(redis)
    client_ip = request.client.host if request.client else "unknown"
    await limiter.check(key=f"login:{client_ip}:{body.email.lower()}", limit=5, window_seconds=60)

    service = AuthService(db)
    return await service.authenticate(
        email=body.email,
        password=body.password,
        device=_device_context(request),
        totp_code=body.totp_code,
        recovery_code=body.recovery_code,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    body: RefreshRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    service = AuthService(db)
    return await service.rotate_refresh_token(
        raw_refresh_token=body.refresh_token, device=_device_context(request)
    )


@router.post("/logout", status_code=204)
async def logout(body: RefreshRequest, db: AsyncSession = Depends(get_db)) -> None:
    service = AuthService(db)
    await service.logout(raw_refresh_token=body.refresh_token)


@router.post("/logout-all", status_code=204)
async def logout_all(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = AuthService(db)
    await service.logout_all(user_id=current_user.id)


@router.post("/forgot-password", status_code=204)
async def forgot_password(
    body: ForgotPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> None:
    limiter = RateLimiter(redis)
    client_ip = request.client.host if request.client else "unknown"
    await limiter.check(key=f"forgot-password:{client_ip}:{body.email.lower()}", limit=3, window_seconds=300)

    service = AuthService(db)
    await service.request_password_reset(email=body.email)


@router.post("/reset-password", status_code=204)
async def reset_password(
    body: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> None:
    service = AuthService(db)
    await service.reset_password(raw_token=body.token, new_password=body.new_password)


@router.get("/sessions", response_model=list[UserSessionOut])
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list:
    return await AuthRepository(db).list_active_sessions(user_id=current_user.id)


@router.delete("/sessions/{session_id}", status_code=204)
async def revoke_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    repository = AuthRepository(db)
    session = await repository.get_session_by_id(session_id=session_id)
    if session is None:
        raise NotFoundError("Session not found.")
    if session.user_id != current_user.id:
        raise ForbiddenError("You can only manage your own sessions.")

    await repository.revoke_session(session_id)
    await db.commit()


@router.get("/2fa/status", response_model=TotpStatusOut)
async def totp_status(current_user: User = Depends(get_current_user)) -> TotpStatusOut:
    return TotpStatusOut(enabled=current_user.totp_enabled)


@router.post("/2fa/setup", response_model=TotpSetupOut)
async def totp_setup(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TotpSetupOut:
    service = AuthService(db)
    return await service.setup_totp(user=current_user)


@router.post("/2fa/verify", response_model=TotpVerifyOut)
async def totp_verify(
    body: TotpVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TotpVerifyOut:
    service = AuthService(db)
    return await service.verify_totp(user=current_user, code=body.code)


@router.post("/2fa/disable", status_code=204)
async def totp_disable(
    body: TotpDisableRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = AuthService(db)
    await service.disable_totp(user=current_user, code=body.code)


@router.get("/google/login")
async def google_login_start(redis: Redis = Depends(get_redis)) -> dict:
    provider = google_login.get_google_login_provider()
    state = await GoogleLoginStateStore(redis).generate_state()
    return {"authorize_url": provider.build_authorize_url(state=state)}


@router.get("/google/callback")
async def google_login_callback(
    request: Request,
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> RedirectResponse:
    store = GoogleLoginStateStore(redis)

    if error or not code or not state or not await store.consume_state(state):
        return RedirectResponse(f"{settings.frontend_base_url}/giris?google_error=1")

    try:
        provider = google_login.get_google_login_provider()
        userinfo = await provider.exchange_code(code)
        if not userinfo.get("email") or not userinfo.get("email_verified"):
            return RedirectResponse(f"{settings.frontend_base_url}/giris?google_error=1")

        tokens = await AuthService(db).login_with_google(
            email=userinfo["email"],
            display_name=userinfo.get("name") or userinfo["email"].split("@")[0],
            device=_device_context(request),
        )
    except AuthError as auth_error:
        reason = "totp_required" if "two-factor" in str(auth_error) else "1"
        return RedirectResponse(f"{settings.frontend_base_url}/giris?google_error={reason}")
    except RuntimeError:
        return RedirectResponse(f"{settings.frontend_base_url}/giris?google_error=1")

    login_code = await store.store_tokens(tokens.model_dump())
    return RedirectResponse(f"{settings.frontend_base_url}/giris?login_code={login_code}")


@router.post("/google/exchange", response_model=TokenResponse)
async def google_login_exchange(
    body: GoogleExchangeRequest,
    redis: Redis = Depends(get_redis),
) -> TokenResponse:
    payload = await GoogleLoginStateStore(redis).consume_tokens(body.login_code)
    if payload is None:
        raise AuthError("This sign-in link has expired or was already used.")
    return TokenResponse(**payload)


@router.post("/accept-invite", response_model=TokenResponse)
async def accept_invite(
    body: AcceptInviteRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    service = AuthService(db)
    return await service.accept_invite(
        raw_token=body.token,
        password=body.password,
        display_name=body.display_name,
        device=_device_context(request),
    )
