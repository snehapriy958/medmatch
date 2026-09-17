from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.hospital import Hospital
    from app.models.match import Match
    from app.models.patient_note import PatientNote


class Patient(Base):
    __tablename__ = "patients"

    __table_args__ = (
        UniqueConstraint(
            "hospital_id",
            "mrn",
            name="uq_patient_hospital_mrn",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    mrn: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    age: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    gender: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    diagnosis: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    cancer_type: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    stage: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="ACTIVE",
        nullable=False,
    )

    match_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    hospital_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("hospitals.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
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
        back_populates="patients",
        lazy="joined",
    )

    notes: Mapped[list["PatientNote"]] = relationship(
        back_populates="patient",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # No cascade here — Match.patient_id is RESTRICT, not CASCADE,
    # since a Match becomes part of the clinical review/approval
    # history and must not be silently destroyed by patient deletion.
    # passive_deletes=True so the DB's RESTRICT constraint is the
    # sole authority on patient deletion: without it, SQLAlchemy's
    # unit-of-work would first try to UPDATE Match.patient_id to
    # NULL (since patient_id is NOT NULL, this raises a confusing
    # "NOT NULL constraint failed" from that UPDATE) before the
    # DELETE ever reaches the DB's RESTRICT constraint. Verified
    # empirically against both configurations before choosing this.
    matches: Mapped[list["Match"]] = relationship(
        back_populates="patient",
        passive_deletes=True,
        lazy="selectin",
    )