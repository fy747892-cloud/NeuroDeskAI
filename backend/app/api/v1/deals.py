import uuid

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import require_permission
from app.core.errors import NotFoundError
from app.core.permissions import Permission
from app.db.session import get_db
from app.modules.audit.repository import AuditRepository
from app.modules.deals.models import Deal
from app.modules.deals.repository import DealRepository
from app.modules.deals.schemas import DealCreate, DealCreateFromApproval, DealOut, DealUpdate
from app.modules.deals.service import DealService
from app.modules.users.models import User

router = APIRouter(prefix="/deals", tags=["deals"])


@router.get("", response_model=list[DealOut])
async def list_deals(
    stage: str | None = None,
    current_user: User = Depends(require_permission(Permission.DEALS_READ)),
    db: AsyncSession = Depends(get_db),
) -> list[Deal]:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")
    return await DealRepository(db).list_deals(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        stage=stage,
    )


@router.post("", response_model=DealOut, status_code=status.HTTP_201_CREATED)
async def create_deal(
    body: DealCreate,
    request: Request,
    current_user: User = Depends(require_permission(Permission.DEALS_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> Deal:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    deal = await DealService(db).create_manual_deal(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        owner_user_id=current_user.id,
        title=body.title,
        description=body.description,
        value=body.value,
        currency=body.currency,
        stage=body.stage,
        expected_close_date=body.expected_close_date,
        contact_id=body.contact_id,
    )
    await _record_deal_audit(db, request, current_user, "deal.created", deal)
    await db.commit()
    return deal


@router.post("/from-approval", response_model=DealOut, status_code=status.HTTP_201_CREATED)
async def create_deal_from_approval(
    body: DealCreateFromApproval,
    request: Request,
    current_user: User = Depends(require_permission(Permission.DEALS_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> Deal:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    deal = await DealService(db).create_deal_from_approval(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        owner_user_id=current_user.id,
        approval_id=body.approval_id,
    )
    await _record_deal_audit(db, request, current_user, "deal.created_from_ai_approval", deal)
    await db.commit()
    return deal


@router.get("/{deal_id}", response_model=DealOut)
async def get_deal(
    deal_id: uuid.UUID,
    current_user: User = Depends(require_permission(Permission.DEALS_READ)),
    db: AsyncSession = Depends(get_db),
) -> Deal:
    return await _get_current_deal(db, current_user, deal_id)


@router.patch("/{deal_id}", response_model=DealOut)
async def update_deal(
    deal_id: uuid.UUID,
    body: DealUpdate,
    request: Request,
    current_user: User = Depends(require_permission(Permission.DEALS_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> Deal:
    deal = await _get_current_deal(db, current_user, deal_id)
    deal = await DealService(db).update_deal(
        deal=deal,
        title=body.title,
        description=body.description,
        value=body.value,
        currency=body.currency,
        stage=body.stage,
        expected_close_date=body.expected_close_date,
        contact_id=body.contact_id,
    )
    await _record_deal_audit(db, request, current_user, "deal.updated", deal)
    await db.commit()
    return deal


@router.delete("/{deal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deal(
    deal_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_permission(Permission.DEALS_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> None:
    deal = await _get_current_deal(db, current_user, deal_id)
    await DealService(db).delete_deal(deal=deal)
    await _record_deal_audit(db, request, current_user, "deal.deleted", deal)
    await db.commit()


async def _get_current_deal(db: AsyncSession, current_user: User, deal_id: uuid.UUID) -> Deal:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")
    deal = await DealRepository(db).get_deal(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        deal_id=deal_id,
    )
    if deal is None:
        raise NotFoundError("Deal not found.")
    return deal


async def _record_deal_audit(
    db: AsyncSession, request: Request, current_user: User, action: str, deal: Deal
) -> None:
    await AuditRepository(db).record(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action=action,
        entity_type="deal",
        entity_id=deal.id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )