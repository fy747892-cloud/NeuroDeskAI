import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.feedback.models import Feedback


class FeedbackRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def create(
        self,
        *,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        category: str,
        message: str,
        page_url: str | None,
    ) -> Feedback:
        feedback = Feedback(
            tenant_id=tenant_id,
            user_id=user_id,
            category=category,
            message=message,
            page_url=page_url,
        )
        self._db.add(feedback)
        await self._db.flush()
        return feedback

    async def list_recent(self, *, tenant_id: uuid.UUID, limit: int = 100) -> list[Feedback]:
        result = await self._db.execute(
            select(Feedback)
            .where(Feedback.tenant_id == tenant_id)
            .order_by(Feedback.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
