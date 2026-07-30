import uuid

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import require_permission
from app.core.errors import NotFoundError, ValidationAppError
from app.core.permissions import Permission
from app.db.session import get_db
from app.modules.ai.models import AIAnalysisJob
from app.modules.ai.repository import AIRepository
from app.modules.ai.schemas import AIActionApprovalOut, AIActionApproveIn, AIAnalysisJobOut
from app.modules.ai.service import AIAnalysisService
from app.modules.audit.repository import AuditRepository
from app.modules.users.consent import get_consent
from app.modules.users.models import User

router = APIRouter(prefix="/ai/analysis", tags=["ai-analysis"])
approval_router = APIRouter(prefix="/ai/approvals", tags=["ai-approvals"])


@router.post(
    "/conversations/{conversation_id}",
    response_model=AIAnalysisJobOut,
    status_code=status.HTTP_201_CREATED,
)
async def request_conversation_analysis(
    conversation_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_permission(Permission.AI_ANALYZE)),
    db: AsyncSession = Depends(get_db),
) -> AIAnalysisJob:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")
    if not get_consent(current_user)["ai_processing"]:
        raise ValidationAppError(
            "AI processing is turned off in your settings. Turn it back on in "
            "Settings to analyze conversations."
        )

    service = AIAnalysisService(db)
    job = await service.request_conversation_analysis(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        conversation_id=conversation_id,
    )
    await AuditRepository(db).record(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action="ai_analysis.requested",
        entity_type="ai_analysis_job",
        entity_id=job.id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata={"source_type": "conversation", "source_id": str(conversation_id)},
    )
    await db.commit()
    return job


@router.get("/jobs", response_model=list[AIAnalysisJobOut])
async def list_analysis_jobs(
    current_user: User = Depends(require_permission(Permission.AI_READ)),
    db: AsyncSession = Depends(get_db),
) -> list[AIAnalysisJob]:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    return await AIRepository(db).list_jobs(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
    )


@router.get("/jobs/{job_id}", response_model=AIAnalysisJobOut)
async def get_analysis_job(
    job_id: uuid.UUID,
    current_user: User = Depends(require_permission(Permission.AI_READ)),
    db: AsyncSession = Depends(get_db),
) -> AIAnalysisJob:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    job = await AIRepository(db).get_job(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        job_id=job_id,
    )
    if job is None:
        raise NotFoundError("AI analysis job not found.")
    return job


@router.post("/jobs/{job_id}/retry", response_model=AIAnalysisJobOut)
async def retry_analysis_job(
    job_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_permission(Permission.AI_ANALYZE)),
    db: AsyncSession = Depends(get_db),
) -> AIAnalysisJob:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    job = await AIAnalysisService(db).retry_job(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        job_id=job_id,
    )
    await AuditRepository(db).record(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action="ai_analysis.retried",
        entity_type="ai_analysis_job",
        entity_id=job.id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    return job


@approval_router.get("", response_model=list[AIActionApprovalOut])
async def list_action_approvals(
    status_filter: str | None = None,
    current_user: User = Depends(require_permission(Permission.AI_READ)),
    db: AsyncSession = Depends(get_db),
):
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    return await AIRepository(db).list_action_approvals(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        status=status_filter,
    )


@approval_router.get("/{approval_id}", response_model=AIActionApprovalOut)
async def get_action_approval(
    approval_id: uuid.UUID,
    current_user: User = Depends(require_permission(Permission.AI_READ)),
    db: AsyncSession = Depends(get_db),
):
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    approval = await AIRepository(db).get_action_approval(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        approval_id=approval_id,
    )
    if approval is None:
        raise NotFoundError("AI action approval not found.")
    return approval


@approval_router.post("/{approval_id}/approve", response_model=AIActionApprovalOut)
async def approve_action_approval(
    approval_id: uuid.UUID,
    payload: AIActionApproveIn,
    request: Request,
    current_user: User = Depends(require_permission(Permission.AI_ANALYZE)),
    db: AsyncSession = Depends(get_db),
):
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    approval = await AIAnalysisService(db).approve_action(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        approval_id=approval_id,
        user_id=current_user.id,
        approved_payload=payload.approved_payload,
    )
    await AuditRepository(db).record(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action="ai_action_approval.approved",
        entity_type="ai_action_approval",
        entity_id=approval.id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata={"action_type": approval.action_type, "source_id": str(approval.source_id)},
    )
    await db.commit()
    return approval


@approval_router.post("/{approval_id}/reject", response_model=AIActionApprovalOut)
async def reject_action_approval(
    approval_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_permission(Permission.AI_ANALYZE)),
    db: AsyncSession = Depends(get_db),
):
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    approval = await AIAnalysisService(db).reject_action(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        approval_id=approval_id,
        user_id=current_user.id,
    )
    await AuditRepository(db).record(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action="ai_action_approval.rejected",
        entity_type="ai_action_approval",
        entity_id=approval.id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata={"action_type": approval.action_type, "source_id": str(approval.source_id)},
    )
    await db.commit()
    return approval
