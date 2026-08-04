import uuid

from fastapi import APIRouter, Depends, Request, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import require_permission
from app.core.errors import NotFoundError
from app.core.permissions import Permission
from app.core.rate_limit import RateLimiter
from app.db.redis import get_redis
from app.db.session import get_db
from app.modules.audit.repository import AuditRepository
from app.modules.lead_forms.models import LeadForm
from app.modules.lead_forms.repository import LeadFormRepository
from app.modules.lead_forms.schemas import (
    LeadFormOut,
    LeadFormPublicOut,
    LeadFormSubmitIn,
    LeadFormUpdate,
)
from app.modules.lead_forms.service import LeadFormService
from app.modules.organizations.repository import OrganizationRepository
from app.modules.users.models import User

router = APIRouter(prefix="/lead-forms", tags=["lead-forms"])


@router.post("", response_model=LeadFormOut, status_code=status.HTTP_201_CREATED)
async def create_lead_form(
    request: Request,
    current_user: User = Depends(require_permission(Permission.ORGANIZATIONS_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> LeadForm:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")
    lead_form = await LeadFormService(db).create_for_organization(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        owner_user_id=current_user.id,
    )
    await _record_lead_form_audit(db, request, current_user, "lead_form.created", lead_form)
    await db.commit()
    return lead_form


@router.get("/me", response_model=LeadFormOut)
async def get_my_lead_form(
    current_user: User = Depends(require_permission(Permission.ORGANIZATIONS_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> LeadForm:
    return await _get_current_lead_form(db, current_user)


@router.patch("/{lead_form_id}", response_model=LeadFormOut)
async def update_lead_form(
    lead_form_id: uuid.UUID,
    body: LeadFormUpdate,
    request: Request,
    current_user: User = Depends(require_permission(Permission.ORGANIZATIONS_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> LeadForm:
    lead_form = await _get_current_lead_form(db, current_user)
    if lead_form.id != lead_form_id:
        raise NotFoundError("Lead form not found.")
    lead_form = await LeadFormService(db).set_active(lead_form=lead_form, is_active=body.is_active)
    await _record_lead_form_audit(db, request, current_user, "lead_form.updated", lead_form)
    await db.commit()
    return lead_form


@router.post("/{lead_form_id}/rotate-token", response_model=LeadFormOut)
async def rotate_lead_form_token(
    lead_form_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_permission(Permission.ORGANIZATIONS_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> LeadForm:
    lead_form = await _get_current_lead_form(db, current_user)
    if lead_form.id != lead_form_id:
        raise NotFoundError("Lead form not found.")
    lead_form = await LeadFormService(db).rotate_token(lead_form=lead_form)
    await _record_lead_form_audit(db, request, current_user, "lead_form.token_rotated", lead_form)
    await db.commit()
    return lead_form


async def _get_current_lead_form(db: AsyncSession, current_user: User) -> LeadForm:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")
    lead_form = await LeadFormRepository(db).get_by_organization(
        tenant_id=current_user.tenant_id, organization_id=current_user.organization_id
    )
    if lead_form is None:
        raise NotFoundError("Lead form not found.")
    return lead_form


async def _record_lead_form_audit(
    db: AsyncSession, request: Request, current_user: User, action: str, lead_form: LeadForm
) -> None:
    await AuditRepository(db).record(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action=action,
        entity_type="lead_form",
        entity_id=lead_form.id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


# --- Public endpoints (no auth: hit by anonymous visitors of the embedded/shared form) ---


@router.get("/public/{public_token}", response_model=LeadFormPublicOut)
async def get_public_lead_form(public_token: str, db: AsyncSession = Depends(get_db)) -> LeadFormPublicOut:
    lead_form = await LeadFormRepository(db).get_by_token(public_token=public_token)
    if lead_form is None:
        raise NotFoundError("Lead form not found.")
    organization = await OrganizationRepository(db).get_by_id(
        tenant_id=lead_form.tenant_id, organization_id=lead_form.organization_id
    )
    if organization is None:
        raise NotFoundError("Lead form not found.")
    return LeadFormPublicOut(organization_name=organization.name, is_active=lead_form.is_active)


@router.post("/public/{public_token}/submit", status_code=status.HTTP_204_NO_CONTENT)
async def submit_public_lead_form(
    public_token: str,
    body: LeadFormSubmitIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> None:
    lead_form = await LeadFormRepository(db).get_by_token(public_token=public_token)
    if lead_form is None or not lead_form.is_active:
        raise NotFoundError("Lead form not found.")

    client_ip = request.client.host if request.client else "unknown"
    rate_limiter = RateLimiter(redis)
    await rate_limiter.check(
        key=f"lead_form_submit:{lead_form.organization_id}", limit=20, window_seconds=3600
    )
    await rate_limiter.check(key=f"lead_form_submit_ip:{client_ip}", limit=5, window_seconds=3600)

    await LeadFormService(db).submit_lead(
        lead_form=lead_form,
        full_name=body.full_name,
        email=body.email,
        phone=body.phone,
        company=body.company,
        message=body.message,
        website=body.website,
    )
    await db.commit()
