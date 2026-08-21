from uuid import UUID

from sqlalchemy.orm import Session

from app.models.patient_note_embedding import PatientNoteEmbedding
from app.repositories.base_repository import BaseRepository


class PatientNoteEmbeddingRepository(BaseRepository):
    """
    Repository responsible for PatientNoteEmbedding database operations.
    """

    def __init__(
        self,
        db: Session,
    ) -> None:
        super().__init__(db)

    def create(
        self,
        embedding: PatientNoteEmbedding,
    ) -> PatientNoteEmbedding:
        """
        Persist a patient note embedding.
        """
        self.db.add(embedding)
        return embedding

    def get_by_note_id(
        self,
        note_id: UUID,
    ) -> PatientNoteEmbedding | None:
        """
        Retrieve an embedding by patient note ID.
        """
        return (
            self.db.query(PatientNoteEmbedding)
            .filter(
                PatientNoteEmbedding.note_id == note_id
            )
            .first()
        )