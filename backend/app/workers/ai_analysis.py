import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.modules.ai.repository import AIRepository
from app.modules.ai.service import AIAnalysisService


async def process_ai_analysis_job(
    *,
    db: AsyncSession,
    tenant_id: uuid.UUID,
    organization_id: uuid.UUID,
    job_id: uuid.UUID,
) -> None:
    job = await AIRepository(db).get_job(
        tenant_id=tenant_id,
        organization_id=organization_id,
        job_id=job_id,
    )
    if job is None:
        raise NotFoundError("AI analysis job not found.")

    await AIAnalysisService(db).process_job(job=job)
    await db.commit()
