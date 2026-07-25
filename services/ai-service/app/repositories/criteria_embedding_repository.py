from uuid import UUID

from sqlalchemy.orm import Session

from app.models.criteria_embedding import CriteriaEmbedding
from app.repositories.base_repository import BaseRepository


class CriteriaEmbeddingRepository(BaseRepository):
    """
    Handles all database operations for criterion embeddings.
    """

    def __init__(
        self,
        db: Session,
    ) -> None:
        super().__init__(db)

    def create_embedding(
        self,
        embedding: CriteriaEmbedding,
    ) -> CriteriaEmbedding:
        self.db.add(embedding)
        return embedding

    def get_by_criteria_id(
        self,
        criteria_id: UUID,
    ) -> CriteriaEmbedding | None:
        return (
            self.db.query(CriteriaEmbedding)
            .filter(
                CriteriaEmbedding.criteria_id == criteria_id
            )
            .first()
        )