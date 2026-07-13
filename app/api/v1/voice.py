from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import require_permission
from app.core.errors import NotFoundError
from app.core.permissions import Permission
from app.db.session import get_db
from app.modules.users.models import User
from app.modules.voice.schemas import VoiceCommandIn, VoiceCommandOut
from app.modules.voice.service import VoiceAssistantService

router = APIRouter(prefix="/voice", tags=["voice"])


@router.post("/commands/interpret", response_model=VoiceCommandOut)
async def interpret_voice_command(
    body: VoiceCommandIn,
    current_user: User = Depends(require_permission(Permission.AI_ANALYZE)),
    db: AsyncSession = Depends(get_db),
) -> VoiceCommandOut:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    result = await VoiceAssistantService(db).interpret_command(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        text=body.text,
        audio_base64=body.audio_base64,
        locale=body.locale,
    )
    await db.commit()
    return result