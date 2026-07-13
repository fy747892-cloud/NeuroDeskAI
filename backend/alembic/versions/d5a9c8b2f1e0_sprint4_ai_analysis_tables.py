"""sprint4 ai analysis tables

Revision ID: d5a9c8b2f1e0
Revises: c1f4e0a2d6b7
Create Date: 2026-07-10 23:59:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "d5a9c8b2f1e0"
down_revision: Union[str, Sequence[str], None] = "c1f4e0a2d6b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "ai_prompt_versions",
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("version", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ai_prompt_versions_name"), "ai_prompt_versions", ["name"])
    op.create_index(op.f("ix_ai_prompt_versions_status"), "ai_prompt_versions", ["status"])

    op.create_table(
        "ai_analysis_jobs",
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("requested_by", sa.UUID(), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("source_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("queued_at", sa.DateTime(timezone=True), server_default="now()", nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(["requested_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ai_analysis_jobs_organization_id"), "ai_analysis_jobs", ["organization_id"])
    op.create_index(op.f("ix_ai_analysis_jobs_requested_by"), "ai_analysis_jobs", ["requested_by"])
    op.create_index(op.f("ix_ai_analysis_jobs_source_id"), "ai_analysis_jobs", ["source_id"])
    op.create_index(op.f("ix_ai_analysis_jobs_source_type"), "ai_analysis_jobs", ["source_type"])
    op.create_index(op.f("ix_ai_analysis_jobs_status"), "ai_analysis_jobs", ["status"])
    op.create_index(op.f("ix_ai_analysis_jobs_tenant_id"), "ai_analysis_jobs", ["tenant_id"])

    op.create_table(
        "ai_analysis_results",
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("job_id", sa.UUID(), nullable=False),
        sa.Column("result_type", sa.String(length=100), nullable=False),
        sa.Column("result_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("prompt_version_id", sa.UUID(), nullable=False),
        sa.Column("model_config", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(["job_id"], ["ai_analysis_jobs.id"]),
        sa.ForeignKeyConstraint(["prompt_version_id"], ["ai_prompt_versions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ai_analysis_results_job_id"), "ai_analysis_results", ["job_id"])
    op.create_index(
        op.f("ix_ai_analysis_results_prompt_version_id"),
        "ai_analysis_results",
        ["prompt_version_id"],
    )
    op.create_index(
        op.f("ix_ai_analysis_results_result_type"), "ai_analysis_results", ["result_type"]
    )
    op.create_index(op.f("ix_ai_analysis_results_tenant_id"), "ai_analysis_results", ["tenant_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_ai_analysis_results_tenant_id"), table_name="ai_analysis_results")
    op.drop_index(op.f("ix_ai_analysis_results_result_type"), table_name="ai_analysis_results")
    op.drop_index(op.f("ix_ai_analysis_results_prompt_version_id"), table_name="ai_analysis_results")
    op.drop_index(op.f("ix_ai_analysis_results_job_id"), table_name="ai_analysis_results")
    op.drop_table("ai_analysis_results")

    op.drop_index(op.f("ix_ai_analysis_jobs_tenant_id"), table_name="ai_analysis_jobs")
    op.drop_index(op.f("ix_ai_analysis_jobs_status"), table_name="ai_analysis_jobs")
    op.drop_index(op.f("ix_ai_analysis_jobs_source_type"), table_name="ai_analysis_jobs")
    op.drop_index(op.f("ix_ai_analysis_jobs_source_id"), table_name="ai_analysis_jobs")
    op.drop_index(op.f("ix_ai_analysis_jobs_requested_by"), table_name="ai_analysis_jobs")
    op.drop_index(op.f("ix_ai_analysis_jobs_organization_id"), table_name="ai_analysis_jobs")
    op.drop_table("ai_analysis_jobs")

    op.drop_index(op.f("ix_ai_prompt_versions_status"), table_name="ai_prompt_versions")
    op.drop_index(op.f("ix_ai_prompt_versions_name"), table_name="ai_prompt_versions")
    op.drop_table("ai_prompt_versions")
