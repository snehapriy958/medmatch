"""create patients table

Revision ID: 0001
Revises:
Create Date: 2026-09-13

Owned by: ai-service.
Depends on: hospitals (external table, owned and migrated by
auth-service via Flyway — must exist before this migration runs).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "patients",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("mrn", sa.String(length=50), nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("age", sa.Integer(), nullable=False),
        sa.Column("gender", sa.String(length=20), nullable=False),
        sa.Column("diagnosis", sa.String(length=255), nullable=False),
        sa.Column("cancer_type", sa.String(length=255), nullable=True),
        sa.Column("stage", sa.String(length=50), nullable=True),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("match_count", sa.Integer(), nullable=False),
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
            "hospital_id", "mrn", name="uq_patient_hospital_mrn"
        ),
    )
    op.create_index(
        op.f("ix_patients_hospital_id"), "patients", ["hospital_id"]
    )
    op.create_index(op.f("ix_patients_mrn"), "patients", ["mrn"])


def downgrade() -> None:
    op.drop_index(op.f("ix_patients_mrn"), table_name="patients")
    op.drop_index(op.f("ix_patients_hospital_id"), table_name="patients")
    op.drop_table("patients")
