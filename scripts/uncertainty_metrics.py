"""
MedMatch Canonical Uncertainty & Human Review Metrics Engine.
Phase 9: Formal Uncertainty & Human Review Foundation.

Defines deterministic mathematical metrics for:
- Uncertainty Rate (UR)
- Missing Information Rate (MIR)
- Conflict Rate (CR)
- Ambiguity Rate (AR)
- Insufficient Evidence Rate (IER)
- Review Routing Rate (RRR)
- Review Resolution Rate (ResR)
- Escalation Rate (ER)
- Appropriate Review Routing Rate (ARRR)
- Unsupported Automatic Decision Rate (UADR)
- Evidence-Backed Resolution Rate (EBRR)

All metrics implement strict zero-denominator safeguards and guardrails.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

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
        ReviewStatus,
        ReviewerDecision,
    )
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
        ReviewStatus,
        ReviewerDecision,
    )


class UncertaintyMetricsReport(BaseModel):
    """
    Strongly typed container of Phase 9 uncertainty and review metrics.
    """
    model_config = ConfigDict(extra="forbid")

    total_cases_evaluated: int = Field(default=0, ge=0)
    total_criteria_evaluated: int = Field(default=0, ge=0)
    total_uncertainties_logged: int = Field(default=0, ge=0)

    uncertainty_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    missing_information_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    conflict_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    ambiguity_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    insufficient_evidence_rate: float = Field(default=0.0, ge=0.0, le=1.0)

    review_routing_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    review_resolution_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    escalation_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    appropriate_review_routing_rate: float = Field(default=1.0, ge=0.0, le=1.0)
    unsupported_automatic_decision_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_backed_resolution_rate: float = Field(default=1.0, ge=0.0, le=1.0)


class UncertaintyMetricsCalculator:
    """
    Deterministic calculation engine for Phase 9 uncertainty metrics.
    """

    @staticmethod
    def calculate_metrics(
        cases_data: List[Dict[str, Any]],
        review_records: Optional[List[HumanReviewRecord]] = None,
    ) -> UncertaintyMetricsReport:
        """
        Computes all Phase 9 metrics across a batch of evaluated cases.

        cases_data format:
        [
            {
                "case_id": str,
                "criteria_count": int,
                "uncertainty_profile": UncertaintyProfile,
                "review_record": HumanReviewRecord,
                "expected_routing": Optional[ReviewStatus],
            },
            ...
        ]
        """
        review_records = review_records or []
        total_cases = len(cases_data)
        total_criteria = sum(c.get("criteria_count", 0) for c in cases_data)
        
        all_uncertainties: List[UncertaintyRecord] = []
        for c in cases_data:
            prof: Optional[UncertaintyProfile] = c.get("uncertainty_profile")
            if prof:
                all_uncertainties.extend(prof.records)

        total_unc = len(all_uncertainties)

        # 1. Uncertainty Rate (criteria with unresolved uncertainty / total criteria)
        unresolved_criteria_refs = {
            r.affected_criterion for r in all_uncertainties
            if r.status != UncertaintyStatus.RESOLVED and r.affected_criterion
        }
        ur = (len(unresolved_criteria_refs) / total_criteria) if total_criteria > 0 else 0.0

        # 2. Missing Information Rate
        missing_count = sum(
            1 for r in all_uncertainties
            if r.uncertainty_type == UncertaintyType.MISSING_PATIENT_FACT
            or r.status == UncertaintyStatus.MISSING
        )
        mir = (missing_count / total_criteria) if total_criteria > 0 else 0.0

        # 3. Conflict Rate
        conflict_count = sum(
            1 for r in all_uncertainties
            if r.uncertainty_type in (
                UncertaintyType.CONFLICTING_PATIENT_FACTS,
                UncertaintyType.CONFLICTING_DOCUMENTS,
                UncertaintyType.GROUNDING_CONTRADICTION,
            )
            or r.status == UncertaintyStatus.CONFLICTING
        )
        cr = (conflict_count / total_criteria) if total_criteria > 0 else 0.0

        # 4. Ambiguity Rate
        ambiguity_count = sum(
            1 for r in all_uncertainties
            if r.uncertainty_type in (
                UncertaintyType.TEMPORAL_AMBIGUITY,
                UncertaintyType.NUMERICAL_AMBIGUITY,
                UncertaintyType.CLINICAL_AMBIGUITY,
            )
            or r.status == UncertaintyStatus.AMBIGUOUS
        )
        ar = (ambiguity_count / total_criteria) if total_criteria > 0 else 0.0

        # 5. Insufficient Evidence Rate
        insufficient_count = sum(
            1 for r in all_uncertainties
            if r.uncertainty_type == UncertaintyType.INSUFFICIENT_RETRIEVAL
            or r.status == UncertaintyStatus.INSUFFICIENT_EVIDENCE
        )
        ier = (insufficient_count / total_criteria) if total_criteria > 0 else 0.0

        # 6. Review Routing Rate (cases routed to review / total cases)
        all_reviews = [c.get("review_record") for c in cases_data if c.get("review_record")]
        routed_cases = sum(
            1 for r in all_reviews
            if r.status in (ReviewStatus.PENDING_REVIEW, ReviewStatus.IN_REVIEW, ReviewStatus.RESOLVED, ReviewStatus.ESCALATED)
        )
        rrr = (routed_cases / total_cases) if total_cases > 0 else 0.0

        # 7. Review Resolution Rate (resolved / total routed)
        resolved_count = sum(1 for r in all_reviews if r.status == ReviewStatus.RESOLVED)
        res_r = (resolved_count / routed_cases) if routed_cases > 0 else 1.0

        # 8. Escalation Rate
        escalated_count = sum(1 for r in all_reviews if r.status == ReviewStatus.ESCALATED)
        er = (escalated_count / total_cases) if total_cases > 0 else 0.0

        # 9. Appropriate Review Routing Rate (matching expected ground truth routing)
        correct_routings = 0
        evaluable_routings = 0
        for c in cases_data:
            expected: Optional[ReviewStatus] = c.get("expected_routing")
            rec: Optional[HumanReviewRecord] = c.get("review_record")
            if expected and rec:
                evaluable_routings += 1
                if rec.status == expected:
                    correct_routings += 1
        arrr = (correct_routings / evaluable_routings) if evaluable_routings > 0 else 1.0

        # 10. Unsupported Automatic Decision Rate
        # Cases where review was marked NOT_REQUIRED despite having unresolved HIGH/CRITICAL uncertainties
        unsupported_auto = 0
        for c in cases_data:
            rec: Optional[HumanReviewRecord] = c.get("review_record")
            prof: Optional[UncertaintyProfile] = c.get("uncertainty_profile")
            if rec and prof and rec.status == ReviewStatus.NOT_REQUIRED:
                has_unresolved_high = any(
                    r.status != UncertaintyStatus.RESOLVED
                    and r.severity in (UncertaintySeverity.HIGH, UncertaintySeverity.CRITICAL)
                    for r in prof.records
                )
                if has_unresolved_high:
                    unsupported_auto += 1
        uadr = (unsupported_auto / total_cases) if total_cases > 0 else 0.0

        # 11. Evidence-Backed Resolution Rate
        # Resolved reviews that provided at least one valid evidence reference
        resolved_reviews = [r for r in all_reviews if r.status == ReviewStatus.RESOLVED]
        evidence_backed_count = sum(1 for r in resolved_reviews if len(r.evidence_references) > 0)
        ebrr = (evidence_backed_count / len(resolved_reviews)) if len(resolved_reviews) > 0 else 1.0

        return UncertaintyMetricsReport(
            total_cases_evaluated=total_cases,
            total_criteria_evaluated=total_criteria,
            total_uncertainties_logged=total_unc,
            uncertainty_rate=round(ur, 4),
            missing_information_rate=round(mir, 4),
            conflict_rate=round(cr, 4),
            ambiguity_rate=round(ar, 4),
            insufficient_evidence_rate=round(ier, 4),
            review_routing_rate=round(rrr, 4),
            review_resolution_rate=round(res_r, 4),
            escalation_rate=round(er, 4),
            appropriate_review_routing_rate=round(arrr, 4),
            unsupported_automatic_decision_rate=round(uadr, 4),
            evidence_backed_resolution_rate=round(ebrr, 4),
        )
