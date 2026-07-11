from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import require_permission
from app.core.errors import NotFoundError
from app.core.permissions import Permission
from app.db.session import get_db
from app.modules.priority.schemas import PriorityQueueOut
from app.modules.priority.service import PriorityService
from app.modules.users.models import User

router = APIRouter(prefix="/priority", tags=["priority"])


@router.get("/queue", response_model=PriorityQueueOut)
async def get_priority_queue(
    limit: int = Query(default=25, ge=1, le=100),
    current_user: User = Depends(require_permission(Permission.TASKS_READ)),
    db: AsyncSession = Depends(get_db),
) -> PriorityQueueOut:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")
    return await PriorityService(db).build_queue(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        limit=limit,
    )
