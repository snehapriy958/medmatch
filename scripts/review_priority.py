"""
MedMatch Deterministic Review Prioritization Engine.
Phase 9: Formal Uncertainty & Human Review Foundation.

Computes explainable, deterministic triage priority for cases routed to human review.
Categories:
- ROUTINE: Non-blocking or secondary criteria uncertainties
- PRIORITY: High-impact single gatekeeper criterion on candidate or grounding failure
- ESCALATED: Active safety contradiction, conflicting contraindication, or critical clinical conflict

Purely rule-based and auditable. Not a clinical urgency score.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
try:
    from scripts.uncertainty_schema import (
        UncertaintyProfile,
        UncertaintyRecord,
        UncertaintySeverity,
        UncertaintyStatus,
    )
    from scripts.review_schema import ReviewPriority
    from scripts.eligibility_schema import (
        CriterionEvaluationStatus,
        TrialEligibilityEvaluation,
        TrialEligibilityStatus,
    )
    from scripts.grounding_schema import GroundingEvaluation
except ImportError:
    from uncertainty_schema import (
        UncertaintyProfile,
        UncertaintyRecord,
        UncertaintySeverity,
        UncertaintyStatus,
    )
    from review_schema import ReviewPriority
    from eligibility_schema import (
        CriterionEvaluationStatus,
        TrialEligibilityEvaluation,
        TrialEligibilityStatus,
    )
    from grounding_schema import GroundingEvaluation


class ReviewPrioritizer:
    """
    Deterministic prioritization engine for human review queue.
    """

    @staticmethod
    def calculate_priority(
        uncertainty_profile: UncertaintyProfile,
        trial_evaluation: Optional[TrialEligibilityEvaluation] = None,
        grounding_evaluation: Optional[GroundingEvaluation] = None,
    ) -> Tuple[ReviewPriority, str]:
        """
        Calculates review priority and produces a structured explanation.

        Returns:
            (ReviewPriority, rationale_string)
        """
        # Rule 1: Any CRITICAL severity uncertainty triggers ESCALATED
        critical_records = [
            r for r in uncertainty_profile.records
            if r.status != UncertaintyStatus.RESOLVED and r.severity == UncertaintySeverity.CRITICAL
        ]
        if critical_records:
            return (
                ReviewPriority.ESCALATED,
                f"Escalated priority due to {len(critical_records)} critical clinical safety uncertainty record(s)."
            )

        # Rule 2: Grounding contradiction (H6) triggers ESCALATED
        if grounding_evaluation and grounding_evaluation.contradicted_claim_count > 0:
            return (
                ReviewPriority.ESCALATED,
                f"Escalated priority due to {grounding_evaluation.contradicted_claim_count} "
                f"contradicted claim(s) in reasoning output."
            )

        # Rule 3: Single Gatekeeper Criterion on otherwise ELIGIBLE candidate
        # If no criteria FAIL, and exactly 1 criterion is UNKNOWN, this single criterion
        # is the sole blocker preventing trial enrollment -> PRIORITY
        if trial_evaluation and trial_evaluation.status == TrialEligibilityStatus.NEEDS_REVIEW:
            unknown_count = sum(
                1 for e in trial_evaluation.criterion_evaluations
                if e.status == CriterionEvaluationStatus.UNKNOWN
            )
            pass_count = sum(
                1 for e in trial_evaluation.criterion_evaluations
                if e.status == CriterionEvaluationStatus.PASS
            )
            if unknown_count == 1 and pass_count > 0:
                return (
                    ReviewPriority.PRIORITY,
                    "High priority: Single gatekeeper criterion is UNKNOWN on an otherwise PASSing candidate."
                )

        # Rule 4: HIGH severity uncertainty or Grounding failure triggers PRIORITY
        has_high = any(
            r.severity == UncertaintySeverity.HIGH
            for r in uncertainty_profile.records
            if r.status != UncertaintyStatus.RESOLVED
        )
        if has_high:
            return (
                ReviewPriority.PRIORITY,
                "High priority due to presence of HIGH severity clinical uncertainties."
            )

        if grounding_evaluation and grounding_evaluation.unsupported_claim_count > 0:
            return (
                ReviewPriority.PRIORITY,
                f"High priority due to {grounding_evaluation.unsupported_claim_count} unsupported claim(s) "
                f"requiring clinician verification."
            )

        # Rule 5: Multiple unresolved criteria (> 3) increase triage urgency
        if uncertainty_profile.unresolved_count >= 3:
            return (
                ReviewPriority.PRIORITY,
                f"High priority due to accumulation of {uncertainty_profile.unresolved_count} unresolved uncertainties."
            )

        # Default fallback: ROUTINE
        return (
            ReviewPriority.ROUTINE,
            "Routine priority: Standard missing historical or demographic information."
        )
