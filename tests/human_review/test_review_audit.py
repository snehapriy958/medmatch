"""
Tests for Phase 9 Human Review Audit Trail and Resolution Manager.
Verifies event immutability, evidence requirement enforcement, and machine output preservation.
"""

import pytest

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
    ReviewResolutionRequest,
    ReviewStatus,
    ReviewerDecision,
)
from scripts.review_audit import (
    AuditEventType,
    ReviewAuditTrail,
    ReviewResolutionManager,
)


def make_sample_record() -> HumanReviewRecord:
    return HumanReviewRecord(
        review_id="REV-AUDIT-01",
        case_or_patient_ref="PT-01",
        trial_or_criterion_ref="NCT-01",
        uncertainty_references=["UNC-01"],
        status=ReviewStatus.PENDING_REVIEW,
        priority=ReviewPriority.PRIORITY,
        original_machine_output={
            "machine_status": "NEEDS_REVIEW",
            "reasoning": "Original ungrounded machine reasoning text",
        },
    )


def test_start_review_transitions_to_in_review():
    """Verify start_review transitions status and records an audit event."""
    rec = make_sample_record()
    trail = ReviewAuditTrail(review_id=rec.review_id)

    updated = ReviewResolutionManager.start_review(rec, reviewer_id="REV-001", audit_trail=trail)
    assert updated.status == ReviewStatus.IN_REVIEW
    assert updated.reviewer_ref == "REV-001"
    assert len(trail.events) == 1
    assert trail.events[0].event_type == AuditEventType.REVIEW_STARTED
    assert trail.events[0].new_state == "IN_REVIEW"


def test_resolve_review_with_evidence_and_preserves_machine_output():
    """Verify clean resolution with evidence citations and immutability of machine output."""
    rec = make_sample_record()
    trail = ReviewAuditTrail(review_id=rec.review_id)
    ReviewResolutionManager.start_review(rec, reviewer_id="REV-001", audit_trail=trail)

    unc = UncertaintyRecord(
        uncertainty_id="UNC-01",
        subject="biomarker",
        fact_or_criterion_ref="C1",
        status=UncertaintyStatus.MISSING,
        uncertainty_type=UncertaintyType.MISSING_PATIENT_FACT,
        description="Missing lab",
        severity=UncertaintySeverity.HIGH,
        review_required=True,
        machine_decision_allowed=False,
        reason="Required lab missing",
    )
    prof = UncertaintyProfile(case_id="PT-01", records=[unc])

    req = ReviewResolutionRequest(
        review_id=rec.review_id,
        reviewer_id="REV-001",
        decision=ReviewerDecision.RESOLVE_PASS,
        rationale="Outside laboratory assay confirms biomarker positive status.",
        evidence_references=["EXT-LAB-999"],
    )

    resolved = ReviewResolutionManager.resolve_review(rec, req, trail, uncertainty_profile=prof)
    assert resolved.status == ReviewStatus.RESOLVED
    assert resolved.reviewer_decision == ReviewerDecision.RESOLVE_PASS
    assert resolved.resolution_timestamp is not None
    assert "EXT-LAB-999" in resolved.evidence_references

    # Machine output must be completely intact
    assert resolved.original_machine_output["machine_status"] == "NEEDS_REVIEW"
    assert resolved.original_machine_output["reasoning"] == "Original ungrounded machine reasoning text"

    # Uncertainty in profile should be transitioned to RESOLVED
    assert unc.status == UncertaintyStatus.RESOLVED

    # Audit events must be appended
    assert len(trail.events) >= 3


def test_resolve_review_without_evidence_rejected():
    """Verify that resolution manager rejects override without evidence references."""
    rec = make_sample_record()
    trail = ReviewAuditTrail(review_id=rec.review_id)
    ReviewResolutionManager.start_review(rec, reviewer_id="REV-001", audit_trail=trail)

    # ResolutionRequest Pydantic validator will reject empty evidence_references
    with pytest.raises(Exception, match="requires at least one evidence reference"):
        ReviewResolutionRequest(
            review_id=rec.review_id,
            reviewer_id="REV-001",
            decision=ReviewerDecision.RESOLVE_PASS,
            rationale="Trying to override without evidence",
            evidence_references=[],
        )


def test_escalate_review_transitions_to_escalated():
    """Verify review escalation records escalation event and rationale."""
    rec = make_sample_record()
    trail = ReviewAuditTrail(review_id=rec.review_id)
    ReviewResolutionManager.start_review(rec, reviewer_id="REV-002", audit_trail=trail)

    req = ReviewResolutionRequest(
        review_id=rec.review_id,
        reviewer_id="REV-002",
        decision=ReviewerDecision.ESCALATE,
        rationale="Patient has severe conflicting autoimmune contraindications.",
        evidence_references=["NOTE-IMMUNO-01"],
        escalation_reason="Severe conflicting contraindication requires PI safety review",
    )

    escalated = ReviewResolutionManager.resolve_review(rec, req, trail)
    assert escalated.status == ReviewStatus.ESCALATED
    assert escalated.reviewer_decision == ReviewerDecision.ESCALATE
    assert trail.events[-1].event_type == AuditEventType.REVIEW_ESCALATED
