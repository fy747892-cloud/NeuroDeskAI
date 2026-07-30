from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.core.rate_limit import RateLimiter
from app.db.redis import get_redis
from app.db.session import get_db
from app.modules.auth.schemas import (
    AcceptInviteRequest,
    ForgotPasswordRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
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
        email=body.email, password=body.password, device=_device_context(request)
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
