from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import require_permission
from app.core.errors import NotFoundError
from app.core.permissions import Permission
from app.db.session import get_db
from app.modules.calendar.models import CalendarAccount
from app.modules.calendar.schemas import CalendarAccountOut
from app.modules.calendar.service import CalendarService
from app.modules.users.models import User

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("/accounts", response_model=list[CalendarAccountOut])
async def list_calendar_accounts(
    current_user: User = Depends(require_permission(Permission.CALENDAR_READ)),
    db: AsyncSession = Depends(get_db),
) -> list[CalendarAccount]:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")
    return await CalendarService(db).list_accounts(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
    )


@router.post(
    "/google/connect", response_model=CalendarAccountOut, status_code=status.HTTP_201_CREATED
)
async def connect_google_calendar(
    current_user: User = Depends(require_permission(Permission.CALENDAR_CONNECT)),
    db: AsyncSession = Depends(get_db),
) -> CalendarAccount:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    account = await CalendarService(db).connect(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        provider="google",
    )
    await db.commit()
    return account
