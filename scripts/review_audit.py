"""
MedMatch Canonical Human Review Audit Trail & Resolution Engine.
Phase 9: Formal Uncertainty & Human Review Foundation.

Defines:
- AuditEventType: uncertainty_detected, review_requested, review_started, evidence_added,
  reviewer_decision_recorded, review_resolved, review_escalated
- AuditEvent: Immutable record of a state transition
- ReviewAuditTrail: Append-only lifecycle container for review cases
- ReviewResolutionManager: Service for transitioning review cases, validating evidence,
  and preserving machine reasoning immutably
"""

from __future__ import annotations

import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

try:
    from scripts.review_schema import (
        HumanReviewRecord,
        ReviewResolutionRequest,
        ReviewStatus,
        ReviewerDecision,
    )
    from scripts.uncertainty_schema import UncertaintyProfile, UncertaintyStatus
except ImportError:
    from review_schema import (
        HumanReviewRecord,
        ReviewResolutionRequest,
        ReviewStatus,
        ReviewerDecision,
    )
    from uncertainty_schema import UncertaintyProfile, UncertaintyStatus


class AuditEventType(str, Enum):
    """
    Immutable audit event taxonomy.
    """
    UNCERTAINTY_DETECTED = "uncertainty_detected"
    REVIEW_REQUESTED = "review_requested"
    REVIEW_STARTED = "review_started"
    EVIDENCE_ADDED = "evidence_added"
    REVIEWER_DECISION_RECORDED = "reviewer_decision_recorded"
    REVIEW_RESOLVED = "review_resolved"
    REVIEW_ESCALATED = "review_escalated"


class AuditEvent(BaseModel):
    """
    Individual immutable audit log entry.
    """
    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(..., min_length=1)
    event_type: AuditEventType = Field(...)
    review_id: str = Field(..., min_length=1)
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    actor: str = Field(..., min_length=1, description="e.g. SYSTEM, REV-001")
    previous_state: Optional[str] = Field(default=None)
    new_state: str = Field(..., min_length=1)
    details: Dict[str, Any] = Field(default_factory=dict)
    evidence_references: List[str] = Field(default_factory=list)


class ReviewAuditTrail(BaseModel):
    """
    Complete chronological audit trail for a review case.
    """
    model_config = ConfigDict(extra="forbid")

    review_id: str = Field(..., min_length=1)
    events: List[AuditEvent] = Field(default_factory=list)

    def append_event(
        self,
        event_type: AuditEventType,
        actor: str,
        previous_state: Optional[str],
        new_state: str,
        details: Optional[Dict[str, Any]] = None,
        evidence_references: Optional[List[str]] = None,
    ) -> AuditEvent:
        event_id = f"EVT-{self.review_id}-{len(self.events) + 1:04d}"
        event = AuditEvent(
            event_id=event_id,
            event_type=event_type,
            review_id=self.review_id,
            actor=actor,
            previous_state=previous_state,
            new_state=new_state,
            details=details or {},
            evidence_references=evidence_references or [],
        )
        self.events.append(event)
        return event


class ReviewResolutionManager:
    """
    Applies review resolutions, validates mandatory evidence requirements,
    and updates audit trails without mutating original machine outputs.
    """

    @staticmethod
    def start_review(
        record: HumanReviewRecord,
        reviewer_id: str,
        audit_trail: ReviewAuditTrail,
    ) -> HumanReviewRecord:
        """
        Transitions case from PENDING_REVIEW to IN_REVIEW.
        """
        if record.status not in (ReviewStatus.PENDING_REVIEW, ReviewStatus.NOT_REQUIRED):
            raise ValueError(f"Cannot start review on case with status {record.status.value}")

        prev_status = record.status.value
        record.status = ReviewStatus.IN_REVIEW
        record.reviewer_ref = reviewer_id
        record.updated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        audit_trail.append_event(
            event_type=AuditEventType.REVIEW_STARTED,
            actor=reviewer_id,
            previous_state=prev_status,
            new_state=ReviewStatus.IN_REVIEW.value,
            details={"reviewer_id": reviewer_id},
        )
        return record

    @staticmethod
    def resolve_review(
        record: HumanReviewRecord,
        request: ReviewResolutionRequest,
        audit_trail: ReviewAuditTrail,
        uncertainty_profile: Optional[UncertaintyProfile] = None,
    ) -> HumanReviewRecord:
        """
        Applies a reviewer's decision to a case, verifying evidence constraints.
        Preserves original_machine_output completely intact.
        """
        if record.status == ReviewStatus.RESOLVED:
            raise ValueError("Review is already RESOLVED and cannot be re-resolved.")

        # Guardrail: Overrides strictly require supporting evidence
        if request.decision in (ReviewerDecision.RESOLVE_PASS, ReviewerDecision.RESOLVE_FAIL):
            if not request.evidence_references:
                raise ValueError(
                    f"Decision {request.decision.value} overrides machine evaluation "
                    f"and strictly requires at least one evidence reference."
                )

        prev_status = record.status.value
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        if request.decision == ReviewerDecision.ESCALATE:
            new_status = ReviewStatus.ESCALATED
            event_type = AuditEventType.REVIEW_ESCALATED
        else:
            new_status = ReviewStatus.RESOLVED
            event_type = AuditEventType.REVIEW_RESOLVED

        record.status = new_status
        record.reviewer_ref = request.reviewer_id
        record.reviewer_decision = request.decision
        record.reviewer_rationale = request.rationale
        record.evidence_references = list(request.evidence_references)
        record.updated_at = now_iso
        record.resolution_timestamp = now_iso

        # Log decision event
        audit_trail.append_event(
            event_type=AuditEventType.REVIEWER_DECISION_RECORDED,
            actor=request.reviewer_id,
            previous_state=prev_status,
            new_state=new_status.value,
            details={
                "decision": request.decision.value,
                "rationale": request.rationale,
                "escalation_reason": request.escalation_reason,
            },
            evidence_references=request.evidence_references,
        )

        # Log completion event
        audit_trail.append_event(
            event_type=event_type,
            actor=request.reviewer_id,
            previous_state=prev_status,
            new_state=new_status.value,
            details={"resolution_timestamp": now_iso},
            evidence_references=request.evidence_references,
        )

        # Update uncertainty profile if provided and successfully resolved
        if uncertainty_profile and new_status == ReviewStatus.RESOLVED:
            for unc_id in record.uncertainty_references:
                for unc_rec in uncertainty_profile.records:
                    if unc_rec.uncertainty_id == unc_id:
                        unc_rec.status = UncertaintyStatus.RESOLVED

        return record
