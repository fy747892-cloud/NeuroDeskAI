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
NOTE_TERMS = ("note", "not al", "not ekle", "kaydet", "not olarak")
EXTRA_TASK_TERMS = ("hatirlat", "hatırlat", "yapilacak", "yapılacak")
EXTRA_APPOINTMENT_TERMS = ("gorusme planla", "görüşme planla", "takvime ekle")
EXTRA_SEARCH_TERMS = ("listele", "goster", "göster")
COMMAND_CLEANUP_PATTERNS = (
    r"\b(bana|benim i[çc]in|l[üu]tfen)\b",
    r"\b(g[öo]rev olarak|g[öo]rev|todo|task|takip)\b",
    r"\b(randevu|toplant[ıi]|meeting|appointment|takvime ekle|planla)\b",
    r"\b(not al|not ekle|not olarak|kaydet)\b",
    r"\b(ekle|oluştur|olustur|haz[ıi]rla|hat[ıi]rlat)\b",
    r"\b(bug[üu]n|yar[ıi]n|haftaya|gelecek hafta|today|tomorrow|next week)\b",
    r"\b(acil|hemen|kritik|urgent|asap|sonra|later|d[üu]ş[üu]k|dusuk)\b",
)


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
        normalized_text = self._normalize_text(text)
        normalized = normalized_text.casefold()
        appointment_terms = APPOINTMENT_TERMS + EXTRA_APPOINTMENT_TERMS + (
            "toplantı",
            "görüşme planla",
        )
        task_terms = TASK_TERMS + EXTRA_TASK_TERMS + (
            "görev",
            "hatırlat",
            "yapılacak",
        )
        search_terms = SEARCH_TERMS + EXTRA_SEARCH_TERMS + ("göster",)

        if self._contains_any(normalized, appointment_terms):
            return VoiceActionOut(
                intent="create_appointment",
                action_type="appointment",
                confidence=0.74,
                suggested_payload={
                    "title": self._clean_title(normalized_text),
                    "proposed_datetime": self._guess_datetime(normalized).isoformat(),
                    "description": text,
                },
            )
        if self._contains_any(normalized, task_terms):
            return VoiceActionOut(
                intent="create_task",
                action_type="task",
                confidence=0.72,
                suggested_payload={
                    "title": self._clean_title(normalized_text),
                    "description": text,
                    "priority": self._guess_priority(normalized),
                    "due_at": self._guess_datetime(normalized).isoformat(),
                },
            )
        if self._contains_any(normalized, search_terms):
            return VoiceActionOut(
                intent="search_workspace",
                action_type="search",
                confidence=0.64,
                suggested_payload={"query": self._clean_title(normalized_text)},
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
                "title": self._clean_title(normalized_text),
                "description": text,
                "priority": self._guess_priority(normalized),
            },
        )

    def _contains_any(self, text: str, terms: tuple[str, ...]) -> bool:
        return any(term in text for term in terms)

    def _normalize_text(self, text: str) -> str:
        replacements = {
            "Ã¶": "ö",
            "Ã¼": "ü",
            "Ã§": "ç",
            "Ã‡": "Ç",
            "Ã–": "Ö",
            "Ãœ": "Ü",
            "ÅŸ": "ş",
            "Åž": "Ş",
            "Ä±": "ı",
            "Ä°": "İ",
            "ÄŸ": "ğ",
            "Äž": "Ğ",
        }
        normalized = text
        for broken, fixed in replacements.items():
            normalized = normalized.replace(broken, fixed)
        return normalized

    def _clean_title(self, text: str) -> str:
        title = text.casefold()
        for pattern in COMMAND_CLEANUP_PATTERNS:
            title = re.sub(pattern, " ", title, flags=re.IGNORECASE)
        for term in (
            "görev olarak",
            "görev",
            "randevu",
            "toplantı",
            "takvime ekle",
            "planla",
            "oluştur",
            "hazırla",
            "hatırlat",
            "bugün",
            "yarın",
            "haftaya",
            "gelecek hafta",
            "acil",
            "hemen",
            "kritik",
            "düşük",
            "ekle",
        ):
            title = re.sub(rf"\b{re.escape(term)}\b", " ", title, flags=re.IGNORECASE)
        title = re.sub(r"\s+", " ", title).strip(" .,-:;")
        if title:
            title = title[0].upper() + title[1:]
        else:
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
        if any(term in text for term in ("bu aksam", "bu akşam", "tonight")):
            return now.replace(hour=18, minute=0, second=0, microsecond=0)
        if any(term in text for term in ("sabah", "morning")):
            return (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
        if any(term in text for term in ("ogle", "öğle", "noon")):
            return (now + timedelta(days=1)).replace(hour=12, minute=0, second=0, microsecond=0)
        if any(term in text for term in ("aksam", "akşam", "evening")):
            return (now + timedelta(days=1)).replace(hour=18, minute=0, second=0, microsecond=0)
        if any(term in text for term in ("yarın", "yarin", "tomorrow")):
            return now + timedelta(days=1)
        if any(term in text for term in ("haftaya", "gelecek hafta", "next week")):
            return now + timedelta(days=7)
        return now + timedelta(days=1)

    def _build_response(self, action: VoiceActionOut) -> str:
        if action.requires_approval:
            return f"{action.action_type} önerisini hazırladım, onay bekliyor."
        return f"{action.action_type} komutunu hazırladım."
