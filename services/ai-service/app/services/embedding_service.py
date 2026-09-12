import logging
from uuid import UUID

from app.cache.cache_keys import CacheKeys
from app.cache.cache_service import CacheService
from app.config.settings import settings
from app.embeddings.model import EmbeddingModel
from app.metrics.metrics import (
    EMBEDDING_CACHE_HITS,
    EMBEDDING_CACHE_MISSES,
)

from app.models.criteria_embedding import CriteriaEmbedding
from app.models.patient_note_embedding import PatientNoteEmbedding
from app.models.trial_embedding import TrialEmbedding
from app.repositories.criteria_embedding_repository import (
    CriteriaEmbeddingRepository,
)
from app.repositories.patient_note_embedding_repository import (
    PatientNoteEmbeddingRepository,
)
from app.repositories.trial_embedding_repository import (
    TrialEmbeddingRepository,
)

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service responsible for generating, caching, and storing embeddings.

    Redis caching is treated as an optimization layer. Cache failures
    must not prevent embedding generation or persistence.

    Database transaction boundaries are owned by the calling service.
    This service creates and persists embedding entities but does not
    commit or roll back transactions.
    """

    def __init__(
        self,
        criteria_repository: CriteriaEmbeddingRepository,
        patient_note_repository: PatientNoteEmbeddingRepository,
        trial_repository: TrialEmbeddingRepository,
    ) -> None:
        self.criteria_repository = criteria_repository
        self.patient_note_repository = patient_note_repository
        self.trial_repository = trial_repository
        self.model = EmbeddingModel()
        self.cache = CacheService()

    def generate_embedding(
        self,
        text: str,
    ) -> list[float]:
        """
        Generate an embedding for the given text.

        Embeddings are cached in Redis to avoid repeated model
        inference for identical normalized input.

        Cache failures do not prevent embedding generation because
        Redis is an optimization rather than a required dependency
        for embedding inference.
        """

        normalized_text = text.strip()

        if not normalized_text:
            raise ValueError(
                "Text for embedding cannot be empty."
            )

        cache_key = CacheKeys.embedding(
            normalized_text
        )

        try:
            cached_embedding = self.cache.get(
                cache_key
            )

        except Exception:
            logger.warning(
                "Embedding cache read failed for key %s. "
                "Continuing without cache.",
                cache_key,
                exc_info=True,
            )

            cached_embedding = None

        if cached_embedding is not None:

            if (
                isinstance(cached_embedding, list)
                and cached_embedding
                and all(
                    isinstance(value, (int, float))
                    for value in cached_embedding
                )
            ):
                EMBEDDING_CACHE_HITS.inc()

                logger.debug(
                    "Embedding cache hit: %s",
                    cache_key,
                )

                return [
                    float(value)
                    for value in cached_embedding
                ]

            logger.warning(
                "Invalid embedding found in cache for key %s. "
                "Regenerating embedding.",
                cache_key,
            )

        EMBEDDING_CACHE_MISSES.inc()

        logger.debug(
            "Embedding cache miss: %s",
            cache_key,
        )

        embedding = self.model.encode(
            normalized_text
        )

        if (
            not isinstance(embedding, list)
            or not embedding
        ):
            raise ValueError(
                "Embedding model returned an invalid embedding."
            )

        try:
            normalized_embedding = [
                float(value)
                for value in embedding
            ]

        except (
            TypeError,
            ValueError,
        ) as exc:
            logger.exception(
                "Embedding model returned non-numeric values."
            )

            raise ValueError(
                "Embedding model returned an invalid embedding."
            ) from exc

        try:
            self.cache.set(
                key=cache_key,
                value=normalized_embedding,
                ttl=settings.EMBEDDING_CACHE_TTL,
            )

        except Exception:
            logger.warning(
                "Embedding cache write failed for key %s. "
                "Continuing without cache.",
                cache_key,
                exc_info=True,
            )

        return normalized_embedding

    def create_trial_embedding(
        self,
        criteria_id: UUID,
        text: str,
    ) -> CriteriaEmbedding:
        """
        Generate and persist an embedding for a trial criterion.

        The caller owns the transaction boundary.
        """

        embedding = self.generate_embedding(
            text
        )

        entity = CriteriaEmbedding(
            criteria_id=criteria_id,
            embedding=embedding,
            model_name=EmbeddingModel.MODEL_NAME,
        )

        try:
            self.criteria_repository.create_embedding(
                entity
            )

            self.criteria_repository.flush()

            return entity

        except Exception:
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

        The caller owns the transaction boundary.
        """

        embedding = self.generate_embedding(
            text
        )

        entity = PatientNoteEmbedding(
            note_id=note_id,
            embedding=embedding,
            model_name=EmbeddingModel.MODEL_NAME,
        )

        try:
            self.patient_note_repository.create(
                entity
            )

            self.patient_note_repository.flush()

            return entity

        except Exception:
            logger.exception(
                "Failed to create embedding for patient note %s.",
                note_id,
            )

            raise

    def create_or_update_trial_embedding(
        self,
        trial_id: UUID,
        text: str,
    ) -> TrialEmbedding:
        """
        Generate and persist a semantic embedding representing an
        entire clinical trial.

        If an embedding already exists for the trial, it is updated.

        The caller owns the transaction boundary.
        """

        if self.trial_repository is None:
            raise RuntimeError(
                "Trial embedding repository is not configured."
            )

        embedding = self.generate_embedding(
            text
        )

        try:
            entity = self.trial_repository.upsert_embedding(
                trial_id=trial_id,
                embedding=embedding,
                model_name=EmbeddingModel.MODEL_NAME,
            )

            self.trial_repository.flush()

            return entity

        except Exception:
            logger.exception(
                "Failed to create or update trial embedding "
                "for trial %s.",
                trial_id,
            )

            raise