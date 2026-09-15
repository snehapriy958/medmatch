"""create criteria_embeddings table

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-13

Owned by: ai-service.
Depends on: trial_criteria (0004), and the `vector` Postgres extension
(enabled separately - see infra/kubernetes/postgres/postgres-init.yaml
for Kubernetes; Docker Compose must be given an equivalent step).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import pgvector.sqlalchemy


revision: str = "0005"
down_revision: Union[str, Sequence[str], None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "criteria_embeddings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("criteria_id", sa.UUID(), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["criteria_id"], ["trial_criteria.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_criteria_embeddings_criteria_id"),
        "criteria_embeddings",
        ["criteria_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_criteria_embeddings_criteria_id"),
        table_name="criteria_embeddings",
    )
    op.drop_table("criteria_embeddings")
