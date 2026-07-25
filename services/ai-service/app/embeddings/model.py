from typing import ClassVar, cast

from sentence_transformers import SentenceTransformer


class EmbeddingModel:
    """
    Singleton wrapper around the SentenceTransformer model.
    """

    MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

    _model: ClassVar[SentenceTransformer | None] = None

    def __init__(self) -> None:
        if EmbeddingModel._model is None:
            EmbeddingModel._model = SentenceTransformer(
                self.MODEL_NAME
            )

        self.model = EmbeddingModel._model

    def encode(
        self,
        text: str,
    ) -> list[float]:
        """
        Generate a normalized 384-dimensional embedding.
        """

        embedding = self.model.encode(
            text,
            normalize_embeddings=True,
        )

        return cast(
            list[float],
            embedding.tolist(),
        )