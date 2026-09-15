from uuid import UUID

from sqlalchemy.orm import Session

from app.models.trial_embedding import TrialEmbedding
from app.repositories.base_repository import BaseRepository


class TrialEmbeddingRepository(BaseRepository):
    """
    Repository responsible for TrialEmbedding database operations.

    A trial has at most one embedding. Callers use upsert_embedding
    rather than a plain create so that re-processing a trial (or
    regenerating its embedding after an update) never produces
    duplicate rows for the same trial_id.
    """

    def __init__(
        self,
        db: Session,
    ) -> None:
        super().__init__(db)

    def get_by_trial_id(
        self,
        trial_id: UUID,
    ) -> TrialEmbedding | None:
        """
        Retrieve the embedding for a trial, if one exists.
        """
        return (
            self.db.query(TrialEmbedding)
            .filter(
                TrialEmbedding.trial_id == trial_id
            )
            .first()
        )

    def upsert_embedding(
        self,
        trial_id: UUID,
        embedding: list[float],
        model_name: str,
    ) -> TrialEmbedding:
        """
        Create or update the embedding for a trial.

        If an embedding already exists for trial_id, it is updated
        in place. Otherwise a new row is created. The caller owns
        the transaction boundary (commit/flush), consistent with
        the other embedding repositories.
        """

        existing = self.get_by_trial_id(
            trial_id
        )

        if existing is not None:
            existing.embedding = embedding
            existing.model_name = model_name

            return existing

        entity = TrialEmbedding(
            trial_id=trial_id,
            embedding=embedding,
            model_name=model_name,
        )

        self.db.add(entity)

        return entity
