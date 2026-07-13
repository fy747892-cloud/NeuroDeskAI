"""sprint3 conversation call tables

Revision ID: c1f4e0a2d6b7
Revises: b8f2c7d1a9e4
Create Date: 2026-07-10 23:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "c1f4e0a2d6b7"
down_revision: Union[str, Sequence[str], None] = "b8f2c7d1a9e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "conversations",
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_conversations_organization_id"), "conversations", ["organization_id"])
    op.create_index(op.f("ix_conversations_status"), "conversations", ["status"])
    op.create_index(op.f("ix_conversations_tenant_id"), "conversations", ["tenant_id"])
    op.create_index(op.f("ix_conversations_user_id"), "conversations", ["user_id"])

    op.create_table(
        "conversation_participants",
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("conversation_id", sa.UUID(), nullable=False),
        sa.Column("participant_type", sa.String(length=50), nullable=False),
        sa.Column("participant_id", sa.UUID(), nullable=True),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_conversation_participants_conversation_id"),
        "conversation_participants",
        ["conversation_id"],
    )
    op.create_index(
        op.f("ix_conversation_participants_tenant_id"), "conversation_participants", ["tenant_id"]
    )

    op.create_table(
        "calls",
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("conversation_id", sa.UUID(), nullable=False),
        sa.Column("call_direction", sa.String(length=50), nullable=True),
        sa.Column("phone_number", sa.String(length=64), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_calls_conversation_id"), "calls", ["conversation_id"])
    op.create_index(op.f("ix_calls_status"), "calls", ["status"])
    op.create_index(op.f("ix_calls_tenant_id"), "calls", ["tenant_id"])

    op.create_table(
        "call_transcriptions",
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("call_id", sa.UUID(), nullable=False),
        sa.Column("transcript_text", sa.Text(), nullable=False),
        sa.Column("language", sa.String(length=20), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["call_id"], ["calls.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_call_transcriptions_call_id"), "call_transcriptions", ["call_id"])
    op.create_index(op.f("ix_call_transcriptions_status"), "call_transcriptions", ["status"])
    op.create_index(op.f("ix_call_transcriptions_tenant_id"), "call_transcriptions", ["tenant_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_call_transcriptions_tenant_id"), table_name="call_transcriptions")
    op.drop_index(op.f("ix_call_transcriptions_status"), table_name="call_transcriptions")
    op.drop_index(op.f("ix_call_transcriptions_call_id"), table_name="call_transcriptions")
    op.drop_table("call_transcriptions")

    op.drop_index(op.f("ix_calls_tenant_id"), table_name="calls")
    op.drop_index(op.f("ix_calls_status"), table_name="calls")
    op.drop_index(op.f("ix_calls_conversation_id"), table_name="calls")
    op.drop_table("calls")

    op.drop_index(
        op.f("ix_conversation_participants_tenant_id"), table_name="conversation_participants"
    )
    op.drop_index(
        op.f("ix_conversation_participants_conversation_id"),
        table_name="conversation_participants",
    )
    op.drop_table("conversation_participants")

    op.drop_index(op.f("ix_conversations_user_id"), table_name="conversations")
    op.drop_index(op.f("ix_conversations_tenant_id"), table_name="conversations")
    op.drop_index(op.f("ix_conversations_status"), table_name="conversations")
    op.drop_index(op.f("ix_conversations_organization_id"), table_name="conversations")
    op.drop_table("conversations")
