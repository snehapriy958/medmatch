"""create trial_embeddings table

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-13

Owned by: ai-service.
Depends on: trials (0002), and the `vector` Postgres extension.

This is the table added in app/models/trial_embedding.py (Phase 0,
Finding 1.1). MatchingRepository.find_similar_criteria joins this
table by literal name ('trial_embeddings') and columns
('trial_id', 'embedding') - see that file's raw SQL.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import pgvector.sqlalchemy


revision: str = "0007"
down_revision: Union[str, Sequence[str], None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "trial_embeddings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("trial_id", sa.UUID(), nullable=False),
        sa.Column(
            "embedding",
            pgvector.sqlalchemy.Vector(384),
            nullable=False,
        ),
        sa.Column("model_name", sa.String(length=100), nullable=False),
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
            ["trial_id"], ["trials.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_trial_embeddings_trial_id"),
        "trial_embeddings",
        ["trial_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_trial_embeddings_trial_id"),
        table_name="trial_embeddings",
    )
    op.drop_table("trial_embeddings")
