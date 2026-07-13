"""priority voice contact links

Revision ID: 1d9a2c3b4e5f
Revises: d00a487861e2
Create Date: 2026-07-11 22:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "1d9a2c3b4e5f"
down_revision: Union[str, Sequence[str], None] = "d00a487861e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tasks", sa.Column("contact_id", sa.UUID(), nullable=True))
    op.create_index(op.f("ix_tasks_contact_id"), "tasks", ["contact_id"], unique=False)
    op.create_foreign_key(
        "fk_tasks_contact_id_contacts",
        "tasks",
        "contacts",
        ["contact_id"],
        ["id"],
    )

    op.add_column("appointments", sa.Column("contact_id", sa.UUID(), nullable=True))
    op.create_index(
        op.f("ix_appointments_contact_id"), "appointments", ["contact_id"], unique=False
    )
    op.create_foreign_key(
        "fk_appointments_contact_id_contacts",
        "appointments",
        "contacts",
        ["contact_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_appointments_contact_id_contacts", "appointments", type_="foreignkey")
    op.drop_index(op.f("ix_appointments_contact_id"), table_name="appointments")
    op.drop_column("appointments", "contact_id")

    op.drop_constraint("fk_tasks_contact_id_contacts", "tasks", type_="foreignkey")
    op.drop_index(op.f("ix_tasks_contact_id"), table_name="tasks")
    op.drop_column("tasks", "contact_id")
