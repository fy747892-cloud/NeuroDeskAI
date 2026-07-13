import re
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics.repository import AICostLogRepository
from app.modules.billing.service import BillingService
from app.modules.voice.provider import VoiceProvider, get_voice_provider
from app.modules.voice.schemas import VoiceActionOut, VoiceCommandOut, VoiceTranscriptOut

TASK_TERMS = ("task", "todo", "follow up", "ara", "gorev", "görev", "takip")
APPOINTMENT_TERMS = ("meeting", "appointment", "schedule", "randevu", "toplanti", "toplantı")
SEARCH_TERMS = ("search", "find", "ara", "bul")
NOTE_TERMS = ("note", "not al", "not ekle")


class VoiceAssistantService:
    def __init__(self, db: AsyncSession, provider: VoiceProvider | None = None):
        self._db = db
        self._cost_logs = AICostLogRepository(db)
        self._billing = BillingService(db)
        self._provider = provider or get_voice_provider()

    async def interpret_command(
        self,
        *,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        text: str | None,
        audio_base64: str | None,
        locale: str,
    ) -> VoiceCommandOut:
        await self._billing.enforce_ai_usage_guard(tenant_id=tenant_id)

        transcript = await self._provider.transcribe(
            text=text,
            audio_base64=audio_base64,
            locale=locale,
        )
        action = self._match_action(transcript.text)
        spoken_response_text = self._build_response(action)
        spoken_response = await self._provider.synthesize(
            text=spoken_response_text,
            locale=locale,
        )
        spoken_response_audio = await self._provider.synthesize_audio(
            text=spoken_response_text,
            locale=locale,
        )

        await self._cost_logs.record(
            tenant_id=tenant_id,
            user_id=user_id,
            provider=self._provider.provider_name,
            model=self._provider.stt_model_name,
            source_type="voice_command_stt",
            input_tokens=0,
            output_tokens=max(1, len(transcript.text) // 4),
            latency_ms=0,
        )
        await self._cost_logs.record(
            tenant_id=tenant_id,
            user_id=user_id,
            provider=self._provider.provider_name,
            model=self._provider.tts_model_name,
            source_type="voice_command_tts",
            input_tokens=max(1, len(spoken_response) // 4),
            output_tokens=0,
            latency_ms=0,
        )
        await self._billing.record_ai_usage(tenant_id=tenant_id, user_id=user_id)

        return VoiceCommandOut(
            transcript=VoiceTranscriptOut(
                text=transcript.text,
                language=transcript.language,
                provider=transcript.provider,
                confidence=transcript.confidence,
            ),
            action=action,
            spoken_response=spoken_response,
            spoken_response_audio_base64=spoken_response_audio,
        )

    def _match_action(self, text: str) -> VoiceActionOut:
        normalized = text.casefold()
        if self._contains_any(normalized, APPOINTMENT_TERMS):
            return VoiceActionOut(
                intent="create_appointment",
                action_type="appointment",
                confidence=0.74,
                suggested_payload={
                    "title": self._clean_title(text),
                    "proposed_datetime": self._guess_datetime(normalized).isoformat(),
                    "description": text,
                },
            )
        if self._contains_any(normalized, TASK_TERMS):
            return VoiceActionOut(
                intent="create_task",
                action_type="task",
                confidence=0.72,
                suggested_payload={
                    "title": self._clean_title(text),
                    "description": text,
                    "priority": self._guess_priority(normalized),
                    "due_at": self._guess_datetime(normalized).isoformat(),
                },
            )
        if self._contains_any(normalized, SEARCH_TERMS):
            return VoiceActionOut(
                intent="search_workspace",
                action_type="search",
                confidence=0.64,
                suggested_payload={"query": self._clean_title(text)},
                requires_approval=False,
            )
        if self._contains_any(normalized, NOTE_TERMS):
            return VoiceActionOut(
                intent="create_note",
                action_type="note",
                confidence=0.61,
                suggested_payload={"body": text},
            )
        return VoiceActionOut(
            intent="capture_follow_up",
            action_type="task",
            confidence=0.52,
            suggested_payload={
                "title": self._clean_title(text),
                "description": text,
                "priority": self._guess_priority(normalized),
            },
        )

    def _contains_any(self, text: str, terms: tuple[str, ...]) -> bool:
        return any(term in text for term in terms)

    def _clean_title(self, text: str) -> str:
        title = re.sub(r"\s+", " ", text).strip()
        return title[:80] or "Voice command"

    def _guess_priority(self, text: str) -> str:
        if any(term in text for term in ("acil", "hemen", "urgent", "asap", "kritik")):
            return "high"
        if any(term in text for term in ("sonra", "later", "düşük", "dusuk")):
            return "low"
        return "medium"

    def _guess_datetime(self, text: str) -> datetime:
        now = datetime.now(timezone.utc)
        if any(term in text for term in ("bugün", "bugun", "today")):
            return now + timedelta(hours=2)
        if any(term in text for term in ("yarın", "yarin", "tomorrow")):
            return now + timedelta(days=1)
        if any(term in text for term in ("haftaya", "next week")):
            return now + timedelta(days=7)
        return now + timedelta(days=1)

    def _build_response(self, action: VoiceActionOut) -> str:
        if action.requires_approval:
            return f"{action.action_type} önerisini hazırladım, onay bekliyor."
        return f"{action.action_type} komutunu hazırladım."