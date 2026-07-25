import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.criteria_embedding import CriteriaEmbedding
    from app.models.trial import Trial


class TrialCriteria(Base):
    __tablename__ = "trial_criteria"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    trial_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trials.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    criteria_type: Mapped[str] = mapped_column(
        String(50),
        index=True,
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    trial: Mapped["Trial"] = relationship(
        back_populates="criteria",
        lazy="selectin",
    )

    embedding: Mapped["CriteriaEmbedding"] = relationship(
        back_populates="criterion",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )