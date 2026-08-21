from uuid import UUID
import logging

from app.cache.cache_keys import CacheKeys
from app.cache.cache_service import CacheService
from app.config.settings import settings
from app.metrics.metrics import (
    EMBEDDING_CACHE_HITS,
    EMBEDDING_CACHE_MISSES,
)
from app.embeddings.model import EmbeddingModel
from app.models.criteria_embedding import CriteriaEmbedding
from app.models.patient_note_embedding import PatientNoteEmbedding
from app.repositories.criteria_embedding_repository import (
    CriteriaEmbeddingRepository,
)
from app.repositories.patient_note_embedding_repository import (
    PatientNoteEmbeddingRepository,
)

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service responsible for generating and storing embeddings.
    """

    def __init__(
        self,
        criteria_repository: CriteriaEmbeddingRepository,
        patient_note_repository: PatientNoteEmbeddingRepository,
    ) -> None:
        self.criteria_repository = criteria_repository
        self.patient_note_repository = patient_note_repository
        self.model = EmbeddingModel()
        self.cache = CacheService()

    def generate_embedding(
        self,
        text: str,
    ) -> list[float]:
        """
        Generate an embedding for the given text.

        Embeddings are cached in Redis to avoid repeated model
        inference for identical input.
        """

        if not text.strip():
            raise ValueError(
                "Text for embedding cannot be empty."
            )

        cache_key = CacheKeys.embedding(text)

        cached_embedding = self.cache.get(cache_key)

        if cached_embedding is not None:
            EMBEDDING_CACHE_HITS.inc()

            logger.info(
                "Embedding cache HIT: %s",
                cache_key,
            )
            return cached_embedding

        EMBEDDING_CACHE_MISSES.inc()

        logger.info(
            "Embedding cache MISS: %s",
            cache_key,
        )

        embedding = self.model.encode(text)

        self.cache.set(
            key=cache_key,
            value=embedding,
            ttl=settings.EMBEDDING_CACHE_TTL,
        )

        return embedding

    def create_trial_embedding(
        self,
        criteria_id: UUID,
        text: str,
    ) -> CriteriaEmbedding:
        """
        Generate and persist an embedding for a trial criterion.
        """

        embedding = self.generate_embedding(text)

        entity = CriteriaEmbedding(
            criteria_id=criteria_id,
            embedding=embedding,
            model_name=EmbeddingModel.MODEL_NAME,
        )

        try:
            self.criteria_repository.create_embedding(entity)
            self.criteria_repository.commit()
            self.criteria_repository.refresh(entity)

            return entity

        except Exception:
            self.criteria_repository.rollback()

            logger.exception(
                "Failed to create embedding for criteria %s.",
                criteria_id,
            )

            raise

    def create_patient_note_embedding(
        self,
        note_id: UUID,
        text: str,
    ) -> PatientNoteEmbedding:
        """
        Generate and persist an embedding for a patient note.
        """

        embedding = self.generate_embedding(text)

        entity = PatientNoteEmbedding(
            note_id=note_id,
            embedding=embedding,
            model_name=EmbeddingModel.MODEL_NAME,
        )

        try:
            self.patient_note_repository.create(entity)
            self.patient_note_repository.commit()
            self.patient_note_repository.refresh(entity)

            return entity

        except Exception:
            self.patient_note_repository.rollback()

            logger.exception(
                "Failed to create embedding for patient note %s.",
                note_id,
            )

            raise