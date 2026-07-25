import hashlib


class CacheKeys:
    """
    Utility class for generating Redis cache keys.
    """

    @staticmethod
    def _hash(value: str) -> str:
        """
        Generate a SHA-256 hash for cache keys.
        """

        return hashlib.sha256(
            value.encode("utf-8")
        ).hexdigest()

    @staticmethod
    def embedding(text: str) -> str:
        """
        Generate a cache key for text embeddings.
        """

        return f"embedding:{CacheKeys._hash(text)}"

    @staticmethod
    def retrieval(
        patient_note: str,
        top_k: int,
    ) -> str:
        """
        Generate a cache key for retrieval results.
        """

        return (
            f"retrieval:"
            f"{CacheKeys._hash(patient_note)}:"
            f"{top_k}"
        )

    @staticmethod
    def llm(prompt: str) -> str:
        """
        Generate a cache key for LLM responses.
        """

        return f"llm:{CacheKeys._hash(prompt)}"

    @staticmethod
    def match(
        patient_id: int,
        trial_id: int,
    ) -> str:
        """
        Generate a cache key for complete trial matching results.
        """

        return f"match:{patient_id}:{trial_id}"