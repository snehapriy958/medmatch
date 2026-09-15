"""create patient_notes table

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-13

Owned by: ai-service.
Depends on: patients (0001).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003"
down_revision: Union[str, Sequence[str], None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "patient_notes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("patient_id", sa.UUID(), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"], ["patients.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_patient_notes_patient_id"), "patient_notes", ["patient_id"]
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_patient_notes_patient_id"), table_name="patient_notes"
    )
    op.drop_table("patient_notes")
