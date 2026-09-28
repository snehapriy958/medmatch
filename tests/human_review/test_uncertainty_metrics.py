"""
Tests for Phase 9 Uncertainty and Human Review Metrics Calculator.
Verifies mathematical formulations, denominator safety, and guardrail enforcement.
"""

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
from scripts.uncertainty_metrics import (
    UncertaintyMetricsCalculator,
    UncertaintyMetricsReport,
)


def test_zero_denominator_safeguards():
    """Verify that empty inputs yield safe zero/one default rates without ZeroDivisionError."""
    report = UncertaintyMetricsCalculator.calculate_metrics([])
    assert report.total_cases_evaluated == 0
    assert report.total_criteria_evaluated == 0
    assert report.uncertainty_rate == 0.0
    assert report.missing_information_rate == 0.0
    assert report.conflict_rate == 0.0
    assert report.ambiguity_rate == 0.0
    assert report.insufficient_evidence_rate == 0.0
    assert report.review_routing_rate == 0.0
    assert report.review_resolution_rate == 1.0
    assert report.escalation_rate == 0.0
    assert report.appropriate_review_routing_rate == 1.0
    assert report.unsupported_automatic_decision_rate == 0.0
    assert report.evidence_backed_resolution_rate == 1.0


def test_populated_metrics_calculation():
    """Verify metrics calculation across multiple simulated cases."""
    # Case 1: Clean eligible, no review
    c1_prof = UncertaintyProfile(case_id="C1", records=[])
    c1_rev = HumanReviewRecord(
        review_id="R1",
        case_or_patient_ref="C1",
        trial_or_criterion_ref="T1",
        status=ReviewStatus.NOT_REQUIRED,
        priority=ReviewPriority.ROUTINE,
        original_machine_output={},
    )

    # Case 2: Missing fact, pending review
    u2 = UncertaintyRecord(
        uncertainty_id="U2",
        subject="HER2",
        fact_or_criterion_ref="CRIT-1",
        status=UncertaintyStatus.MISSING,
        uncertainty_type=UncertaintyType.MISSING_PATIENT_FACT,
        description="Missing HER2",
        affected_criterion="CRIT-1",
        severity=UncertaintySeverity.HIGH,
        review_required=True,
        machine_decision_allowed=False,
        reason="Missing",
    )
    c2_prof = UncertaintyProfile(case_id="C2", records=[u2])
    c2_rev = HumanReviewRecord(
        review_id="R2",
        case_or_patient_ref="C2",
        trial_or_criterion_ref="T2",
        status=ReviewStatus.PENDING_REVIEW,
        priority=ReviewPriority.PRIORITY,
        original_machine_output={},
    )

    # Case 3: Conflicting documents, resolved review with evidence
    u3 = UncertaintyRecord(
        uncertainty_id="U3",
        subject="histology",
        fact_or_criterion_ref="CRIT-2",
        status=UncertaintyStatus.CONFLICTING,
        uncertainty_type=UncertaintyType.CONFLICTING_DOCUMENTS,
        description="Conflicting histology",
        affected_criterion="CRIT-2",
        severity=UncertaintySeverity.HIGH,
        review_required=True,
        machine_decision_allowed=False,
        reason="Conflict",
        conflict_details=[
            {"source_id": "D1", "source_type": "NOTE", "asserted_value": "V1"},
            {"source_id": "D2", "source_type": "NOTE", "asserted_value": "V2"},
        ],
    )
    c3_prof = UncertaintyProfile(case_id="C3", records=[u3])
    c3_rev = HumanReviewRecord(
        review_id="R3",
        case_or_patient_ref="C3",
        trial_or_criterion_ref="T3",
        status=ReviewStatus.RESOLVED,
        priority=ReviewPriority.PRIORITY,
        reviewer_decision=ReviewerDecision.RESOLVE_PASS,
        reviewer_rationale="Resolved with slide review",
        evidence_references=["SLIDE-REV-01"],
        original_machine_output={},
    )

    cases_data = [
        {"case_id": "C1", "criteria_count": 2, "uncertainty_profile": c1_prof, "review_record": c1_rev, "expected_routing": ReviewStatus.NOT_REQUIRED},
        {"case_id": "C2", "criteria_count": 2, "uncertainty_profile": c2_prof, "review_record": c2_rev, "expected_routing": ReviewStatus.PENDING_REVIEW},
        {"case_id": "C3", "criteria_count": 2, "uncertainty_profile": c3_prof, "review_record": c3_rev, "expected_routing": ReviewStatus.PENDING_REVIEW},
    ]

    report = UncertaintyMetricsCalculator.calculate_metrics(cases_data)

    assert report.total_cases_evaluated == 3
    assert report.total_criteria_evaluated == 6
    assert report.total_uncertainties_logged == 2

    # 2 unresolved criteria out of 6 -> 2/6 = 0.3333
    assert report.uncertainty_rate == 0.3333
    # 1 missing out of 6 -> 1/6 = 0.1667
    assert report.missing_information_rate == 0.1667
    # 1 conflict out of 6 -> 1/6 = 0.1667
    assert report.conflict_rate == 0.1667

    # 2 routed cases out of 3 -> 2/3 = 0.6667
    assert report.review_routing_rate == 0.6667
    # 1 resolved out of 2 routed -> 1/2 = 0.5
    assert report.review_resolution_rate == 0.5
    # 1 resolved review and it had evidence -> 1.0
    assert report.evidence_backed_resolution_rate == 1.0
    # Guardrail: zero unsupported automatic decisions
    assert report.unsupported_automatic_decision_rate == 0.0
