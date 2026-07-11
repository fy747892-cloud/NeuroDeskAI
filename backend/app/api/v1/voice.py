from fastapi import APIRouter, Depends

from app.api.v1.deps import require_permission
from app.core.permissions import Permission
from app.modules.users.models import User
from app.modules.voice.schemas import VoiceCommandIn, VoiceCommandOut
from app.modules.voice.service import VoiceAssistantService

router = APIRouter(prefix="/voice", tags=["voice"])


@router.post("/commands/interpret", response_model=VoiceCommandOut)
async def interpret_voice_command(
    body: VoiceCommandIn,
    current_user: User = Depends(require_permission(Permission.AI_ANALYZE)),
) -> VoiceCommandOut:
    _ = current_user
    return await VoiceAssistantService().interpret_command(
        text=body.text,
        audio_base64=body.audio_base64,
        locale=body.locale,
    )
