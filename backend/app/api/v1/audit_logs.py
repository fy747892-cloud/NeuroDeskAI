from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import require_permission
from app.core.permissions import Permission
from app.db.session import get_db
from app.modules.audit.models import AuditLog
from app.modules.audit.repository import AuditRepository
from app.modules.audit.schemas import AuditLogOut
from app.modules.users.models import User

router = APIRouter(prefix="/audit-logs", tags=["audit"])


@router.get("", response_model=list[AuditLogOut])
async def list_audit_logs(
    limit: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(require_permission(Permission.AUDIT_READ)),
    db: AsyncSession = Depends(get_db),
) -> list[AuditLog]:
    return await AuditRepository(db).list_for_tenant(
        tenant_id=current_user.tenant_id,
        limit=limit,
    )
