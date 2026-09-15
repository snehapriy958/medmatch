"""create trials table

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-13

Owned by: ai-service.
Depends on: hospitals (external table, owned and migrated by
auth-service via Flyway — must exist before this migration runs).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002"
down_revision: Union[str, Sequence[str], None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "trials",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("brief_summary", sa.Text(), nullable=True),
        sa.Column("condition", sa.String(length=255), nullable=True),
        sa.Column("phase", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=100), nullable=True),
        sa.Column("hospital_id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["hospital_id"], ["hospitals.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "hospital_id",
            "title",
            "condition",
            "phase",
            name="uq_trials_hospital_title_condition_phase",
        ),
    )
    op.create_index(op.f("ix_trials_condition"), "trials", ["condition"])
    op.create_index(op.f("ix_trials_hospital_id"), "trials", ["hospital_id"])
    op.create_index(op.f("ix_trials_status"), "trials", ["status"])
    op.create_index(op.f("ix_trials_title"), "trials", ["title"])


def downgrade() -> None:
    op.drop_index(op.f("ix_trials_title"), table_name="trials")
    op.drop_index(op.f("ix_trials_status"), table_name="trials")
    op.drop_index(op.f("ix_trials_hospital_id"), table_name="trials")
    op.drop_index(op.f("ix_trials_condition"), table_name="trials")
    op.drop_table("trials")
