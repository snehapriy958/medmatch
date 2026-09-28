"""
Tests for Phase 9 Review-Routing Policy and Uncertainty Propagation.
Verifies deterministic decision routing, triage priority calculation, and safety guardrails.
"""

from scripts.uncertainty_schema import (
    ConflictEvidenceItem,
    UncertaintyProfile,
    UncertaintyRecord,
    UncertaintySeverity,
    UncertaintyStatus,
    UncertaintyType,
)
from scripts.review_schema import ReviewPriority, ReviewStatus
from scripts.review_policy import ReviewRoutingPolicy
from scripts.review_priority import ReviewPrioritizer
from scripts.eligibility_schema import (
    CriterionEvaluationRecord,
    CriterionEvaluationStatus,
    CriterionType,
    TrialEligibilityEvaluation,
    TrialEligibilityStatus,
)
from scripts.grounding_schema import (
    ClaimType,
    ContradictionStatus,
    GroundingClaim,
    GroundingEvaluation,
    HallucinationCategory,
    SupportStatus,
)


def make_eval(status: TrialEligibilityStatus, criteria_specs: list) -> TrialEligibilityEvaluation:
    recs = [
        CriterionEvaluationRecord(
            criterion_id=cid,
            trial_id="TRIAL-TEST",
            criterion_type=CriterionType.INCLUSION,
            criterion_text=f"Criterion text for {cid}",
            status=CriterionEvaluationStatus(st),
            reasoning=f"Reasoning for {cid}",
            evidence_citations=[],
            patient_fact_references=[f"FACT-{cid}"] if st in ("PASS", "FAIL") else [],
        )
        for cid, st in criteria_specs
    ]
    return TrialEligibilityEvaluation(
        trial_id="TRIAL-TEST",
        status=status,
        criterion_evaluations=recs,
        total_criteria_evaluated=len(recs),
        passed_count=sum(1 for _, st in criteria_specs if st == "PASS"),
        failed_count=sum(1 for _, st in criteria_specs if st == "FAIL"),
        unknown_count=sum(1 for _, st in criteria_specs if st == "UNKNOWN"),
        clinical_summary="Test summary",
    )


def test_routing_clean_eligible():
    """Clean trial with all PASS and 0 uncertainties routes to NOT_REQUIRED."""
    eval_obj = make_eval(TrialEligibilityStatus.ELIGIBLE, [("C1", "PASS"), ("C2", "PASS")])
    unc_prof = UncertaintyProfile(case_id="P1", trial_id="TRIAL-TEST", records=[])

    status, priority, rationale, unc_ids = ReviewRoutingPolicy.evaluate_routing(eval_obj, unc_prof)
    assert status == ReviewStatus.NOT_REQUIRED
    assert priority == ReviewPriority.ROUTINE
    assert len(unc_ids) == 0


def test_routing_eligible_with_unresolved_uncertainty_blocked():
    """Machine declares ELIGIBLE, but an unresolved uncertainty exists; blocks autonomous decision."""
    eval_obj = make_eval(TrialEligibilityStatus.ELIGIBLE, [("C1", "PASS")])
    unc = UncertaintyRecord(
        uncertainty_id="UNC-01",
        subject="biomarker",
        fact_or_criterion_ref="C1",
        status=UncertaintyStatus.MISSING,
        uncertainty_type=UncertaintyType.MISSING_PATIENT_FACT,
        description="Missing confirmatory assay",
        severity=UncertaintySeverity.HIGH,
        review_required=True,
        machine_decision_allowed=False,
        reason="Required assay missing",
    )
    unc_prof = UncertaintyProfile(case_id="P1", trial_id="TRIAL-TEST", records=[unc])

    status, priority, rationale, unc_ids = ReviewRoutingPolicy.evaluate_routing(eval_obj, unc_prof)
    assert status == ReviewStatus.PENDING_REVIEW
    assert priority == ReviewPriority.PRIORITY
    assert "UNC-01" in unc_ids


def test_routing_clean_ineligible():
    """Clean failure supported by grounded evidence routes to NOT_REQUIRED."""
    eval_obj = make_eval(TrialEligibilityStatus.INELIGIBLE, [("C1", "FAIL")])
    unc_prof = UncertaintyProfile(case_id="P1", trial_id="TRIAL-TEST", records=[])

    status, priority, rationale, unc_ids = ReviewRoutingPolicy.evaluate_routing(eval_obj, unc_prof)
    assert status == ReviewStatus.NOT_REQUIRED
    assert priority == ReviewPriority.ROUTINE


def test_routing_ineligible_with_conflicted_failure_intercepted():
    """Trial declared INELIGIBLE, but the failing criterion has conflicting evidence; routes to review."""
    eval_obj = make_eval(TrialEligibilityStatus.INELIGIBLE, [("C1", "FAIL")])
    unc = UncertaintyRecord(
        uncertainty_id="UNC-CONF-01",
        subject="ejection_fraction",
        fact_or_criterion_ref="C1",
        status=UncertaintyStatus.CONFLICTING,
        uncertainty_type=UncertaintyType.CONFLICTING_DOCUMENTS,
        description="ECHO says 35%, MRI says 52%",
        affected_criterion="C1",
        severity=UncertaintySeverity.HIGH,
        review_required=True,
        machine_decision_allowed=False,
        reason="Discordant imaging modalities",
        conflict_details=[
            ConflictEvidenceItem(source_id="ECHO", source_type="NOTE", asserted_value="35%"),
            ConflictEvidenceItem(source_id="MRI", source_type="NOTE", asserted_value="52%"),
        ],
    )
    unc_prof = UncertaintyProfile(case_id="P1", trial_id="TRIAL-TEST", records=[unc])

    status, priority, rationale, unc_ids = ReviewRoutingPolicy.evaluate_routing(eval_obj, unc_prof)
    assert status == ReviewStatus.PENDING_REVIEW
    assert priority == ReviewPriority.PRIORITY


def test_routing_grounding_contradiction_escalation():
    """Phase 8 grounding contradiction (H6) immediately escalates the case."""
    eval_obj = make_eval(TrialEligibilityStatus.ELIGIBLE, [("C1", "PASS")])
    unc_prof = UncertaintyProfile(case_id="P1", trial_id="TRIAL-TEST", records=[])
    contra_claim = GroundingClaim(
        claim_id="CLM-01",
        claim_text="Contradicted proposition",
        claim_type=ClaimType.PATIENT_FACT,
        support_status=SupportStatus.CONTRADICTED,
        contradiction_status=ContradictionStatus.DIRECT_CONTRADICTION,
        confidence=0.5,
        hallucination_category=HallucinationCategory.H6_CONTRADICTION_OF_SOURCE_EVIDENCE,
    )
    grounding = GroundingEvaluation(
        evaluation_id="GEVAL-TEST",
        trial_id="TRIAL-TEST",
        criterion_id="C1",
        raw_reasoning_text="Reasoning with contradiction",
        claims=[contra_claim],
        citations_audited=[],
        total_claims=1,
        supported_claim_count=0,
        partially_supported_claim_count=0,
        unsupported_claim_count=0,
        contradicted_claim_count=1,
        insufficient_evidence_count=0,
        claim_support_rate=0.0,
        unsupported_claim_rate=0.0,
        contradiction_rate=1.0,
        citation_validity_rate=1.0,
        evidence_coverage=0.0,
        grounding_score=0.0,
        hallucination_rate=1.0,
        evaluator_version="1.0.0",
    )

    status, priority, rationale, unc_ids = ReviewRoutingPolicy.evaluate_routing(
        eval_obj, unc_prof, grounding_evaluation=grounding
    )
    assert status == ReviewStatus.ESCALATED
    assert priority == ReviewPriority.ESCALATED
    assert "contradicted claim" in rationale


def test_review_prioritizer_single_gatekeeper():
    """Trial with 1 UNKNOWN and 1 PASS triggers PRIORITY (single gatekeeper)."""
    eval_obj = make_eval(TrialEligibilityStatus.NEEDS_REVIEW, [("C1", "PASS"), ("C2", "UNKNOWN")])
    unc = UncertaintyRecord(
        uncertainty_id="U1",
        subject="s1",
        fact_or_criterion_ref="C2",
        status=UncertaintyStatus.MISSING,
        uncertainty_type=UncertaintyType.MISSING_PATIENT_FACT,
        description="d1",
        severity=UncertaintySeverity.MEDIUM,
        review_required=True,
        machine_decision_allowed=False,
        reason="r1",
    )
    unc_prof = UncertaintyProfile(case_id="P1", records=[unc])

    priority, reason = ReviewPrioritizer.calculate_priority(unc_prof, trial_evaluation=eval_obj)
    assert priority == ReviewPriority.PRIORITY
    assert "Single gatekeeper criterion" in reason
