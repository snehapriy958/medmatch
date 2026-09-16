import logging
from uuid import UUID

from app.cache.cache_keys import CacheKeys
from app.cache.cache_service import CacheService
from app.config.settings import settings
from app.metrics.metrics import (
    EMBEDDING_REQUESTS,
    LLM_CACHE_HITS,
    LLM_CACHE_MISSES,
    LLM_REQUESTS,
    MATCH_DURATION,
    MATCH_FAILURE,
    MATCH_REQUESTS,
    MATCH_SUCCESS,
    RETRIEVAL_CACHE_HITS,
    RETRIEVAL_CACHE_MISSES,
)
from app.rag.prompt_builder import PromptBuilder
from app.repositories.hospital_repository import HospitalRepository
from app.repositories.matching_repository import MatchingRepository
from app.repositories.trial_criteria_repository import (
    TrialCriteriaRepository,
)
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

logger = logging.getLogger(__name__)


class MatchingService:
    """
    Business logic for semantic clinical trial matching and
    eligibility evaluation.

    Retrieval is tenant-isolated by hospital and eligibility
    evaluations are validated against the exact trials retrieved
    before results are returned or cached.
    """

    def __init__(
        self,
        repository: MatchingRepository,
        trial_criteria_repository: TrialCriteriaRepository,
        hospital_repository: HospitalRepository,
        embedding_service: EmbeddingService,
        llm_service: LLMService,
        audit_service: AuditService,
    ) -> None:
        self.repository = repository
        self.trial_criteria_repository = (
            trial_criteria_repository
        )
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
        Write an audit log for an eligibility evaluation.

        The patient note itself is intentionally not written to the
        audit details to avoid storing unnecessary clinical content.
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

    def _validate_user_hospital(
        self,
        hospital_id: UUID,
        current_user: dict,
    ) -> UUID:
        """
        Ensure the hospital supplied to the service matches the
        authenticated user's hospital.

        This provides a defensive tenant-isolation check before
        retrieval, LLM evaluation, caching, or audit logging.
        """

        try:
            user_hospital_id = UUID(
                current_user["hospital_id"]
            )

        except (KeyError, ValueError, TypeError) as exc:
            logger.error(
                "Invalid or missing hospital_id in current user."
            )

            raise ValueError(
                "Current user does not contain a valid hospital ID."
            ) from exc

        if user_hospital_id != hospital_id:
            logger.error(
                "Hospital mismatch during eligibility evaluation. "
                "requested_hospital=%s user_hospital=%s",
                hospital_id,
                user_hospital_id,
            )

            raise ValueError(
                "Hospital access mismatch."
            )

        return user_hospital_id

    def _retrieve_matching_criteria(
        self,
        patient_note: str,
        hospital_id: UUID,
        limit: int,
    ) -> list[dict]:
        """
        Retrieve candidate clinical trials using trial-level
        semantic similarity ranking.

        Results are tenant-isolated and cached per hospital.
        """

        limit = max(1, min(limit, 100))

        cache_key = CacheKeys.retrieval(
            patient_note=f"{hospital_id}:{patient_note}",
            top_k=limit,
        )

        cached_results = self.cache.get(
            cache_key
        )

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

        embedding = (
            self.embedding_service.generate_embedding(
                patient_note
            )
        )

        criteria = (
            self.repository.find_similar_criteria(
                embedding=embedding,
                hospital_id=hospital_id,
                limit=limit,
            )
        )

        filtered_results = [
            criterion
            for criterion in criteria
            if criterion["distance"]
            <= settings.SIMILARITY_THRESHOLD
        ]

        self.cache.set(
            key=cache_key,
            value=filtered_results,
            ttl=settings.RETRIEVAL_CACHE_TTL,
        )

        return filtered_results

    def _get_retrieved_trial_ids(
        self,
        filtered_criteria: list[dict],
    ) -> set[str]:
        """
        Return the unique clinical trial IDs represented by the
        retrieved criteria.

        These IDs define the exact set of trials that Gemini is
        permitted to evaluate.
        """

        trial_ids: set[str] = set()

        for criterion in filtered_criteria:

            trial_id = criterion.get(
                "trial_id"
            )

            if trial_id is None:
                continue

            trial_ids.add(
                str(trial_id)
            )

        return trial_ids

    def _get_complete_trial_criteria(
        self,
        trial_ids: set[str],
    ) -> list[dict]:
        """
        Fetch every inclusion and exclusion criterion for the candidate
        trials identified during semantic retrieval.

        Semantic retrieval is used only to discover candidate trials.
        Eligibility evaluation must use the complete criterion set for
        each candidate trial.
        """

        complete_criteria: list[dict] = []

        for trial_id in sorted(trial_ids):

            criteria = (
                self.trial_criteria_repository.list_by_trial(
                    UUID(trial_id)
                )
            )

            for criterion in criteria:

                complete_criteria.append(
                    {
                        "id": str(criterion.id),
                        "trial_id": str(
                            criterion.trial_id
                        ),
                        "criteria_type": (
                            criterion.criteria_type
                        ),
                        "description": (
                            criterion.description
                        ),
                    }
                )

        return complete_criteria

    def _validate_llm_trial_results(
        self,
        llm_results: list[EligibilityResponse],
        expected_trial_ids: set[str],
    ) -> None:
        """
        Validate that Gemini returned exactly one evaluation for
        every retrieved clinical trial.

        The validation prevents:
        - hallucinated trial IDs
        - duplicate trial evaluations
        - missing trial evaluations
        """

        returned_trial_ids: list[str] = []

        for result in llm_results:

            if len(
                result.trial_ids_evaluated
            ) != 1:
                raise ValueError(
                    "Each eligibility result must correspond "
                    "to exactly one clinical trial."
                )

            trial_id = (
                result.trial_ids_evaluated[0]
            )

            returned_trial_ids.append(
                trial_id
            )

        returned_trial_id_set = set(
            returned_trial_ids
        )

        unexpected_trial_ids = (
            returned_trial_id_set
            - expected_trial_ids
        )

        if unexpected_trial_ids:

            logger.error(
                "LLM returned trial IDs that were not retrieved: %s",
                sorted(unexpected_trial_ids),
            )

            raise ValueError(
                "LLM returned an evaluation for an unexpected "
                "clinical trial."
            )

        if len(returned_trial_ids) != len(
            returned_trial_id_set
        ):

            logger.error(
                "LLM returned duplicate eligibility evaluations. "
                "trial_ids=%s",
                returned_trial_ids,
            )

            raise ValueError(
                "LLM returned duplicate clinical trial evaluations."
            )

        missing_trial_ids = (
            expected_trial_ids
            - returned_trial_id_set
        )

        if missing_trial_ids:

            logger.error(
                "LLM did not evaluate all retrieved trials. "
                "missing_trial_ids=%s",
                sorted(missing_trial_ids),
            )

            raise ValueError(
                "LLM did not return an eligibility evaluation for "
                "every retrieved clinical trial."
            )

    def find_matching_criteria(
        self,
        patient_note: str,
        hospital_id: UUID,
        limit: int = 10,
    ) -> MatchingResponse:
        """
        Generate an embedding for the patient note, retrieve the top
        candidate trials, and return one representative criterion
        per trial.

        The retrieval layer may contain multiple criteria for each
        trial, but the search API represents each trial only once.
        """

        if not patient_note.strip():
            raise ValueError(
                "Patient note cannot be empty."
            )

        limit = max(
            1,
            min(limit, 100),
        )

        filtered_results = (
            self._retrieve_matching_criteria(
                patient_note=patient_note,
                hospital_id=hospital_id,
                limit=limit,
            )
        )

        # Deduplicate by trial ID and retain the criterion with
        # the smallest cosine distance.
        best_by_trial: dict[UUID, dict] = {}

        for result in filtered_results:

            trial_id = result[
                "trial_id"
            ]

            existing = best_by_trial.get(
                trial_id
            )

            if (
                existing is None
                or result["distance"]
                < existing["distance"]
            ):
                best_by_trial[trial_id] = result

        ranked_results = sorted(
            best_by_trial.values(),
            key=lambda result: result[
                "distance"
            ],
        )

        ranked_results = ranked_results[
            :limit
        ]

        matches = [
            MatchingResult(**result)
            for result in ranked_results
        ]

        return MatchingResponse(
            query=patient_note,
            total_matches=len(
                ranked_results
            ),
            returned_matches=len(
                matches
            ),
            similarity_threshold=(
                settings.SIMILARITY_THRESHOLD
            ),
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
        Evaluate patient eligibility using condition-aware semantic
        retrieval followed by independent LLM reasoning for each
        retrieved clinical trial.
        """

        if not patient_note.strip():
            raise ValueError(
                "Patient note cannot be empty."
            )

        limit = max(
            1,
            min(limit, 100),
        )

        validated_hospital_id = (
            self._validate_user_hospital(
                hospital_id=hospital_id,
                current_user=current_user,
            )
        )

        MATCH_REQUESTS.inc()

        with MATCH_DURATION.time():

            try:

                filtered_criteria = (
                    self._retrieve_matching_criteria(
                        patient_note=patient_note,
                        hospital_id=validated_hospital_id,
                        limit=limit,
                    )
                )

                expected_trial_ids = (
                    self._get_retrieved_trial_ids(
                        filtered_criteria
                    )
                )

                complete_trial_criteria = (
                    self._get_complete_trial_criteria(
                        expected_trial_ids
                    )
                )

                if expected_trial_ids and not complete_trial_criteria:
                    raise ValueError(
                        "Candidate trials were retrieved, but no complete "
                        "trial criteria could be loaded."
                    )

                logger.info(
                    "Eligibility retrieval completed. "
                    "hospital=%s retrieved_criteria_count=%d "
                    "complete_criteria_count=%d trial_count=%d",
                    validated_hospital_id,
                    len(filtered_criteria),
                    len(complete_trial_criteria),
                    len(expected_trial_ids),
                )

                # No criteria means there is no specific trial
                # against which eligibility can safely be evaluated.
                if not filtered_criteria:

                    logger.info(
                        "No matching trial criteria found. "
                        "Skipping Gemini eligibility evaluation. "
                        "hospital=%s",
                        validated_hospital_id,
                    )

                    response = (
                        EligibilityEvaluationResponse(
                            results=[
                                EligibilityResponse(
                                    eligibility=(
                                        EligibilityStatus
                                        .POSSIBLY_ELIGIBLE
                                    ),
                                    confidence=0.0,
                                    trial_ids_evaluated=[],
                                    summary=(
                                        "No matching clinical trial "
                                        "criteria were retrieved. "
                                        "Eligibility cannot be "
                                        "determined."
                                    ),
                                    matched_inclusion=[],
                                    failed_inclusion=[],
                                    satisfied_exclusion=[],
                                    triggered_exclusion=[],
                                    missing_information=[
                                        (
                                            "No matching clinical "
                                            "trial criteria available."
                                        )
                                    ],
                                    recommendation=(
                                        "Retrieve additional clinical "
                                        "trial criteria before making "
                                        "an eligibility determination."
                                    ),
                                    matched_criteria=[],
                                    failed_criteria=[],
                                    reasoning=(
                                        "No trial criteria were "
                                        "retrieved for this patient. "
                                        "Therefore, eligibility cannot "
                                        "be determined for a specific "
                                        "clinical trial."
                                    ),
                                )
                            ]
                        )
                    )

                    MATCH_SUCCESS.inc()

                    return response

                prompt = (
                    PromptBuilder.build_matching_prompt(
                        patient_note=patient_note,
                        retrieved_criteria=complete_trial_criteria,
                    )
                )

                # Do not log the full prompt because it may contain
                # sensitive clinical information.
                logger.info(
                    "Eligibility prompt built. "
                    "hospital=%s trial_count=%d criteria_count=%d",
                    validated_hospital_id,
                    len(expected_trial_ids),
                    len(filtered_criteria),
                )

                hospital = (
                    self.hospital_repository.get_by_id(
                        validated_hospital_id
                    )
                )

                hospital_name = (
                    hospital.name
                    if hospital is not None
                    else "Unknown Hospital"
                )

                cache_key = CacheKeys.llm(
                    f"{validated_hospital_id}:{prompt}",
                )

                cached_result = (
                    self.cache.get(
                        cache_key
                    )
                )

                if cached_result is not None:

                    LLM_CACHE_HITS.inc()

                    logger.info(
                        "LLM cache HIT (hospital=%s)",
                        validated_hospital_id,
                    )

                    response = (
                        EligibilityEvaluationResponse(
                            **cached_result
                        )
                    )

                    self._validate_llm_trial_results(
                        llm_results=response.results,
                        expected_trial_ids=(
                            expected_trial_ids
                        ),
                    )

                    for evaluation in response.results:

                        self._log_matching_audit(
                            result=evaluation,
                            current_user=current_user,
                            hospital_name=hospital_name,
                            filtered_criteria=(
                                filtered_criteria
                            ),
                            patient_note=patient_note,
                        )

                    MATCH_SUCCESS.inc()

                    return response

                LLM_CACHE_MISSES.inc()

                logger.info(
                    "LLM cache MISS (hospital=%s)",
                    validated_hospital_id,
                )

                LLM_REQUESTS.inc()

                llm_results = (
                    self.llm_service
                    .evaluate_eligibility(
                        prompt=prompt
                    )
                )

                try:

                    self._validate_llm_trial_results(
                        llm_results=llm_results,
                        expected_trial_ids=(
                            expected_trial_ids
                        ),
                    )

                except ValueError as exc:

                    logger.warning(
                        "LLM eligibility response failed trial validation. "
                        "Returning safe abstention. reason=%s",
                        str(exc),
                    )

                    MATCH_SUCCESS.inc()

                    return EligibilityEvaluationResponse(
                        results=[
                            EligibilityResponse(
                                eligibility=EligibilityStatus.POSSIBLY_ELIGIBLE,
                                confidence=0.0,
                                trial_ids_evaluated=[],
                                summary=(
                                    "No reliable clinical trial eligibility "
                                    "evaluation could be produced for the "
                                    "retrieved candidate trials."
                                ),
                                matched_inclusion=[],
                                failed_inclusion=[],
                                satisfied_exclusion=[],
                                triggered_exclusion=[],
                                missing_information=[
                                    "Reliable trial-specific eligibility evaluation"
                                ],
                                recommendation=(
                                    "Do not treat this as an eligibility decision. "
                                    "Review the candidate trials manually."
                                ),
                                matched_criteria=[],
                                failed_criteria=[],
                                reasoning=(
                                    "The AI response failed validation against "
                                    "the exact clinical trials retrieved by the "
                                    "system. The result was therefore rejected "
                                    "instead of returning an ungrounded decision."
                                ),
                            )
                        ]
                    )

                response = (
                    EligibilityEvaluationResponse(
                        results=llm_results
                    )
                )

                # Only validated responses are cached.
                self.cache.set(
                    key=cache_key,
                    value=response.model_dump(
                        mode="json"
                    ),
                    ttl=settings.LLM_CACHE_TTL,
                )

                for evaluation in response.results:

                    self._log_matching_audit(
                        result=evaluation,
                        current_user=current_user,
                        hospital_name=hospital_name,
                        filtered_criteria=(
                            filtered_criteria
                        ),
                        patient_note=patient_note,
                    )

                MATCH_SUCCESS.inc()

                return response

            except Exception:

                MATCH_FAILURE.inc()

                logger.exception(
                    "Eligibility evaluation failed. "
                    "hospital=%s",
                    validated_hospital_id,
                )

                raise