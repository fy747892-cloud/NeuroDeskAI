"""sprint5 ai action approvals

Revision ID: e9b7c6a5d4f3
Revises: d5a9c8b2f1e0
Create Date: 2026-07-10 23:59:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "e9b7c6a5d4f3"
down_revision: Union[str, Sequence[str], None] = "d5a9c8b2f1e0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "ai_action_approvals",
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("requested_by", sa.UUID(), nullable=False),
        sa.Column("decided_by", sa.UUID(), nullable=True),
        sa.Column("analysis_result_id", sa.UUID(), nullable=False),
        sa.Column("action_type", sa.String(length=50), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("source_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("suggested_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("approved_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(["analysis_result_id"], ["ai_analysis_results.id"]),
        sa.ForeignKeyConstraint(["decided_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["requested_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ai_action_approvals_action_type"), "ai_action_approvals", ["action_type"])
    op.create_index(
        op.f("ix_ai_action_approvals_analysis_result_id"),
        "ai_action_approvals",
        ["analysis_result_id"],
    )
    op.create_index(op.f("ix_ai_action_approvals_decided_by"), "ai_action_approvals", ["decided_by"])
    op.create_index(
        op.f("ix_ai_action_approvals_organization_id"),
        "ai_action_approvals",
        ["organization_id"],
    )
    op.create_index(op.f("ix_ai_action_approvals_requested_by"), "ai_action_approvals", ["requested_by"])
    op.create_index(op.f("ix_ai_action_approvals_source_id"), "ai_action_approvals", ["source_id"])
    op.create_index(op.f("ix_ai_action_approvals_source_type"), "ai_action_approvals", ["source_type"])
    op.create_index(op.f("ix_ai_action_approvals_status"), "ai_action_approvals", ["status"])
    op.create_index(op.f("ix_ai_action_approvals_tenant_id"), "ai_action_approvals", ["tenant_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_ai_action_approvals_tenant_id"), table_name="ai_action_approvals")
    op.drop_index(op.f("ix_ai_action_approvals_status"), table_name="ai_action_approvals")
    op.drop_index(op.f("ix_ai_action_approvals_source_type"), table_name="ai_action_approvals")
    op.drop_index(op.f("ix_ai_action_approvals_source_id"), table_name="ai_action_approvals")
    op.drop_index(op.f("ix_ai_action_approvals_requested_by"), table_name="ai_action_approvals")
    op.drop_index(op.f("ix_ai_action_approvals_organization_id"), table_name="ai_action_approvals")
    op.drop_index(op.f("ix_ai_action_approvals_decided_by"), table_name="ai_action_approvals")
    op.drop_index(op.f("ix_ai_action_approvals_analysis_result_id"), table_name="ai_action_approvals")
    op.drop_index(op.f("ix_ai_action_approvals_action_type"), table_name="ai_action_approvals")
    op.drop_table("ai_action_approvals")
