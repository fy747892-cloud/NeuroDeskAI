import re
from datetime import datetime, timedelta, timezone

from app.modules.voice.provider import MockVoiceProvider, VoiceProvider
from app.modules.voice.schemas import VoiceActionOut, VoiceCommandOut, VoiceTranscriptOut

TASK_TERMS = ("task", "todo", "follow up", "ara", "gorev", "görev", "takip")
APPOINTMENT_TERMS = ("meeting", "appointment", "schedule", "randevu", "toplanti", "toplantı")
SEARCH_TERMS = ("search", "find", "ara", "bul")
NOTE_TERMS = ("note", "not al", "not ekle")


class VoiceAssistantService:
    def __init__(self, provider: VoiceProvider | None = None):
        self._provider = provider or MockVoiceProvider()

    async def interpret_command(
        self,
        *,
        text: str | None,
        audio_base64: str | None,
        locale: str,
    ) -> VoiceCommandOut:
        transcript = await self._provider.transcribe(
            text=text,
            audio_base64=audio_base64,
            locale=locale,
        )
        action = self._match_action(transcript.text)
        spoken_response = await self._provider.synthesize(
            text=self._build_response(action),
            locale=locale,
        )
        return VoiceCommandOut(
            transcript=VoiceTranscriptOut(
                text=transcript.text,
                language=transcript.language,
                provider=transcript.provider,
                confidence=transcript.confidence,
            ),
            action=action,
            spoken_response=spoken_response,
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
