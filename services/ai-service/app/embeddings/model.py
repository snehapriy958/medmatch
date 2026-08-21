from pathlib import Path
from typing import ClassVar

from sentence_transformers import SentenceTransformer


class EmbeddingModel:
    """
    Singleton wrapper around the local SentenceTransformer model.
    """

    MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

    MODEL_PATH = (
        Path(__file__).resolve().parents[2]
        / "models"
        / "all-MiniLM-L6-v2"
    )

    _model: ClassVar[SentenceTransformer | None] = None

    def __init__(self) -> None:
        if EmbeddingModel._model is None:
            if not self.MODEL_PATH.exists():
                raise RuntimeError(
                    f"Embedding model not found at {self.MODEL_PATH}"
                )

            EmbeddingModel._model = SentenceTransformer(
                str(self.MODEL_PATH),
                device="cpu",
            )

    def encode(self, text: str) -> list[float]:
        """
        Generate a normalized 384-dimensional embedding.
        """

        if not text.strip():
            raise ValueError(
                "Text for embedding cannot be empty."
            )

        model = EmbeddingModel._model

        if model is None:
            raise RuntimeError(
                "Embedding model is not initialized."
            )

        embedding = model.encode(
            text,
            normalize_embeddings=True,
        )

        return embedding.tolist()