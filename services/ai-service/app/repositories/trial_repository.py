from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session, selectinload

from app.models.trial import Trial
from app.models.trial_criteria import TrialCriteria


class TrialRepository:
    """
    Handles all database operations for clinical trials.
    """

    def __init__(self, db: Session):
        self.db = db

    def create_trial(self, trial: Trial) -> Trial:
        self.db.add(trial)
        return trial

    def get_trial_by_id(
        self,
        trial_id: UUID,
        hospital_id: UUID,
    ) -> Trial | None:
        return (
            self.db.query(Trial)
            .options(selectinload(Trial.criteria))
            .filter(
                Trial.id == trial_id,
                Trial.hospital_id == hospital_id,
            )
            .first()
        )

    def list_trials(
        self,
        hospital_id: UUID,
    ) -> list[Trial]:
        return (
            self.db.query(Trial)
            .filter(Trial.hospital_id == hospital_id)
            .order_by(Trial.created_at.desc())
            .all()
        )

    def delete_trial(self, trial: Trial) -> None:
        self.db.delete(trial)

    def create_criteria(
        self,
        criteria: TrialCriteria,
    ) -> TrialCriteria:
        self.db.add(criteria)
        return criteria

    def list_criteria(
        self,
        trial_id: UUID,
    ) -> list[TrialCriteria]:
        return (
            self.db.query(TrialCriteria)
            .filter(TrialCriteria.trial_id == trial_id)
            .order_by(TrialCriteria.criteria_type)
            .all()
        )

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()

    def refresh(self, instance: Any) -> None:
        self.db.refresh(instance)