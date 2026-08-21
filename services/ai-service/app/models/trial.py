import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.hospital import Hospital
    from app.models.trial_criteria import TrialCriteria


class Trial(Base):
    __tablename__ = "trials"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    title: Mapped[str] = mapped_column(
        String(500),
        index=True,
        nullable=False,
    )

    brief_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    condition: Mapped[str | None] = mapped_column(
        String(255),
        index=True,
        nullable=True,
    )

    phase: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    status: Mapped[str | None] = mapped_column(
        String(100),
        index=True,
        nullable=True,
    )

    hospital_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "hospitals.id",
            ondelete="RESTRICT",
        ),
        index=True,
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

    hospital: Mapped["Hospital"] = relationship(
        back_populates="trials",
        lazy="joined",
    )

    criteria: Mapped[list["TrialCriteria"]] = relationship(
        back_populates="trial",
        cascade="all, delete-orphan",
        lazy="selectin",
    )