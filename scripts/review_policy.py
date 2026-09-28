"""
MedMatch Deterministic Review-Routing Policy.
Phase 9: Formal Uncertainty & Human Review Foundation.

Implements pure, reproducible routing rules that connect:
- Patient fact uncertainties (Phase 4)
- Criterion-level reasoning & aggregation (Phase 6)
- Evidence grounding evaluations (Phase 8)
- Downstream human review triggers (Phase 9)

Rules:
1. Automatic ELIGIBLE is permitted ONLY if all criteria are PASS, count > 0,
   and zero unresolved uncertainties exist.
2. Automatic INELIGIBLE is permitted if at least one criterion is FAIL with
   grounded evidence and no active contradictions undermining the failure.
3. NEEDS_REVIEW is strictly required whenever:
   - Any criterion is UNKNOWN
   - Required patient facts are missing
   - Conflicting facts or documents exist
   - Temporal or numerical ambiguity affects a criterion
   - Retrieval evidence is insufficient
   - Machine reasoning contains UNSUPPORTED or CONTRADICTED claims (H1, H3, H6, H8)
   - Machine displays unsupported certainty
4. ESCALATED routing occurs when critical contradictions or safety conflicts exist.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
try:
    from scripts.uncertainty_schema import (
        UncertaintyProfile,
        UncertaintyRecord,
        UncertaintySeverity,
        UncertaintyStatus,
        UncertaintyType,
    )
    from scripts.review_schema import (
        HumanReviewRecord,
        ReviewPriority,
        ReviewStatus,
        ReviewerDecision,
    )
    from scripts.eligibility_schema import (
        CriterionEvaluationRecord,
        CriterionEvaluationStatus,
        TrialEligibilityEvaluation,
        TrialEligibilityStatus,
    )
    from scripts.grounding_schema import (
        GroundingClaim,
        GroundingEvaluation,
        SupportStatus,
    )
    from scripts.review_priority import ReviewPrioritizer
except ImportError:
    from uncertainty_schema import (
        UncertaintyProfile,
        UncertaintyRecord,
        UncertaintySeverity,
        UncertaintyStatus,
        UncertaintyType,
    )
    from review_schema import (
        HumanReviewRecord,
        ReviewPriority,
        ReviewStatus,
        ReviewerDecision,
    )
    from eligibility_schema import (
        CriterionEvaluationRecord,
        CriterionEvaluationStatus,
        TrialEligibilityEvaluation,
        TrialEligibilityStatus,
    )
    from grounding_schema import (
        GroundingClaim,
        GroundingEvaluation,
        SupportStatus,
    )
    from review_priority import ReviewPrioritizer


class ReviewRoutingPolicy:
    """
    Deterministic clinical review routing policy engine.
    """

    @staticmethod
    def evaluate_routing(
        trial_evaluation: TrialEligibilityEvaluation,
        uncertainty_profile: UncertaintyProfile,
        grounding_evaluation: Optional[GroundingEvaluation] = None,
        claims: Optional[List[GroundingClaim]] = None,
    ) -> Tuple[ReviewStatus, ReviewPriority, str, List[str]]:
        """
        Evaluates trial evaluation, uncertainty records, and grounding to determine
        exact review routing status, priority, justification, and triggered uncertainty IDs.

        Returns:
            (review_status, priority, routing_rationale, triggered_uncertainty_ids)
        """
        triggered_uncertainty_ids = [
            r.uncertainty_id for r in uncertainty_profile.records
            if r.status != UncertaintyStatus.RESOLVED and r.review_required
        ]

        # 1. Check for Critical Escalation Triggers
        critical_records = [
            r for r in uncertainty_profile.records
            if r.status != UncertaintyStatus.RESOLVED and r.severity == UncertaintySeverity.CRITICAL
        ]
        if critical_records:
            reasons = "; ".join(f"{r.uncertainty_id}: {r.reason}" for r in critical_records)
            return (
                ReviewStatus.ESCALATED,
                ReviewPriority.ESCALATED,
                f"Escalated due to critical safety or contradiction uncertainty: {reasons}",
                triggered_uncertainty_ids,
            )

        # Check for Grounding Contradictions (H6)
        if grounding_evaluation and grounding_evaluation.contradicted_claim_count > 0:
            return (
                ReviewStatus.ESCALATED,
                ReviewPriority.ESCALATED,
                f"Escalated due to {grounding_evaluation.contradicted_claim_count} contradicted claim(s) "
                f"detected in machine reasoning.",
                triggered_uncertainty_ids,
            )

        # 2. Check for Grounding Failures (Unsupported Claims / H1, H3, H8)
        if grounding_evaluation and grounding_evaluation.unsupported_claim_count > 0:
            # If an unsupported claim was made in machine reasoning, intercept automatic decision
            return (
                ReviewStatus.PENDING_REVIEW,
                ReviewPriority.PRIORITY,
                f"Routed to review due to {grounding_evaluation.unsupported_claim_count} unsupported "
                f"claim(s) in automated reasoning.",
                triggered_uncertainty_ids,
            )

        # 3. Check for Phase 6 Trial-Level Aggregation State
        if trial_evaluation.status == TrialEligibilityStatus.NEEDS_REVIEW:
            priority, priority_reason = ReviewPrioritizer.calculate_priority(
                uncertainty_profile=uncertainty_profile,
                trial_evaluation=trial_evaluation,
                grounding_evaluation=grounding_evaluation,
            )
            
            reason_str = "; ".join(
                f"Criterion {e.criterion_id} UNKNOWN" for e in trial_evaluation.criterion_evaluations
                if e.status == CriterionEvaluationStatus.UNKNOWN
            ) or "Trial status is NEEDS_REVIEW"

            return (
                ReviewStatus.PENDING_REVIEW,
                priority,
                f"Human review required: {reason_str}",
                triggered_uncertainty_ids,
            )

        # 4. Check INELIGIBLE status
        if trial_evaluation.status == TrialEligibilityStatus.INELIGIBLE:
            # Even if trial is INELIGIBLE, if any FAIL criterion has an active contradiction
            # or severe conflict, it requires review; otherwise automatic INELIGIBLE stands.
            conflicted_criteria = {
                r.affected_criterion for r in uncertainty_profile.records
                if r.status in (UncertaintyStatus.CONFLICTING, UncertaintyStatus.AMBIGUOUS)
                and r.affected_criterion is not None
            }
            failing_criteria = {
                e.criterion_id for e in trial_evaluation.criterion_evaluations
                if e.status == CriterionEvaluationStatus.FAIL
            }
            # If any failure is in conflict, route to review
            if failing_criteria.intersection(conflicted_criteria):
                return (
                    ReviewStatus.PENDING_REVIEW,
                    ReviewPriority.PRIORITY,
                    "Failing criterion has conflicting or ambiguous evidence; human confirmation required.",
                    triggered_uncertainty_ids,
                )

            # Clean INELIGIBLE: Deterministically verified disqualification
            return (
                ReviewStatus.NOT_REQUIRED,
                ReviewPriority.ROUTINE,
                "Deterministic disqualification verified by grounded evidence; no review required.",
                [],
            )

        # 5. Check ELIGIBLE status
        if trial_evaluation.status == TrialEligibilityStatus.ELIGIBLE:
            # Automatic ELIGIBLE permitted ONLY if 0 unresolved uncertainties exist
            if uncertainty_profile.unresolved_count > 0:
                return (
                    ReviewStatus.PENDING_REVIEW,
                    ReviewPriority.PRIORITY,
                    f"Trial evaluated as ELIGIBLE by machine, but {uncertainty_profile.unresolved_count} "
                    f"unresolved uncertainty record(s) require clinician review before confirmation.",
                    triggered_uncertainty_ids,
                )

            return (
                ReviewStatus.NOT_REQUIRED,
                ReviewPriority.ROUTINE,
                "Deterministic eligibility confirmed with full evidence and zero uncertainties.",
                [],
            )

        # Fallback safeguard
        return (
            ReviewStatus.PENDING_REVIEW,
            ReviewPriority.ROUTINE,
            "Indeterminate state; routed to review by safety policy.",
            triggered_uncertainty_ids,
        )

    @staticmethod
    def create_review_record(
        review_id: str,
        case_id: str,
        trial_id: str,
        trial_evaluation: TrialEligibilityEvaluation,
        uncertainty_profile: UncertaintyProfile,
        grounding_evaluation: Optional[GroundingEvaluation] = None,
    ) -> HumanReviewRecord:
        """
        Creates a HumanReviewRecord from trial evaluation and uncertainty profile.
        Preserves original machine output immutably.
        """
        status, priority, rationale, unc_ids = ReviewRoutingPolicy.evaluate_routing(
            trial_evaluation=trial_evaluation,
            uncertainty_profile=uncertainty_profile,
            grounding_evaluation=grounding_evaluation,
        )

        original_output = {
            "trial_id": trial_id,
            "case_id": case_id,
            "machine_status": trial_evaluation.status.value,
            "criterion_evaluations": [
                {
                    "criterion_id": e.criterion_id,
                    "status": e.status.value,
                    "reasoning": e.reasoning,
                    "citations": [c.model_dump() for c in e.evidence_citations],
                }
                for e in trial_evaluation.criterion_evaluations
            ],
            "grounding_score": grounding_evaluation.grounding_score if grounding_evaluation else None,
            "hallucination_score": grounding_evaluation.hallucination_rate if grounding_evaluation else None,
        }

        return HumanReviewRecord(
            review_id=review_id,
            case_or_patient_ref=case_id,
            trial_or_criterion_ref=trial_id,
            uncertainty_references=unc_ids,
            status=status,
            priority=priority,
            reviewer_decision=None,
            reviewer_rationale=rationale if status == ReviewStatus.ESCALATED else None,
            evidence_references=[],
            audit_metadata={"routing_rationale": rationale},
            original_machine_output=original_output,
        )
