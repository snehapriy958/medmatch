import logging

from app.cache.cache_keys import CacheKeys
from app.cache.cache_service import CacheService
from app.config.settings import settings
from app.rag.prompt_builder import PromptBuilder
from app.repositories.matching_repository import MatchingRepository
from app.schemas import (
    MatchingResponse,
    MatchingResult,
)
from app.schemas.eligibility import EligibilityResponse
from app.services.audit_service import AuditService
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class MatchingService:
    """
    Business logic for semantic trial matching and eligibility evaluation.
    """

    def __init__(
        self,
        repository: MatchingRepository,
        embedding_service: EmbeddingService,
        llm_service: LLMService,
        audit_service: AuditService,
    ) -> None:
        self.repository = repository
        self.embedding_service = embedding_service
        self.llm_service = llm_service
        self.audit_service = audit_service
        self.cache = CacheService()

    def _retrieve_matching_criteria(
        self,
        patient_note: str,
        hospital_id: int,
        limit: int,
    ) -> list[dict]:
        """
        Generate an embedding for the patient note, retrieve similar
        trial criteria, and cache retrieval results.
        """

        cache_key = CacheKeys.retrieval(
            patient_note=f"{hospital_id}:{patient_note}",
            top_k=limit,
        )

        cached_results = self.cache.get(cache_key)

        if cached_results is not None:
            logger.info(
                "Retrieval cache HIT (hospital=%s)",
                hospital_id,
            )
            return cached_results

        logger.info(
            "Retrieval cache MISS (hospital=%s)",
            hospital_id,
        )

        embedding = self.embedding_service.generate_embedding(
            patient_note,
        )

        criteria = self.repository.find_similar_criteria(
            embedding=embedding,
            hospital_id=hospital_id,
            limit=limit,
        )

        filtered_results = [
            criterion
            for criterion in criteria
            if criterion["distance"] <= settings.SIMILARITY_THRESHOLD
        ]

        self.cache.set(
            key=cache_key,
            value=filtered_results,
            ttl=settings.RETRIEVAL_CACHE_TTL,
        )

        return filtered_results

    def find_matching_criteria(
        self,
        patient_note: str,
        hospital_id: int,
        limit: int = 10,
    ) -> MatchingResponse:
        """
        Generate an embedding for the patient note and retrieve
        the most similar trial criteria.
        """

        if not patient_note.strip():
            raise ValueError(
                "Patient note cannot be empty."
            )

        filtered_results = self._retrieve_matching_criteria(
            patient_note=patient_note,
            hospital_id=hospital_id,
            limit=limit,
        )

        matches = [
            MatchingResult(**result)
            for result in filtered_results
        ]

        return MatchingResponse(
            query=patient_note,
            total_matches=len(filtered_results),
            returned_matches=len(matches),
            similarity_threshold=settings.SIMILARITY_THRESHOLD,
            matches=matches,
        )

    def evaluate_eligibility(
        self,
        patient_note: str,
        hospital_id: int,
        limit: int = 10,
    ) -> EligibilityResponse:
        """
        Evaluate a patient's eligibility using semantic retrieval
        followed by LLM reasoning.
        """

        if not patient_note.strip():
            raise ValueError(
                "Patient note cannot be empty."
            )

        filtered_criteria = self._retrieve_matching_criteria(
            patient_note=patient_note,
            hospital_id=hospital_id,
            limit=limit,
        )

        prompt = PromptBuilder.build_matching_prompt(
            patient_note=patient_note,
            retrieved_criteria=filtered_criteria,
        )

        cache_key = CacheKeys.llm(
            f"{hospital_id}:{prompt}",
        )

        cached_result = self.cache.get(cache_key)

        if cached_result is not None:
            logger.info(
                "LLM cache HIT (hospital=%s)",
                hospital_id,
            )

            response = EligibilityResponse(**cached_result)

            try:
                self.audit_service.log(
                    action="ELIGIBILITY_EVALUATED",
                    resource="Matching",
                    details=(
                        f"Eligibility evaluated using cached response. "
                        f"Result: {response.eligibility}"
                    ),
                )
            except Exception:
                logger.exception(
                    "Failed to write eligibility audit log."
                )

            return response

        logger.info(
            "LLM cache MISS (hospital=%s)",
            hospital_id,
        )

        try:
            result = self.llm_service.evaluate_eligibility(
                prompt=prompt,
            )
        except Exception:
            logger.exception(
                "Eligibility evaluation failed."
            )
            raise

        self.cache.set(
            key=cache_key,
            value=result.model_dump(),
            ttl=settings.LLM_CACHE_TTL,
        )

        try:
            self.audit_service.log(
                action="ELIGIBILITY_EVALUATED",
                resource="Matching",
                details=(
                    f"Eligibility evaluated. "
                    f"Result: {result.eligibility}"
                ),
            )
        except Exception:
            logger.exception(
                "Failed to write eligibility audit log."
            )

        return result