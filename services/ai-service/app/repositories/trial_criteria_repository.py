from uuid import UUID

from sqlalchemy.orm import Session

from app.models.trial_criteria import TrialCriteria
from app.repositories.base_repository import BaseRepository


class TrialCriteriaRepository(BaseRepository):
    """
    Repository for trial criteria.
    """

    def __init__(self, db: Session):
        super().__init__(db)

    def create(
        self,
        criterion: TrialCriteria,
    ) -> TrialCriteria:
        self.db.add(criterion)
        return criterion

    def get_by_id(
        self,
        criterion_id: UUID,
    ) -> TrialCriteria | None:
        return (
            self.db.query(TrialCriteria)
            .filter(TrialCriteria.id == criterion_id)
            .first()
        )

    def list_by_trial(
        self,
        trial_id: UUID,
    ) -> list[TrialCriteria]:
        return (
            self.db.query(TrialCriteria)
            .filter(TrialCriteria.trial_id == trial_id)
            .order_by(TrialCriteria.criteria_type)
            .all()
        )