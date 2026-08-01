"""add google calendar oauth integration

Revision ID: 5a5db55286b1
Revises: defca6de96cb
Create Date: 2026-08-01 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "5a5db55286b1"
down_revision: Union[str, Sequence[str], None] = "defca6de96cb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("calendar_accounts", sa.Column("email_address", sa.String(length=255), nullable=True))
    op.add_column("calendar_accounts", sa.Column("consent_scope", sa.String(length=255), nullable=True))
    op.add_column(
        "calendar_accounts", sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True)
    )

    op.create_table(
        "calendar_tokens",
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("calendar_account_id", sa.UUID(), nullable=False),
        sa.Column("access_token_encrypted", sa.Text(), nullable=False),
        sa.Column("refresh_token_encrypted", sa.Text(), nullable=True),
        sa.Column("scope", sa.String(length=255), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(["calendar_account_id"], ["calendar_accounts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_calendar_tokens_calendar_account_id"),
        "calendar_tokens",
        ["calendar_account_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_calendar_tokens_tenant_id"), "calendar_tokens", ["tenant_id"], unique=False
    )

    op.add_column("appointments", sa.Column("external_event_id", sa.String(length=255), nullable=True))
    op.create_index(
        op.f("ix_appointments_external_event_id"), "appointments", ["external_event_id"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_appointments_external_event_id"), table_name="appointments")
    op.drop_column("appointments", "external_event_id")

    op.drop_index(op.f("ix_calendar_tokens_tenant_id"), table_name="calendar_tokens")
    op.drop_index(op.f("ix_calendar_tokens_calendar_account_id"), table_name="calendar_tokens")
    op.drop_table("calendar_tokens")

    op.drop_column("calendar_accounts", "last_synced_at")
    op.drop_column("calendar_accounts", "consent_scope")
    op.drop_column("calendar_accounts", "email_address")
