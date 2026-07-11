"""sprint6 task tables

Revision ID: f2c8d9e1a0b6
Revises: e9b7c6a5d4f3
Create Date: 2026-07-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "f2c8d9e1a0b6"
down_revision: Union[str, Sequence[str], None] = "e9b7c6a5d4f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "tasks",
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("priority", sa.String(length=50), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("source_id", sa.UUID(), nullable=True),
        sa.Column("ai_action_approval_id", sa.UUID(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["ai_action_approval_id"], ["ai_action_approvals.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ai_action_approval_id"),
    )
    op.create_index(op.f("ix_tasks_ai_action_approval_id"), "tasks", ["ai_action_approval_id"])
    op.create_index(op.f("ix_tasks_due_at"), "tasks", ["due_at"])
    op.create_index(op.f("ix_tasks_organization_id"), "tasks", ["organization_id"])
    op.create_index(op.f("ix_tasks_priority"), "tasks", ["priority"])
    op.create_index(op.f("ix_tasks_source_id"), "tasks", ["source_id"])
    op.create_index(op.f("ix_tasks_source_type"), "tasks", ["source_type"])
    op.create_index(op.f("ix_tasks_status"), "tasks", ["status"])
    op.create_index(op.f("ix_tasks_tenant_id"), "tasks", ["tenant_id"])
    op.create_index(op.f("ix_tasks_user_id"), "tasks", ["user_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_tasks_user_id"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_tenant_id"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_status"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_source_type"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_source_id"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_priority"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_organization_id"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_due_at"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_ai_action_approval_id"), table_name="tasks")
    op.drop_table("tasks")
