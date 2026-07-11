from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import require_permission
from app.core.errors import NotFoundError
from app.core.permissions import Permission
from app.db.session import get_db
from app.modules.dashboard.schemas import DashboardOut
from app.modules.dashboard.service import DashboardService
from app.modules.users.models import User

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardOut)
async def get_dashboard(
    current_user: User = Depends(require_permission(Permission.DASHBOARD_READ)),
    db: AsyncSession = Depends(get_db),
) -> DashboardOut:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    return await DashboardService(db).build(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
    )
