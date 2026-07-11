import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.ai.models import AIActionApproval, AIAnalysisJob, AIAnalysisResult, AIPromptVersion


class AIRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_or_create_prompt_version(self, *, name: str, version: str) -> AIPromptVersion:
        result = await self._db.execute(
            select(AIPromptVersion).where(
                AIPromptVersion.name == name,
                AIPromptVersion.version == version,
                AIPromptVersion.status == "active",
            )
        )
        prompt = result.scalar_one_or_none()
        if prompt is not None:
            return prompt

        prompt = AIPromptVersion(
            name=name,
            version=version,
            description="Mock conversation analysis prompt for Sprint 4.",
            status="active",
        )
        self._db.add(prompt)
        await self._db.flush()
        return prompt

    async def create_job(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        requested_by: uuid.UUID,
        source_type: str,
        source_id: uuid.UUID,
    ) -> AIAnalysisJob:
        job = AIAnalysisJob(
            tenant_id=tenant_id,
            organization_id=organization_id,
            requested_by=requested_by,
            source_type=source_type,
            source_id=source_id,
            status="queued",
            attempts=0,
        )
        self._db.add(job)
        await self._db.flush()
        return job

    async def get_job(
        self, *, tenant_id: uuid.UUID, organization_id: uuid.UUID, job_id: uuid.UUID
    ) -> AIAnalysisJob | None:
        result = await self._db.execute(
            select(AIAnalysisJob)
            .options(selectinload(AIAnalysisJob.results))
            .where(
                AIAnalysisJob.tenant_id == tenant_id,
                AIAnalysisJob.organization_id == organization_id,
                AIAnalysisJob.id == job_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_jobs(
        self, *, tenant_id: uuid.UUID, organization_id: uuid.UUID
    ) -> list[AIAnalysisJob]:
        result = await self._db.execute(
            select(AIAnalysisJob)
            .options(selectinload(AIAnalysisJob.results))
            .where(
                AIAnalysisJob.tenant_id == tenant_id,
                AIAnalysisJob.organization_id == organization_id,
            )
            .order_by(AIAnalysisJob.created_at.desc())
        )
        return list(result.scalars().all())

    async def mark_processing(self, *, job: AIAnalysisJob) -> None:
        job.status = "processing"
        job.attempts += 1
        job.started_at = datetime.now(timezone.utc)
        job.error_message = None
        await self._db.flush()

    async def mark_completed(self, *, job: AIAnalysisJob) -> None:
        job.status = "completed"
        job.completed_at = datetime.now(timezone.utc)
        await self._db.flush()

    async def mark_failed(self, *, job: AIAnalysisJob, error_message: str) -> None:
        job.status = "failed"
        job.error_message = error_message
        job.completed_at = datetime.now(timezone.utc)
        await self._db.flush()

    async def reset_for_retry(self, *, job: AIAnalysisJob) -> None:
        job.status = "queued"
        job.error_message = None
        job.started_at = None
        job.completed_at = None
        await self._db.flush()

    async def create_result(
        self,
        *,
        tenant_id: uuid.UUID,
        job_id: uuid.UUID,
        result_type: str,
        result_payload: dict,
        prompt_version_id: uuid.UUID,
        model_config: dict | None = None,
    ) -> AIAnalysisResult:
        result = AIAnalysisResult(
            tenant_id=tenant_id,
            job_id=job_id,
            result_type=result_type,
            result_payload=result_payload,
            prompt_version_id=prompt_version_id,
            model_config=model_config,
        )
        self._db.add(result)
        await self._db.flush()
        return result

    async def create_action_approval(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        requested_by: uuid.UUID,
        analysis_result_id: uuid.UUID,
        action_type: str,
        source_type: str,
        source_id: uuid.UUID,
        suggested_payload: dict,
        confidence_score: float | None = None,
    ) -> AIActionApproval:
        approval = AIActionApproval(
            tenant_id=tenant_id,
            organization_id=organization_id,
            requested_by=requested_by,
            analysis_result_id=analysis_result_id,
            action_type=action_type,
            source_type=source_type,
            source_id=source_id,
            status="pending",
            suggested_payload=suggested_payload,
            confidence_score=confidence_score,
        )
        self._db.add(approval)
        await self._db.flush()
        return approval

    async def list_action_approvals(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        status: str | None = None,
    ) -> list[AIActionApproval]:
        statement = select(AIActionApproval).where(
            AIActionApproval.tenant_id == tenant_id,
            AIActionApproval.organization_id == organization_id,
        )
        if status is not None:
            statement = statement.where(AIActionApproval.status == status)
        result = await self._db.execute(statement.order_by(AIActionApproval.created_at.desc()))
        return list(result.scalars().all())

    async def get_action_approval(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        approval_id: uuid.UUID,
    ) -> AIActionApproval | None:
        result = await self._db.execute(
            select(AIActionApproval).where(
                AIActionApproval.tenant_id == tenant_id,
                AIActionApproval.organization_id == organization_id,
                AIActionApproval.id == approval_id,
            )
        )
        return result.scalar_one_or_none()
