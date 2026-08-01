"""add whatsapp messages table

Revision ID: defca6de96cb
Revises: 1187ea296d24
Create Date: 2026-08-01 12:58:46.584325

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "defca6de96cb"
down_revision: Union[str, Sequence[str], None] = "1187ea296d24"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "ai_action_approvals",
        "analysis_result_id",
        existing_type=postgresql.UUID(),
        nullable=True,
    )

    op.add_column(
        "ai_chat_messages", sa.Column("pending_action_approval_id", sa.UUID(), nullable=True)
    )
    op.create_index(
        op.f("ix_ai_chat_messages_pending_action_approval_id"),
        "ai_chat_messages",
        ["pending_action_approval_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_ai_chat_messages_pending_action_approval_id",
        "ai_chat_messages",
        "ai_action_approvals",
        ["pending_action_approval_id"],
        ["id"],
    )

    op.create_table(
        "whatsapp_messages",
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("contact_id", sa.UUID(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("to_phone_raw", sa.String(length=64), nullable=False),
        sa.Column("to_phone_normalized", sa.String(length=32), nullable=False),
        sa.Column("deep_link_url", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("source_id", sa.UUID(), nullable=True),
        sa.Column("ai_action_approval_id", sa.UUID(), nullable=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(["ai_action_approval_id"], ["ai_action_approvals.id"]),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_whatsapp_messages_ai_action_approval_id"),
        "whatsapp_messages",
        ["ai_action_approval_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_whatsapp_messages_contact_id"), "whatsapp_messages", ["contact_id"], unique=False
    )
    op.create_index(
        op.f("ix_whatsapp_messages_organization_id"),
        "whatsapp_messages",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_whatsapp_messages_source_id"), "whatsapp_messages", ["source_id"], unique=False
    )
    op.create_index(
        op.f("ix_whatsapp_messages_source_type"), "whatsapp_messages", ["source_type"], unique=False
    )
    op.create_index(
        op.f("ix_whatsapp_messages_status"), "whatsapp_messages", ["status"], unique=False
    )
    op.create_index(
        op.f("ix_whatsapp_messages_tenant_id"), "whatsapp_messages", ["tenant_id"], unique=False
    )
    op.create_index(
        op.f("ix_whatsapp_messages_user_id"), "whatsapp_messages", ["user_id"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_whatsapp_messages_user_id"), table_name="whatsapp_messages")
    op.drop_index(op.f("ix_whatsapp_messages_tenant_id"), table_name="whatsapp_messages")
    op.drop_index(op.f("ix_whatsapp_messages_status"), table_name="whatsapp_messages")
    op.drop_index(op.f("ix_whatsapp_messages_source_type"), table_name="whatsapp_messages")
    op.drop_index(op.f("ix_whatsapp_messages_source_id"), table_name="whatsapp_messages")
    op.drop_index(op.f("ix_whatsapp_messages_organization_id"), table_name="whatsapp_messages")
    op.drop_index(op.f("ix_whatsapp_messages_contact_id"), table_name="whatsapp_messages")
    op.drop_index(op.f("ix_whatsapp_messages_ai_action_approval_id"), table_name="whatsapp_messages")
    op.drop_table("whatsapp_messages")

    op.drop_constraint(
        "fk_ai_chat_messages_pending_action_approval_id",
        "ai_chat_messages",
        type_="foreignkey",
    )
    op.drop_index(
        op.f("ix_ai_chat_messages_pending_action_approval_id"), table_name="ai_chat_messages"
    )
    op.drop_column("ai_chat_messages", "pending_action_approval_id")

    op.alter_column(
        "ai_action_approvals",
        "analysis_result_id",
        existing_type=postgresql.UUID(),
        nullable=False,
    )
