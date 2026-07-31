import logging

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.core.rate_limit import RateLimiter
from app.db.redis import get_redis
from app.db.session import get_db
from app.modules.feedback.repository import FeedbackRepository
from app.modules.feedback.schemas import FeedbackCreate, FeedbackOut
from app.modules.users.models import User

logger = logging.getLogger("neurodesk.feedback")

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackOut, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    body: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> FeedbackOut:
    await RateLimiter(redis).check(
        key=f"feedback-submit:{current_user.id}", limit=5, window_seconds=3600
    )

    logger.info(
        "feedback category=%s user_id=%s tenant_id=%s url=%s",
        body.category,
        current_user.id,
        current_user.tenant_id,
        body.page_url,
    )

    feedback = await FeedbackRepository(db).create(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        category=body.category,
        message=body.message,
        page_url=body.page_url,
    )
    await db.commit()
    return FeedbackOut.model_validate(feedback)
