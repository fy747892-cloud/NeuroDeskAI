import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.attributes import set_committed_value

from app.modules.conversations.models import (
    Call,
    CallTranscription,
    Conversation,
    ConversationParticipant,
)


class ConversationRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def create_conversation(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        title: str,
        source_type: str = "manual",
        participant_names: list[str] | None = None,
    ) -> Conversation:
        conversation = Conversation(
            tenant_id=tenant_id,
            organization_id=organization_id,
            user_id=user_id,
            title=title,
            source_type=source_type,
            status="active",
        )
        self._db.add(conversation)
        await self._db.flush()

        for display_name in participant_names or []:
            self._db.add(
                ConversationParticipant(
                    tenant_id=tenant_id,
                    conversation_id=conversation.id,
                    participant_type="manual",
                    display_name=display_name,
                )
            )
        await self._db.flush()
        return conversation

    async def list_conversations(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        limit: int | None = None,
        search: str | None = None,
    ) -> list[Conversation]:
        statement = (
            select(Conversation)
            .where(
                Conversation.tenant_id == tenant_id,
                Conversation.organization_id == organization_id,
                Conversation.is_deleted.is_(False),
            )
            .order_by(Conversation.created_at.desc())
        )
        if search is not None:
            statement = statement.where(Conversation.title.ilike(f"%{search}%"))
        if limit is not None:
            statement = statement.limit(limit)
        result = await self._db.execute(statement)
        return list(result.scalars().all())

    async def get_conversation(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        conversation_id: uuid.UUID,
    ) -> Conversation | None:
        result = await self._db.execute(
            select(Conversation)
            .options(
                selectinload(Conversation.participants),
                selectinload(Conversation.calls).selectinload(Call.transcriptions),
            )
            .where(
                Conversation.tenant_id == tenant_id,
                Conversation.organization_id == organization_id,
                Conversation.id == conversation_id,
                Conversation.is_deleted.is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def update_conversation(
        self,
        *,
        conversation: Conversation,
        title: str | None = None,
        status: str | None = None,
    ) -> Conversation:
        if title is not None:
            conversation.title = title
        if status is not None:
            conversation.status = status
        await self._db.flush()
        return conversation

    async def add_participant(
        self,
        *,
        tenant_id: uuid.UUID,
        conversation_id: uuid.UUID,
        display_name: str,
        participant_type: str = "manual",
        participant_id: uuid.UUID | None = None,
    ) -> ConversationParticipant:
        participant = ConversationParticipant(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            participant_type=participant_type,
            participant_id=participant_id,
            display_name=display_name,
        )
        self._db.add(participant)
        await self._db.flush()
        return participant

    async def soft_delete_conversation(self, *, conversation: Conversation) -> None:
        conversation.is_deleted = True
        conversation.deleted_at = datetime.now(timezone.utc)
        conversation.status = "deleted"
        await self._db.flush()

    async def create_call_with_transcription(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        title: str,
        transcript_text: str,
        participant_names: list[str] | None = None,
        call_direction: str | None = None,
        phone_number: str | None = None,
        started_at: datetime | None = None,
        duration_seconds: int | None = None,
        language: str | None = None,
    ) -> tuple[Conversation, Call, CallTranscription]:
        conversation = await self.create_conversation(
            tenant_id=tenant_id,
            organization_id=organization_id,
            user_id=user_id,
            title=title,
            source_type="call",
            participant_names=participant_names,
        )
        call = Call(
            tenant_id=tenant_id,
            conversation_id=conversation.id,
            call_direction=call_direction,
            phone_number=phone_number,
            started_at=started_at,
            duration_seconds=duration_seconds,
            status="completed",
        )
        self._db.add(call)
        await self._db.flush()

        transcription = CallTranscription(
            tenant_id=tenant_id,
            call_id=call.id,
            transcript_text=transcript_text,
            language=language,
            status="completed",
        )
        self._db.add(transcription)
        await self._db.flush()
        set_committed_value(call, "transcriptions", [transcription])
        return conversation, call, transcription

    async def list_calls(self, *, tenant_id: uuid.UUID, organization_id: uuid.UUID) -> list[Call]:
        result = await self._db.execute(
            select(Call)
            .options(selectinload(Call.transcriptions))
            .join(Conversation, Conversation.id == Call.conversation_id)
            .where(
                Call.tenant_id == tenant_id,
                Conversation.organization_id == organization_id,
                Call.is_deleted.is_(False),
                Conversation.is_deleted.is_(False),
            )
            .order_by(Call.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_call(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        call_id: uuid.UUID,
    ) -> Call | None:
        result = await self._db.execute(
            select(Call)
            .options(selectinload(Call.transcriptions))
            .join(Conversation, Conversation.id == Call.conversation_id)
            .where(
                Call.tenant_id == tenant_id,
                Conversation.organization_id == organization_id,
                Call.id == call_id,
                Call.is_deleted.is_(False),
                Conversation.is_deleted.is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def update_call(
        self,
        *,
        call: Call,
        call_direction: str | None = None,
        phone_number: str | None = None,
        started_at: datetime | None = None,
        duration_seconds: int | None = None,
        status: str | None = None,
    ) -> Call:
        if call_direction is not None:
            call.call_direction = call_direction
        if phone_number is not None:
            call.phone_number = phone_number
        if started_at is not None:
            call.started_at = started_at
        if duration_seconds is not None:
            call.duration_seconds = duration_seconds
        if status is not None:
            call.status = status
        await self._db.flush()
        return call

    async def soft_delete_call(self, *, call: Call) -> None:
        call.is_deleted = True
        call.deleted_at = datetime.now(timezone.utc)
        call.status = "deleted"
        await self._db.flush()
