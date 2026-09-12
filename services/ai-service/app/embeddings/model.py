import logging
import math
from pathlib import Path
from threading import Lock
from typing import ClassVar

from sentence_transformers import SentenceTransformer


logger = logging.getLogger(__name__)


class EmbeddingModel:
    """
    Thread-safe singleton wrapper around the local SentenceTransformer model.

    The model is loaded once per Python process and reused for all
    embedding requests handled by that process.
    """

    MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

    EMBEDDING_DIMENSION = 384

    MODEL_PATH = (
        Path(__file__).resolve().parents[2]
        / "models"
        / "all-MiniLM-L6-v2"
    )

    _model: ClassVar[SentenceTransformer | None] = None
    _lock: ClassVar[Lock] = Lock()

    def __init__(self) -> None:
        if EmbeddingModel._model is None:
            with EmbeddingModel._lock:
                if EmbeddingModel._model is None:
                    self._load_model()

    @classmethod
    def _load_model(cls) -> None:
        """
        Load the SentenceTransformer model from the local filesystem.
        """

        if not cls.MODEL_PATH.exists():
            raise RuntimeError(
                "Embedding model not found at "
                f"{cls.MODEL_PATH}"
            )

        try:
            logger.info(
                "Loading embedding model '%s' from %s.",
                cls.MODEL_NAME,
                cls.MODEL_PATH,
            )

            cls._model = SentenceTransformer(
                str(cls.MODEL_PATH),
                device="cpu",
            )

            logger.info(
                "Embedding model '%s' loaded successfully.",
                cls.MODEL_NAME,
            )

        except Exception as exc:
            logger.exception(
                "Failed to load embedding model '%s'.",
                cls.MODEL_NAME,
            )

            raise RuntimeError(
                "Failed to initialize embedding model."
            ) from exc

    def encode(
        self,
        text: str,
    ) -> list[float]:
        """
        Generate a normalized embedding for the supplied text.

        The returned embedding must be a finite numeric vector with
        the expected dimension for the configured embedding model.
        """

        normalized_text = text.strip()

        if not normalized_text:
            raise ValueError(
                "Text for embedding cannot be empty."
            )

        model = EmbeddingModel._model

        if model is None:
            raise RuntimeError(
                "Embedding model is not initialized."
            )

        try:
            embedding = model.encode(
                normalized_text,
                normalize_embeddings=True,
            )

        except Exception as exc:
            logger.exception(
                "Embedding generation failed."
            )

            raise RuntimeError(
                "Failed to generate embedding."
            ) from exc

        try:
            values = embedding.tolist()

        except AttributeError as exc:
            logger.exception(
                "Embedding model returned an unexpected output type."
            )

            raise RuntimeError(
                "Embedding model returned an invalid output."
            ) from exc

        if not isinstance(values, list):
            raise RuntimeError(
                "Embedding model returned an invalid output."
            )

        if len(values) != self.EMBEDDING_DIMENSION:
            logger.error(
                "Embedding dimension mismatch. "
                "Expected %d but received %d.",
                self.EMBEDDING_DIMENSION,
                len(values),
            )

            raise RuntimeError(
                "Embedding model returned an unexpected dimension."
            )

        try:
            normalized_embedding = [
                float(value)
                for value in values
            ]

        except (
            TypeError,
            ValueError,
        ) as exc:
            logger.exception(
                "Embedding model returned non-numeric values."
            )

            raise RuntimeError(
                "Embedding model returned an invalid output."
            ) from exc

        if not all(
            math.isfinite(value)
            for value in normalized_embedding
        ):
            logger.error(
                "Embedding model returned non-finite values."
            )

            raise RuntimeError(
                "Embedding model returned invalid values."
            )

        return normalized_embedding