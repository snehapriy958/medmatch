import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.hospital import Hospital
    from app.models.patient import Patient
    from app.models.trial import Trial


class Match(Base):
    """
    Persisted eligibility-evaluation result linking a patient to a
    clinical trial.

    Owned by: ai-service.

    FK deletion policy is deliberately RESTRICT (not CASCADE) on all
    three relationships: a Match becomes part of the clinical review
    and approval history, so deleting a patient, trial, or hospital
    must never silently destroy that history. Callers that need to
    delete a patient/trial with existing matches must handle that
    explicitly (out of scope for this phase — no service layer is
    added here; matching routes and MatchingService are unchanged).
    """

    __tablename__ = "matches"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )

    trial_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trials.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )

    hospital_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("hospitals.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )

    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    overall_status: Mapped[str] = mapped_column(
        String(50),
        index=True,
        nullable=False,
    )

    # Preserves the existing EligibilityResponse shape: flat lists of
    # criterion-description strings (see app/schemas/eligibility.py —
    # matched_criteria / failed_criteria / missing_information are
    # already list[str] there). No concrete reason found to diverge;
    # keeping the shapes identical avoids a translation layer if/when
    # this is wired up in a future phase.
    matched_criteria: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )

    failed_criteria: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )

    missing_information: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )

    explanation: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    model_version: Mapped[str] = mapped_column(
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

    # These are normal navigation relationships (not viewonly=True) —
    # they can be traversed in both directions (match.patient,
    # patient.matches, etc.) and participate in the default
    # "merge, save-update" cascade like any other relationship. What
    # they do NOT do is cascade a delete: no "all, delete-orphan" or
    # "delete" is configured on any of the four `matches` relationship
    # declarations (here and on Patient/Trial/Hospital), and each of
    # those four sets passive_deletes=True so the DB's RESTRICT
    # constraint on patient_id/trial_id/hospital_id is the sole
    # authority on whether a delete is allowed — never SQLAlchemy's
    # own cascade logic. This was verified empirically (not assumed):
    # without passive_deletes=True, SQLAlchemy's unit-of-work tries to
    # UPDATE the child FK to NULL before the parent DELETE runs, which
    # raises a confusing NOT NULL error instead of a clean RESTRICT
    # violation, since patient_id/trial_id/hospital_id are all
    # non-nullable.
    #
    # Note for the future service layer: nothing at this model layer
    # enforces that hospital_id on a Match actually matches the
    # hospital_id of the Patient/Trial it references — a Match row
    # could in principle be constructed with a hospital_id that
    # disagrees with its patient/trial's own hospital_id, and the DB
    # would not reject it. That consistency check belongs in whichever
    # service eventually creates Match rows (mirroring the
    # _validate_user_hospital-style checks already used elsewhere in
    # this project), not here — this phase adds no such service.
    patient: Mapped["Patient"] = relationship(
        back_populates="matches",
        lazy="selectin",
    )

    trial: Mapped["Trial"] = relationship(
        back_populates="matches",
        lazy="selectin",
    )

    hospital: Mapped["Hospital"] = relationship(
        back_populates="matches",
        lazy="joined",
    )
