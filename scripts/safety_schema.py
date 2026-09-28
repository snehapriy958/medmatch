"""
MedMatch Clinical Safety Schema.
Phase 12: Clinical Safety.

Defines canonical Pydantic models, safety taxonomy enums (S1–S24),
safety gates (GATE-01 to GATE-20), safety invariants (INV-01 to INV-15),
and evaluation data structures.
"""

from __future__ import annotations

import enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SafetySeverity(str, enum.Enum):
    """Clinical safety error severity tiers."""
    CRITICAL = "CRITICAL"  # Potential direct patient harm or regulatory breach
    HIGH = "HIGH"          # Indirect clinical risk, unverified evidence, routing failure
    MEDIUM = "MEDIUM"      # Ambiguity or explainability discrepancy
    LOW = "LOW"            # Formatting / minor offset drift


class DefenseTier(str, enum.Enum):
    """Multi-tiered defense response."""
    PREVENTION = "PREVENTION"      # Intercept and abort transaction
    DETECTION = "DETECTION"        # Flag and record anomaly
    MITIGATION = "MITIGATION"      # Automatically apply conservative safe default
    HUMAN_REVIEW = "HUMAN_REVIEW"  # Escalate case to credentialed clinician


class SafetyTaxonomyCode(str, enum.Enum):
    """Canonical S1–S24 Clinical Safety Error Taxonomy."""
    S1 = "S1"    # Fabricated Patient Fact
    S2 = "S2"    # Fabricated Trial Criterion
    S3 = "S3"    # Unsupported Clinical Inference
    S4 = "S4"    # Missing Info Treated as Negative Evidence
    S5 = "S5"    # UNKNOWN Treated as PASS
    S6 = "S6"    # UNKNOWN Treated as FAIL
    S7 = "S7"    # Contradictory Evidence Ignored
    S8 = "S8"    # Negation Error
    S9 = "S9"    # Temporal Validity Error / Washout Violation
    S10 = "S10"  # Numerical Threshold Error
    S11 = "S11"  # Unit / Measurement Mismatch
    S12 = "S12"  # Compound Criterion Logic Error
    S13 = "S13"  # Critical Trial Omission in Retrieval
    S14 = "S14"  # Unsupported Eligibility Conclusion
    S15 = "S15"  # Hallucinated Explanation
    S16 = "S16"  # Provenance Mismatch
    S17 = "S17"  # Citation / Evidence Semantic Mismatch
    S18 = "S18"  # Human-Review Routing Failure
    S19 = "S19"  # Unsafe Reviewer Override
    S20 = "S20"  # Audit-Trail Loss
    S21 = "S21"  # Cross-Tenant Information Leakage
    S22 = "S22"  # Stale Clinical Information Used
    S23 = "S23"  # Ambiguous Evidence Presented as Definitive
    S24 = "S24"  # Failure to Disclose Insufficient Evidence


class SafetyGateID(str, enum.Enum):
    """Deterministic Safety Gate identifiers."""
    GATE_01 = "GATE-01"  # Patient Fact Provenance Gate
    GATE_02 = "GATE-02"  # Criterion Schema Integrity Gate
    GATE_03 = "GATE-03"  # Retrieval Sufficiency Gate
    GATE_04 = "GATE-04"  # Temporal Evidence Validity Gate
    GATE_05 = "GATE-05"  # Strict Tri-State Evidence Gate
    GATE_06 = "GATE-06"  # Deterministic Numerical Boundary Gate
    GATE_07 = "GATE-07"  # Conservative Temporal Washout Gate
    GATE_08 = "GATE-08"  # Negation Integrity Gate
    GATE_09 = "GATE-09"  # Contradiction Escalation Gate
    GATE_10 = "GATE-10"  # Protocol Discrepancy Gate
    GATE_11 = "GATE-11"  # Open-World Completeness Gate
    GATE_12 = "GATE-12"  # Claim Grounding Verification Gate
    GATE_14 = "GATE-14"  # Deterministic Aggregation Gate
    GATE_15 = "GATE-15"  # Mandatory Human Escalation Gate
    GATE_16 = "GATE-16"  # Auditable Override Gate
    GATE_17 = "GATE-17"  # Explanation Graph Alignment Gate
    GATE_18 = "GATE-18"  # Verbatim Provenance Gate
    GATE_19 = "GATE-19"  # Tenant Boundary Enforcement Gate
    GATE_20 = "GATE-20"  # Fail-Closed Audit Gate


class SafetyInvariantID(str, enum.Enum):
    """Machine-checkable safety invariant identifiers."""
    INV_01 = "INV-01"  # No Fabricated Patient Facts
    INV_02 = "INV-02"  # No Fabricated Trial Criteria
    INV_03 = "INV-03"  # No UNKNOWN -> PASS Conversion
    INV_04 = "INV-04"  # No Missing -> Negative Conversion
    INV_05 = "INV-05"  # No Unsupported Criteria Decisions
    INV_06 = "INV-06"  # No Unsupported Definitive Decisions
    INV_07 = "INV-07"  # Traceable Evidence Mandate
    INV_08 = "INV-08"  # Valid Provenance Offsets
    INV_09 = "INV-09"  # Conflict Disclosure Mandate
    INV_10 = "INV-10"  # Temporal Constraint Verification
    INV_11 = "INV-11"  # Deterministic Numerical Math
    INV_12 = "INV-12"  # Machine Output Preservation
    INV_13 = "INV-13"  # Auditable Overrides Mandate
    INV_14 = "INV-14"  # Graph-Bounded Explanations
    INV_15 = "INV-15"  # Tenant Boundary Preservation


class SafetyGateResult(BaseModel):
    """Outcome of a deterministic safety gate evaluation."""
    gate_id: SafetyGateID
    gate_name: str
    passed: bool
    defense_tier: DefenseTier
    taxonomy_code: Optional[SafetyTaxonomyCode] = None
    severity: Optional[SafetySeverity] = None
    violation_message: Optional[str] = None
    remedial_action_taken: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SafetyMetrics(BaseModel):
    """Deterministic Phase 12 safety metrics (M-S01 to M-S14)."""
    safety_gate_pass_rate: float = Field(..., ge=0.0, le=1.0)
    unsafe_decision_rate: float = Field(..., ge=0.0, le=1.0)
    unsupported_definitive_decision_rate: float = Field(..., ge=0.0, le=1.0)
    unknown_to_pass_violation_rate: float = Field(..., ge=0.0, le=1.0)
    missing_to_negative_violation_rate: float = Field(..., ge=0.0, le=1.0)
    evidence_support_rate: float = Field(..., ge=0.0, le=1.0)
    provenance_validity_rate: float = Field(..., ge=0.0, le=1.0)
    contradiction_disclosure_rate: float = Field(..., ge=0.0, le=1.0)
    temporal_safety_rate: float = Field(..., ge=0.0, le=1.0)
    numerical_safety_rate: float = Field(..., ge=0.0, le=1.0)
    human_review_routing_recall: float = Field(..., ge=0.0, le=1.0)
    human_override_auditability_rate: float = Field(..., ge=0.0, le=1.0)
    explanation_safety_rate: float = Field(..., ge=0.0, le=1.0)
    tenant_isolation_violation_rate: float = Field(..., ge=0.0, le=1.0)
    total_evaluations: int = Field(default=0, ge=0)
    total_gate_checks: int = Field(default=0, ge=0)


class SafetyAblationResult(BaseModel):
    """Outcome of a controlled safety ablation (A-S1 to A-S7)."""
    ablation_id: str
    name: str
    baseline_experiment: str
    treatment_experiment: str
    changed_gate: str
    primary_metric: str
    baseline_value: float
    treatment_value: float
    delta: float
    is_development_fixture_observation_only: bool = True
    clinical_claim_permitted: bool = False
    observation_summary: str


class ErrorInjectionResult(BaseModel):
    """Outcome of a deterministic fault injection test."""
    injection_id: str
    corruption_type: str
    target_gate: SafetyGateID
    defense_tier: DefenseTier
    detected: bool
    mitigated: bool
    prevented: bool
    escalated_to_review: bool
    taxonomy_code: SafetyTaxonomyCode
    details: str


class ErrorInjectionSummary(BaseModel):
    """Comprehensive breakdown of fault injection results across defense tiers."""
    total_injections: int = Field(..., ge=0)
    prevented_count: int = Field(..., ge=0)
    prevention_rate: float = Field(..., ge=0.0, le=1.0)
    detected_count: int = Field(..., ge=0)
    detection_rate: float = Field(..., ge=0.0, le=1.0)
    mitigated_count: int = Field(..., ge=0)
    mitigation_rate: float = Field(..., ge=0.0, le=1.0)
    escalated_to_review_count: int = Field(..., ge=0)
    human_review_routing_rate: float = Field(..., ge=0.0, le=1.0)
    missed_count: int = Field(..., ge=0)
    missed_injection_rate: float = Field(..., ge=0.0, le=1.0)
    aggregate_interception_count: int = Field(..., ge=0)
    aggregate_interception_rate: float = Field(..., ge=0.0, le=1.0)
