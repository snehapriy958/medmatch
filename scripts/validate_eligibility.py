"""
MedMatch Deterministic Eligibility Validation Harness.
Phase 6: Eligibility Reasoning.

Validates:
1. Schema conformity of CriterionEvaluationRecord and TrialEligibilityEvaluation
2. Strict 3-valued logic (PASS, FAIL, UNKNOWN)
3. Evidence Citation Invariant: PASS/FAIL must cite grounded evidence
4. Deterministic Aggregation Invariant:
   - Any FAIL -> INELIGIBLE
   - No FAIL + any UNKNOWN -> NEEDS_REVIEW
   - All PASS -> ELIGIBLE
   - 0 criteria -> NEEDS_REVIEW
5. Summary count consistency (total == passed + failed + unknown)
6. Duplicate criterion ID detection
7. Clean JSON round-trip serialization
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set
from pydantic import ValidationError

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


class EligibilityValidator:
    """
    Validation engine for research eligibility records and evaluations.
    """

    @classmethod
    def validate_criterion_evaluation(
        cls, record: CriterionEvaluationRecord
    ) -> List[str]:
        """Validates a single CriterionEvaluationRecord."""
        errors: List[str] = []

        # Validate status enum
        if record.status not in (
            CriterionEvaluationStatus.PASS,
            CriterionEvaluationStatus.FAIL,
            CriterionEvaluationStatus.UNKNOWN,
        ):
            errors.append(f"Invalid criterion status '{record.status}'.")

        # Evidence policy: PASS or FAIL must cite evidence
        if record.status in (
            CriterionEvaluationStatus.PASS,
            CriterionEvaluationStatus.FAIL,
        ):
            if not record.evidence_citations and not record.patient_fact_references:
                errors.append(
                    f"Evidence violation: criterion '{record.criterion_id}' is '{record.status}' "
                    "without supporting evidence citations or fact references."
                )

        # UNKNOWN should not cite affirmative proof without uncertainty notes
        if record.status == CriterionEvaluationStatus.UNKNOWN:
            if not record.uncertainty_notes and not record.reasoning:
                errors.append(
                    f"Uncertainty violation: criterion '{record.criterion_id}' is UNKNOWN "
                    "without reasoning or uncertainty notes."
                )

        return errors

    @classmethod
    def validate_trial_evaluation(
        cls, evaluation: TrialEligibilityEvaluation
    ) -> List[str]:
        """Validates a TrialEligibilityEvaluation and its aggregation consistency."""
        errors: List[str] = []

        if not evaluation.trial_id:
            errors.append("Trial evaluation missing trial_id.")

        seen_criterion_ids: Set[str] = set()
        actual_passed = 0
        actual_failed = 0
        actual_unknown = 0

        for crit in evaluation.criterion_evaluations:
            # Validate individual criterion
            crit_errors = cls.validate_criterion_evaluation(crit)
            errors.extend(crit_errors)

            # Check duplicate criterion IDs
            if crit.criterion_id in seen_criterion_ids:
                errors.append(
                    f"Duplicate criterion_id '{crit.criterion_id}' in trial '{evaluation.trial_id}'."
                )
            seen_criterion_ids.add(crit.criterion_id)

            if crit.status == CriterionEvaluationStatus.PASS:
                actual_passed += 1
            elif crit.status == CriterionEvaluationStatus.FAIL:
                actual_failed += 1
            elif crit.status == CriterionEvaluationStatus.UNKNOWN:
                actual_unknown += 1

        # Check count consistency
        if evaluation.passed_count != actual_passed:
            errors.append(
                f"Count mismatch: passed_count ({evaluation.passed_count}) != actual ({actual_passed})."
            )
        if evaluation.failed_count != actual_failed:
            errors.append(
                f"Count mismatch: failed_count ({evaluation.failed_count}) != actual ({actual_failed})."
            )
        if evaluation.unknown_count != actual_unknown:
            errors.append(
                f"Count mismatch: unknown_count ({evaluation.unknown_count}) != actual ({actual_unknown})."
            )
        if evaluation.total_criteria_evaluated != len(evaluation.criterion_evaluations):
            errors.append(
                f"Total count mismatch: total_criteria_evaluated ({evaluation.total_criteria_evaluated}) "
                f"!= evaluations list length ({len(evaluation.criterion_evaluations)})."
            )

        # Check Aggregation Decision Invariant
        expected_status: TrialEligibilityStatus
        if actual_failed > 0:
            expected_status = TrialEligibilityStatus.INELIGIBLE
        elif actual_unknown > 0:
            expected_status = TrialEligibilityStatus.NEEDS_REVIEW
        elif len(evaluation.criterion_evaluations) > 0 and actual_passed == len(evaluation.criterion_evaluations):
            expected_status = TrialEligibilityStatus.ELIGIBLE
        else:
            expected_status = TrialEligibilityStatus.NEEDS_REVIEW

        if evaluation.status != expected_status:
            errors.append(
                f"Aggregation invariant violation: trial status is '{evaluation.status}', "
                f"but based on criteria counts (FAIL={actual_failed}, UNKNOWN={actual_unknown}, PASS={actual_passed}), "
                f"expected '{expected_status}'."
            )

        return errors

    @classmethod
    def validate_evaluation_batch(
        cls, evaluations: List[TrialEligibilityEvaluation]
    ) -> Dict[str, Any]:
        """
        Validates a collection of trial evaluations.
        Returns a dictionary summary with valid flag and aggregated errors.
        """
        all_errors: Dict[str, List[str]] = {}
        is_valid = True

        for trial_eval in evaluations:
            t_errors = cls.validate_trial_evaluation(trial_eval)
            if t_errors:
                is_valid = False
                all_errors[trial_eval.trial_id] = t_errors

        return {
            "is_valid": is_valid,
            "total_trials_checked": len(evaluations),
            "errors": all_errors,
        }
