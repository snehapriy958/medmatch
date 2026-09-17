"""create matches table

Revision ID: 0008
Revises: 0007
Create Date: 2026-09-17

Owned by: ai-service.
Depends on: patients (0001), trials (0002).

Persisted eligibility-evaluation results (app/models/match.py).
FK deletion policy is RESTRICT on patient_id, trial_id, and
hospital_id — deliberately not CASCADE, since Match rows become
part of the clinical review/approval history and must not be
silently destroyed by a patient/trial/hospital deletion.

This migration is schema-only: no service or route in this phase
writes to this table yet. Matching routes, MatchingService, and
EligibilityResponse are unchanged.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0008"
down_revision: Union[str, Sequence[str], None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "matches",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("patient_id", sa.UUID(), nullable=False),
        sa.Column("trial_id", sa.UUID(), nullable=False),
        sa.Column("hospital_id", sa.UUID(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("overall_status", sa.String(length=50), nullable=False),
        sa.Column(
            "matched_criteria",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "failed_criteria",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "missing_information",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("model_version", sa.String(length=100), nullable=False),
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
            ["patient_id"], ["patients.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["trial_id"], ["trials.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["hospital_id"], ["hospitals.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_matches_patient_id"), "matches", ["patient_id"]
    )
    op.create_index(
        op.f("ix_matches_trial_id"), "matches", ["trial_id"]
    )
    op.create_index(
        op.f("ix_matches_hospital_id"), "matches", ["hospital_id"]
    )
    op.create_index(
        op.f("ix_matches_overall_status"), "matches", ["overall_status"]
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_matches_overall_status"), table_name="matches")
    op.drop_index(op.f("ix_matches_hospital_id"), table_name="matches")
    op.drop_index(op.f("ix_matches_trial_id"), table_name="matches")
    op.drop_index(op.f("ix_matches_patient_id"), table_name="matches")
    op.drop_table("matches")
