"""
MedMatch Canonical Human Review Decision Schemas & Contracts.
Phase 9: Formal Uncertainty & Human Review Foundation.

Defines strongly-typed Pydantic models for:
- ReviewStatus: NOT_REQUIRED, PENDING_REVIEW, IN_REVIEW, RESOLVED, ESCALATED
- ReviewerDecision: CONFIRM_PASS, CONFIRM_FAIL, RESOLVE_PASS, RESOLVE_FAIL, INSUFFICIENT_EVIDENCE, ESCALATE
- ReviewPriority: ROUTINE, PRIORITY, ESCALATED
- ReviewerIdentity: Synthetic reviewer identity for development/research testing
- HumanReviewRecord: Complete canonical review record preserving original machine reasoning
- ReviewResolutionRequest: Explicit request payload to resolve or escalate a review
"""

from __future__ import annotations

import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# =============================================================================
# 1. Canonical Enumerations
# =============================================================================

class ReviewStatus(str, Enum):
    """
    Workflow state of a human clinical review case.
    """
    NOT_REQUIRED = "NOT_REQUIRED"       # Case deterministically resolved; no human review needed
    PENDING_REVIEW = "PENDING_REVIEW"   # Queued for human clinician assessment
    IN_REVIEW = "IN_REVIEW"             # Claimed and actively being inspected by a reviewer
    RESOLVED = "RESOLVED"               # Formally resolved with a recorded clinical decision
    ESCALATED = "ESCALATED"             # Escalated to senior clinical investigator or safety committee


class ReviewerDecision(str, Enum):
    """
    Formal adjudication decision rendered by a human reviewer.
    """
    CONFIRM_PASS = "CONFIRM_PASS"                   # Agrees with machine PASS verdict
    CONFIRM_FAIL = "CONFIRM_FAIL"                   # Agrees with machine FAIL verdict
    RESOLVE_PASS = "RESOLVE_PASS"                   # Overrides machine UNKNOWN/dispute to PASS with evidence
    RESOLVE_FAIL = "RESOLVE_FAIL"                   # Overrides machine UNKNOWN/dispute to FAIL with evidence
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE" # Confirms evidence remains insufficient; patient excluded or placed on hold
    ESCALATE = "ESCALATE"                           # Refers to multidisciplinary tumor board / panel


class ReviewPriority(str, Enum):
    """
    Deterministic triage priority for review queue sorting.
    Research-only; not an autonomous clinical risk score.
    """
    ROUTINE = "ROUTINE"       # Standard missing non-critical demographic or historical fact
    PRIORITY = "PRIORITY"     # Single blocking inclusion criterion on otherwise eligible candidate
    ESCALATED = "ESCALATED"   # Contradictory contraindication, safety alert, or critical data conflict


# =============================================================================
# 2. Synthetic Reviewer Identity
# =============================================================================

class ReviewerIdentity(BaseModel):
    """
    Synthetic reviewer representation for research simulation and audit trails.
    Contains no PHI and requires no real authentication infrastructure.
    """
    model_config = ConfigDict(extra="forbid")

    reviewer_id: str = Field(..., min_length=1, description="Synthetic reviewer identifier, e.g., REV-001")
    role: str = Field(default="CLINICAL_COORDINATOR", description="e.g., ONCOLOGIST, RESEARCH_NURSE, COORDINATOR")
    display_name: str = Field(default="Synthetic Reviewer", description="Human-readable synthetic display name")


# =============================================================================
# 3. Canonical Human Review Record
# =============================================================================

class HumanReviewRecord(BaseModel):
    """
    Canonical audit record capturing the entire review lifecycle.
    Preserves original machine output immutably; review actions append to this record.
    """
    model_config = ConfigDict(extra="forbid")

    review_id: str = Field(..., min_length=1, description="Unique review case identifier, e.g., REV-CASE-001")
    case_or_patient_ref: str = Field(..., min_length=1, description="Patient ID or Case ID")
    trial_or_criterion_ref: str = Field(..., min_length=1, description="Trial ID or specific Criterion ID under review")
    uncertainty_references: List[str] = Field(default_factory=list, description="List of uncertainty_id references")
    reviewer_ref: Optional[str] = Field(default=None, description="synthetic reviewer_id if claimed")
    status: ReviewStatus = Field(default=ReviewStatus.PENDING_REVIEW, description="Current workflow status")
    priority: ReviewPriority = Field(default=ReviewPriority.ROUTINE, description="Deterministic review priority")
    reviewer_decision: Optional[ReviewerDecision] = Field(default=None, description="Final reviewer decision")
    reviewer_rationale: Optional[str] = Field(default=None, description="Clinical justification for reviewer action")
    evidence_references: List[str] = Field(default_factory=list, description="Citations supporting reviewer action")
    created_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    resolution_timestamp: Optional[str] = Field(default=None, description="ISO timestamp when resolution occurred")
    audit_metadata: Dict[str, Any] = Field(default_factory=dict, description="Operational audit metadata")
    original_machine_output: Dict[str, Any] = Field(
        ...,
        description="Immutable snapshot of the original machine decision and reasoning text"
    )

    @model_validator(mode="after")
    def validate_resolution_consistency(self) -> "HumanReviewRecord":
        """
        Validates that resolved reviews have a decision, rationale, and timestamp.
        """
        if self.status == ReviewStatus.RESOLVED:
            if not self.reviewer_decision:
                raise ValueError("Review marked as RESOLVED must specify reviewer_decision.")
            if not self.reviewer_rationale:
                raise ValueError("Review marked as RESOLVED must provide reviewer_rationale.")
            if not self.resolution_timestamp:
                self.resolution_timestamp = self.updated_at

        if self.status == ReviewStatus.ESCALATED:
            if not self.reviewer_rationale and not self.audit_metadata.get("routing_rationale"):
                raise ValueError("Review marked as ESCALATED must document escalation rationale.")

        return self


# =============================================================================
# 4. Review Resolution Request
# =============================================================================

class ReviewResolutionRequest(BaseModel):
    """
    Contract for resolving or escalating a pending review.
    Enforces evidence citation where required.
    """
    model_config = ConfigDict(extra="forbid")

    review_id: str = Field(..., min_length=1)
    reviewer_id: str = Field(..., min_length=1)
    decision: ReviewerDecision = Field(...)
    rationale: str = Field(..., min_length=5, description="Clinical rationale for decision")
    evidence_references: List[str] = Field(
        default_factory=list,
        description="Must be non-empty for RESOLVE_PASS and RESOLVE_FAIL overrides"
    )
    escalation_reason: Optional[str] = Field(default=None)

    @model_validator(mode="after")
    def validate_evidence_for_resolution(self) -> "ReviewResolutionRequest":
        """
        Overriding an UNKNOWN to PASS or FAIL strictly requires cited evidence.
        """
        if self.decision in (ReviewerDecision.RESOLVE_PASS, ReviewerDecision.RESOLVE_FAIL):
            if not self.evidence_references:
                raise ValueError(
                    f"Decision {self.decision.value} overrides machine output and strictly "
                    f"requires at least one evidence reference in evidence_references."
                )

        if self.decision == ReviewerDecision.ESCALATE and not self.escalation_reason:
            if not self.rationale:
                raise ValueError("ESCALATE decision requires escalation_reason or rationale.")

        return self
