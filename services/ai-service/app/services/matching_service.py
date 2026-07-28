import logging

from uuid import UUID

from app.cache.cache_keys import CacheKeys
from app.cache.cache_service import CacheService
from app.config.settings import settings
from app.metrics.metrics import (
    MATCH_DURATION,
    MATCH_FAILURE,
    MATCH_REQUESTS,
    MATCH_SUCCESS,
    EMBEDDING_REQUESTS,
    LLM_REQUESTS,
)
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
from app.repositories.hospital_repository import HospitalRepository

logger = logging.getLogger(__name__)


class MatchingService:
    """
    Business logic for semantic trial matching and eligibility evaluation.
    """

    def __init__(
        self,
        repository: MatchingRepository,
        hospital_repository: HospitalRepository,
        embedding_service: EmbeddingService,
        llm_service: LLMService,
        audit_service: AuditService,
    ) -> None:
        self.repository = repository
        self.hospital_repository = hospital_repository
        self.embedding_service = embedding_service
        self.llm_service = llm_service
        self.audit_service = audit_service
        self.cache = CacheService()

    def _log_matching_audit(
        self,
        result: EligibilityResponse,
        current_user: dict,
        hospital_name: str,
        filtered_criteria: list[dict],
        patient_note: str,
    ) -> None:
        """
        Write audit log for eligibility evaluation.
        """

        try:
            self.audit_service.log(
                action="ELIGIBILITY_EVALUATED",
                resource_type="Matching",
                performed_by_id=UUID(current_user["sub"]),
                performed_by_username=current_user["email"],
                performed_by_role=current_user["role"],
                hospital_id=UUID(current_user["hospital_id"]),
                hospital_name=hospital_name,
                resource_id=None,
                details=(
                    f"Eligibility={result.eligibility}; "
                    f"Confidence={result.confidence}; "
                    f"MatchedInclusion={len(result.matched_inclusion)}; "
                    f"FailedInclusion={len(result.failed_inclusion)}; "
                    f"TriggeredExclusion={len(result.triggered_exclusion)}; "
                    f"MissingInfo={len(result.missing_information)}; "
                    f"TopMatches={len(filtered_criteria)}"
                ),
            )

        except Exception:
            logger.exception(
                "Failed to write eligibility audit log."
            )


    def _retrieve_matching_criteria(
        self,
        patient_note: str,
        hospital_id: UUID,
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

        EMBEDDING_REQUESTS.inc()

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
        hospital_id: UUID,
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
        hospital_id: UUID,
        current_user: dict,
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

        MATCH_REQUESTS.inc()

        
        with MATCH_DURATION.time():

            filtered_criteria = self._retrieve_matching_criteria(
                patient_note=patient_note,
                hospital_id=hospital_id,
                limit=limit,
            )

            prompt = PromptBuilder.build_matching_prompt(
                patient_note=patient_note,
                retrieved_criteria=filtered_criteria,
            )

            hospital = self.hospital_repository.get_by_id(
                UUID(current_user["hospital_id"])
            )
            
            hospital_name = (
                hospital.name
                if hospital is not None
                else "Unknown Hospital"
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

                              
                self._log_matching_audit(
                    result=response,
                    current_user=current_user,
                    hospital_name=hospital_name,
                    filtered_criteria=filtered_criteria,
                    patient_note=patient_note,
                )

                MATCH_SUCCESS.inc()
                return response

            logger.info(
                "LLM cache MISS (hospital=%s)",
                hospital_id,
            )

            try:
                LLM_REQUESTS.inc()

                result = self.llm_service.evaluate_eligibility(
                    prompt=prompt,
                )

            except Exception:
                MATCH_FAILURE.inc()

                logger.exception(
                    "Eligibility evaluation failed."
                )
                raise

            self.cache.set(
                key=cache_key,
                value=result.model_dump(),
                ttl=settings.LLM_CACHE_TTL,
            )

            self._log_matching_audit(
                result=result,
                current_user=current_user,
                hospital_name=hospital_name,
                filtered_criteria=filtered_criteria,
                patient_note=patient_note,
            )


            MATCH_SUCCESS.inc()

            return result