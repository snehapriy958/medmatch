"""
Tests for Phase 9 Canonical Human Review Schema.
Verifies review states, decisions, priority, and resolution request constraints.
"""

import pytest
from pydantic import ValidationError

from scripts.review_schema import (
    HumanReviewRecord,
    ReviewPriority,
    ReviewResolutionRequest,
    ReviewStatus,
    ReviewerDecision,
    ReviewerIdentity,
)


def test_review_enums():
    """Verify review status, decisions, and priority enums."""
    assert ReviewStatus.NOT_REQUIRED.value == "NOT_REQUIRED"
    assert ReviewStatus.PENDING_REVIEW.value == "PENDING_REVIEW"
    assert ReviewStatus.IN_REVIEW.value == "IN_REVIEW"
    assert ReviewStatus.RESOLVED.value == "RESOLVED"
    assert ReviewStatus.ESCALATED.value == "ESCALATED"

    assert ReviewerDecision.CONFIRM_PASS.value == "CONFIRM_PASS"
    assert ReviewerDecision.CONFIRM_FAIL.value == "CONFIRM_FAIL"
    assert ReviewerDecision.RESOLVE_PASS.value == "RESOLVE_PASS"
    assert ReviewerDecision.RESOLVE_FAIL.value == "RESOLVE_FAIL"
    assert ReviewerDecision.INSUFFICIENT_EVIDENCE.value == "INSUFFICIENT_EVIDENCE"
    assert ReviewerDecision.ESCALATE.value == "ESCALATE"

    assert ReviewPriority.ROUTINE.value == "ROUTINE"
    assert ReviewPriority.PRIORITY.value == "PRIORITY"
    assert ReviewPriority.ESCALATED.value == "ESCALATED"


def test_valid_pending_review_record():
    """Verify creation of a valid pending review record."""
    rec = HumanReviewRecord(
        review_id="REV-001",
        case_or_patient_ref="PT-01",
        trial_or_criterion_ref="NCT-01",
        uncertainty_references=["UNC-01"],
        status=ReviewStatus.PENDING_REVIEW,
        priority=ReviewPriority.PRIORITY,
        original_machine_output={"machine_status": "NEEDS_REVIEW"},
    )
    assert rec.status == ReviewStatus.PENDING_REVIEW
    assert rec.priority == ReviewPriority.PRIORITY
    assert rec.original_machine_output["machine_status"] == "NEEDS_REVIEW"


def test_resolved_review_requires_decision_and_rationale():
    """Status RESOLVED must specify reviewer_decision and reviewer_rationale."""
    with pytest.raises(ValidationError, match="must specify reviewer_decision"):
        HumanReviewRecord(
            review_id="REV-ERR-01",
            case_or_patient_ref="PT-01",
            trial_or_criterion_ref="NCT-01",
            status=ReviewStatus.RESOLVED,
            original_machine_output={},
        )


def test_override_resolution_request_strictly_requires_evidence():
    """ReviewResolutionRequest with RESOLVE_PASS/RESOLVE_FAIL must reject empty evidence_references."""
    # Attempting to override without evidence
    with pytest.raises(ValidationError, match="strictly requires at least one evidence reference"):
        ReviewResolutionRequest(
            review_id="REV-01",
            reviewer_id="REV-USR-01",
            decision=ReviewerDecision.RESOLVE_PASS,
            rationale="Overriding to pass without documentation",
            evidence_references=[],  # VIOLATION
        )

    # With evidence
    valid_req = ReviewResolutionRequest(
        review_id="REV-01",
        reviewer_id="REV-USR-01",
        decision=ReviewerDecision.RESOLVE_PASS,
        rationale="External lab report confirms criterion met",
        evidence_references=["EXT-LAB-01"],
    )
    assert valid_req.decision == ReviewerDecision.RESOLVE_PASS
    assert len(valid_req.evidence_references) == 1


def test_synthetic_reviewer_identity():
    """Verify synthetic reviewer structure without PHI or real auth."""
    identity = ReviewerIdentity(
        reviewer_id="REV-SIM-01",
        role="ONCOLOGIST",
        display_name="Dr. Synthetic Reviewer",
    )
    assert identity.reviewer_id == "REV-SIM-01"
    assert identity.role == "ONCOLOGIST"
