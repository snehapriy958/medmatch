"""create patient_note_embeddings table

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-13

Owned by: ai-service.
Depends on: patient_notes (0003), and the `vector` Postgres extension.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import pgvector.sqlalchemy


revision: str = "0006"
down_revision: Union[str, Sequence[str], None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "patient_note_embeddings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("note_id", sa.UUID(), nullable=False),
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
            ["note_id"], ["patient_notes.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_patient_note_embeddings_note_id"),
        "patient_note_embeddings",
        ["note_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_patient_note_embeddings_note_id"),
        table_name="patient_note_embeddings",
    )
    op.drop_table("patient_note_embeddings")
