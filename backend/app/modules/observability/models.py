import uuid

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPKMixin


class ClientErrorReport(UUIDPKMixin, TimestampMixin, Base):
    """Self-hosted crash/error log for the frontend — a Sentry substitute
    that doesn't require a third-party account."""

    __tablename__ = "client_error_reports"

    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    message: Mapped[str] = mapped_column(String(2000), nullable=False)
    stack: Mapped[str | None] = mapped_column(Text, nullable=True)
    digest: Mapped[str | None] = mapped_column(String(255), nullable=True)
    url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    context: Mapped[str | None] = mapped_column(String(255), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
