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
    RETRIEVAL_CACHE_HITS,
    RETRIEVAL_CACHE_MISSES,
    LLM_CACHE_HITS,
    LLM_CACHE_MISSES,
)
from app.rag.prompt_builder import PromptBuilder
from app.schemas import (
    MatchingResponse,
    MatchingResult,
)
from app.schemas.eligibility import (
    EligibilityEvaluationResponse,
    EligibilityResponse,
    EligibilityStatus,
)
from app.services.audit_service import AuditService
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService
from app.repositories.hospital_repository import HospitalRepository
from app.repositories.matching_repository import MatchingRepository

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
            Retrieve condition-compatible trial criteria using
            condition-aware filtering followed by pgvector ranking.
            
            Results are tenant-isolated and cached per hospital.
        """

        cache_key = CacheKeys.retrieval(
            patient_note=f"{hospital_id}:{patient_note}",
            top_k=limit,
        )

        cached_results = self.cache.get(cache_key)

        if cached_results is not None:
            RETRIEVAL_CACHE_HITS.inc()
            logger.info(
                "Retrieval cache HIT (hospital=%s)",
                hospital_id,
            )
            return cached_results

        RETRIEVAL_CACHE_MISSES.inc()

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
            patient_note=patient_note,
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
        Generate an embedding for the patient note, retrieve the top
        candidate trials, and return one representative criterion per trial.

        The retrieval layer may contain multiple criteria for each trial,
        but the search API represents each trial only once.
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

        # Deduplicate by trial_id.
        # Keep the criterion with the smallest cosine distance
        # because lower distance means stronger semantic similarity.
        best_by_trial: dict[UUID, dict] = {}

        for result in filtered_results:
            trial_id = result["trial_id"]

            existing = best_by_trial.get(trial_id)

            if existing is None or result["distance"] < existing["distance"]:
                best_by_trial[trial_id] = result

        # Preserve ranking by best semantic distance.
        ranked_results = sorted(
            best_by_trial.values(),
            key=lambda result: result["distance"],
        )

        # Defensive limit: number of trials, not number of criteria.
        ranked_results = ranked_results[:limit]

        matches = [
            MatchingResult(**result)
            for result in ranked_results
        ]

        return MatchingResponse(
            query=patient_note,
            total_matches=len(ranked_results),
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
    ) -> EligibilityEvaluationResponse:
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

            logger.info(
                "EVALUATION RETRIEVAL RESULT: hospital=%s criteria_count=%d trial_ids=%s",
                hospital_id,
                len(filtered_criteria),
                list({
                    str(item.get("trial_id"))
                    for item in filtered_criteria
                    if item.get("trial_id") is not None
                }),
            )

            # No trial criteria means there is nothing to evaluate.
            # Do not ask Gemini to make an eligibility decision.
            if not filtered_criteria:

                logger.info(
                    "EMPTY RETRIEVAL GUARD TRIGGERED: hospital=%s",
                    hospital_id,
                )
                
                logger.info(
                    "No matching trial criteria found "
                    "(hospital=%s). Skipping Gemini eligibility evaluation.",
                    hospital_id,
                )

                response = EligibilityEvaluationResponse(
                    results=[
                        EligibilityResponse(
                            eligibility=EligibilityStatus.POSSIBLY_ELIGIBLE,
                            confidence=0.0,
                            trial_ids_evaluated=[],
                            summary=(
                                "No matching clinical trial criteria were retrieved. "
                                "Eligibility cannot be determined."
                            ),
                            matched_inclusion=[],
                            failed_inclusion=[],
                            satisfied_exclusion=[],
                            triggered_exclusion=[],
                            missing_information=[
                                "No matching clinical trial criteria available."
                            ],
                            recommendation=(
                                "Retrieve additional clinical trial criteria "
                                "before making an eligibility determination."
                            ),
                            matched_criteria=[],
                            failed_criteria=[],
                            reasoning=(
                                "No trial criteria were retrieved for this patient. "
                                "Therefore, eligibility cannot be determined for "
                                "a specific clinical trial."
                            ),
                        )
                    ]
                )

                MATCH_SUCCESS.inc()

                return response

            prompt = PromptBuilder.build_matching_prompt(
                patient_note=patient_note,
                retrieved_criteria=filtered_criteria,
            )

            logger.info(
                "========== GEMINI PROMPT =========="
            )
            logger.info(prompt)
            logger.info(
                "========== END GEMINI PROMPT =========="
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
                LLM_CACHE_HITS.inc()

                logger.info(
                    "LLM cache HIT (hospital=%s)",
                    hospital_id,
                )

                response = EligibilityEvaluationResponse(
                    **cached_result
                )

                for evaluation in response.results:
                    self._log_matching_audit(
                        result=evaluation,
                        current_user=current_user,
                        hospital_name=hospital_name,
                        filtered_criteria=filtered_criteria,
                        patient_note=patient_note,
                    )

                MATCH_SUCCESS.inc()

                return response

            LLM_CACHE_MISSES.inc()

            logger.info(
                "LLM cache MISS (hospital=%s)",
                hospital_id,
            )

            try:
                LLM_REQUESTS.inc()

                # Gemini returns one independent EligibilityResponse
                # for every evaluated clinical trial.
                llm_results = self.llm_service.evaluate_eligibility(
                    prompt=prompt,
                )

                # Preserve the independent per-trial results.
                response = EligibilityEvaluationResponse(
                    results=llm_results
                )

            except Exception:
                MATCH_FAILURE.inc()

                logger.exception(
                    "Eligibility evaluation failed."
                )

                raise

            # Cache the same structure returned by the API.
            self.cache.set(
                key=cache_key,
                value=response.model_dump(),
                ttl=settings.LLM_CACHE_TTL,
            )

            for evaluation in response.results:
                self._log_matching_audit(
                    result=evaluation,
                    current_user=current_user,
                    hospital_name=hospital_name,
                    filtered_criteria=filtered_criteria,
                    patient_note=patient_note,
                )

            MATCH_SUCCESS.inc()

            return response