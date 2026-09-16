"""create trial_criteria table

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-13

Owned by: ai-service.
Depends on: trials (0002).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0004"
down_revision: Union[str, Sequence[str], None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "trial_criteria",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("trial_id", sa.UUID(), nullable=False),
        sa.Column("criteria_type", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["trial_id"], ["trials.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_trial_criteria_criteria_type"),
        "trial_criteria",
        ["criteria_type"],
    )
    op.create_index(
        op.f("ix_trial_criteria_trial_id"), "trial_criteria", ["trial_id"]
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_trial_criteria_trial_id"), table_name="trial_criteria"
    )
    op.drop_index(
        op.f("ix_trial_criteria_criteria_type"), table_name="trial_criteria"
    )
    op.drop_table("trial_criteria")
