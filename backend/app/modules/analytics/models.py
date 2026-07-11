import uuid
from datetime import date as date_type

from sqlalchemy import Date, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPKMixin


class AICostLog(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "ai_cost_logs"

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    cost_amount: Mapped[float] = mapped_column(Float, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)


class AnalyticsTaskMetric(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "analytics_task_metrics"
    __table_args__ = (
        UniqueConstraint("tenant_id", "date", name="uq_analytics_task_metrics_tenant_date"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    date: Mapped[date_type] = mapped_column(Date, nullable=False, index=True)
    created_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    overdue_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class AnalyticsCallMetric(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "analytics_call_metrics"
    __table_args__ = (
        UniqueConstraint("tenant_id", "date", name="uq_analytics_call_metrics_tenant_date"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    date: Mapped[date_type] = mapped_column(Date, nullable=False, index=True)
    call_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    analyzed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class AnalyticsAppointmentMetric(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "analytics_appointment_metrics"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "date", name="uq_analytics_appointment_metrics_tenant_date"
        ),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    date: Mapped[date_type] = mapped_column(Date, nullable=False, index=True)
    completed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    upcoming_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class AnalyticsAIMetric(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "analytics_ai_metrics"
    __table_args__ = (
        UniqueConstraint("tenant_id", "date", name="uq_analytics_ai_metrics_tenant_date"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    date: Mapped[date_type] = mapped_column(Date, nullable=False, index=True)
    request_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    avg_latency_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)


class AnalyticsDailyUserStat(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "analytics_daily_user_stats"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "user_id", "date", name="uq_analytics_daily_user_stats_tenant_user_date"
        ),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    date: Mapped[date_type] = mapped_column(Date, nullable=False, index=True)
    metrics: Mapped[dict] = mapped_column(JSONB, nullable=False)
