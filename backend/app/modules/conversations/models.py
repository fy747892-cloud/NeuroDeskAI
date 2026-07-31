import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPKMixin

# Placeholder title the frontend sends when a call is recorded from the web
# mic flow (see conversations-view.tsx). AI analysis replaces it with a
# summary-derived title once analysis completes, as long as the user hasn't
# already renamed the conversation to something else.
DEFAULT_WEB_RECORDING_TITLE = "Webden kaydedilen görüşme"


class Conversation(UUIDPKMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "conversations"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, default="manual")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active", index=True)

    participants: Mapped[list["ConversationParticipant"]] = relationship(
        back_populates="conversation"
    )
    calls: Mapped[list["Call"]] = relationship(back_populates="conversation")


class ConversationParticipant(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "conversation_participants"

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True
    )
    participant_type: Mapped[str] = mapped_column(String(50), nullable=False, default="manual")
    participant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)

    conversation: Mapped[Conversation] = relationship(back_populates="participants")


class Call(UUIDPKMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "calls"

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True
    )
    call_direction: Mapped[str | None] = mapped_column(String(50), nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="completed", index=True)

    conversation: Mapped[Conversation] = relationship(back_populates="calls")
    transcriptions: Mapped[list["CallTranscription"]] = relationship(back_populates="call")


class CallTranscription(UUIDPKMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "call_transcriptions"

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    call_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("calls.id"), nullable=False, index=True
    )
    transcript_text: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str | None] = mapped_column(String(20), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="completed", index=True)

    call: Mapped[Call] = relationship(back_populates="transcriptions")
