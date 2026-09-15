from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.trial import Trial


class TrialEmbedding(Base):
    """
    Trial-level semantic embedding.

    Represents the clinical identity of an entire trial (title,
    condition, phase, and criteria summary) and is used during
    first-stage candidate trial retrieval in MatchingRepository.

    This is distinct from CriteriaEmbedding, which embeds individual
    criteria. A trial has at most one TrialEmbedding, upserted
    whenever the trial or its criteria change.
    """

    __tablename__ = "trial_embeddings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    trial_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trials.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )

    embedding: Mapped[list[float]] = mapped_column(
        Vector(384),
        nullable=False,
    )

    model_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    trial: Mapped["Trial"] = relationship(
        back_populates="embedding",
        lazy="selectin",
    )
