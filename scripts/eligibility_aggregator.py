"""
MedMatch Deterministic Eligibility Aggregator.
Phase 6: Eligibility Reasoning.

Implements pure, deterministic programmatic aggregation of atomic criterion evaluations
into trial-level eligibility decisions.

Aggregation Rules:
1. IF any criterion is FAIL:
       Trial status = INELIGIBLE
2. ELSE IF no criterion is FAIL and at least one criterion is UNKNOWN:
       Trial status = NEEDS_REVIEW
3. ELSE IF all criteria are PASS (and count > 0):
       Trial status = ELIGIBLE
4. IF zero criteria evaluated:
       Trial status = NEEDS_REVIEW (cannot confirm eligibility without criteria)
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set
try:
    from scripts.eligibility_schema import (
        CriterionEvaluationRecord,
        CriterionEvaluationStatus,
        TrialEligibilityEvaluation,
        TrialEligibilityStatus,
    )
except ImportError:
    from eligibility_schema import (
        CriterionEvaluationRecord,
        CriterionEvaluationStatus,
        TrialEligibilityEvaluation,
        TrialEligibilityStatus,
    )


class EligibilityAggregator:
    """
    Deterministic aggregator for criterion-level evaluations.
    """

    @staticmethod
    def aggregate_trial(
        trial_id: str,
        criterion_evaluations: List[CriterionEvaluationRecord],
        trial_title: Optional[str] = None,
        allow_duplicates: bool = False,
    ) -> TrialEligibilityEvaluation:
        """
        Aggregates a list of criterion evaluations for a single clinical trial.

        Parameters:
        - trial_id: canonical trial identifier
        - criterion_evaluations: list of atomic criterion evaluations
        - trial_title: optional trial title
        - allow_duplicates: if False, raises ValueError upon duplicate criterion_id

        Returns:
        - TrialEligibilityEvaluation with deterministic status and summary counts
        """
        if not trial_id or not trial_id.strip():
            raise ValueError("trial_id cannot be empty")

        # Check for duplicate criterion IDs
        seen_criterion_ids: Set[str] = set()
        deduped_evaluations: List[CriterionEvaluationRecord] = []

        for eval_record in criterion_evaluations:
            cid = eval_record.criterion_id
            if cid in seen_criterion_ids:
                if not allow_duplicates:
                    raise ValueError(
                        f"Duplicate criterion_id '{cid}' detected in evaluation for trial '{trial_id}'."
                    )
            else:
                seen_criterion_ids.add(cid)
                deduped_evaluations.append(eval_record)

        evals_to_process = deduped_evaluations if not allow_duplicates else criterion_evaluations

        # Partition criteria by status
        passed_ids: List[str] = []
        failed_ids: List[str] = []
        unknown_ids: List[str] = []

        for eval_record in evals_to_process:
            if eval_record.status == CriterionEvaluationStatus.FAIL:
                failed_ids.append(eval_record.criterion_id)
            elif eval_record.status == CriterionEvaluationStatus.UNKNOWN:
                unknown_ids.append(eval_record.criterion_id)
            elif eval_record.status == CriterionEvaluationStatus.PASS:
                passed_ids.append(eval_record.criterion_id)
            else:
                raise ValueError(f"Encountered unexpected status: {eval_record.status}")

        total_evaluated = len(evals_to_process)

        # Deterministic Aggregation Decision Rule
        if len(failed_ids) > 0:
            status = TrialEligibilityStatus.INELIGIBLE
            summary = (
                f"Ineligible: Patient fails {len(failed_ids)} criterion/criteria "
                f"({', '.join(failed_ids[:3])}{'...' if len(failed_ids) > 3 else ''})."
            )
        elif len(unknown_ids) > 0:
            status = TrialEligibilityStatus.NEEDS_REVIEW
            summary = (
                f"Needs Review: No criteria failed, but {len(unknown_ids)} criterion/criteria are unknown "
                f"({', '.join(unknown_ids[:3])}{'...' if len(unknown_ids) > 3 else ''})."
            )
        elif total_evaluated > 0 and len(passed_ids) == total_evaluated:
            status = TrialEligibilityStatus.ELIGIBLE
            summary = f"Eligible: Patient satisfies all {total_evaluated} evaluated criteria."
        else:
            # Zero criteria evaluated
            status = TrialEligibilityStatus.NEEDS_REVIEW
            summary = "Needs Review: Zero criteria evaluated. Eligibility cannot be confirmed."

        return TrialEligibilityEvaluation(
            trial_id=trial_id,
            trial_title=trial_title,
            status=status,
            criterion_evaluations=evals_to_process,
            total_criteria_evaluated=total_evaluated,
            passed_count=len(passed_ids),
            failed_count=len(failed_ids),
            unknown_count=len(unknown_ids),
            failed_criterion_ids=failed_ids,
            unknown_criterion_ids=unknown_ids,
            passed_criterion_ids=passed_ids,
            clinical_summary=summary,
            evaluator="deterministic_aggregator",
        )

    @classmethod
    def aggregate_batch(
        cls,
        evaluations_by_trial: Dict[str, List[CriterionEvaluationRecord]],
        trial_titles: Optional[Dict[str, str]] = None,
    ) -> List[TrialEligibilityEvaluation]:
        """
        Aggregates evaluations across multiple trials.
        Deterministic ordering by trial_id ASC.
        """
        results: List[TrialEligibilityEvaluation] = []
        titles = trial_titles or {}

        for trial_id in sorted(evaluations_by_trial.keys()):
            evals = evaluations_by_trial[trial_id]
            title = titles.get(trial_id)
            aggregated = cls.aggregate_trial(
                trial_id=trial_id,
                criterion_evaluations=evals,
                trial_title=title,
            )
            results.append(aggregated)

        return results
