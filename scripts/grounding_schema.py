"""
MedMatch Canonical Evidence Grounding & Hallucination Schemas.
Phase 8: Grounding Evaluation & Faithfulness Auditing.

Defines strongly-typed Pydantic models for:
- SupportStatus (SUPPORTED, PARTIALLY_SUPPORTED, UNSUPPORTED, CONTRADICTED, INSUFFICIENT_EVIDENCE)
- ClaimType (PATIENT_FACT, TRIAL_CRITERION, TEMPORAL_FACT, NUMERICAL_VALUE, ELIGIBILITY_CONCLUSION, INFERRED_CLAIM)
- ContradictionStatus (NO_CONTRADICTION, DIRECT_CONTRADICTION, ASSERTION_CONFLICT, TEMPORAL_CONFLICT)
- EvidenceSourceType (PATIENT_FACT, PATIENT_NOTE, PATIENT_DEMOGRAPHICS, TRIAL_CRITERION, TRIAL_SUMMARY, RETRIEVED_PROTOCOL)
- HallucinationCategory (H1 through H10)
- GroundingEvidence (atomic verified source truth item)
- GroundingClaim (extracted atomic proposition from generated reasoning)
- CitationValidationRecord (verification of an individual citation)
- GroundingEvaluation (comprehensive criterion- or trial-level grounding evaluation)
"""

from __future__ import annotations

import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# =============================================================================
# 1. Enums & Ontological States
# =============================================================================

class SupportStatus(str, Enum):
    """
    Epistemic support state of a generated claim relative to verified evidence.
    Must never be collapsed into PASS/FAIL/UNKNOWN.
    """
    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class ClaimType(str, Enum):
    """
    Taxonomic category of an atomic proposition extracted from reasoning text.
    """
    PATIENT_FACT = "PATIENT_FACT"                 # e.g., "Patient has stage IV adenocarcinoma"
    TRIAL_CRITERION = "TRIAL_CRITERION"           # e.g., "Trial requires age >= 18"
    TEMPORAL_FACT = "TEMPORAL_FACT"               # e.g., "Diagnosed within past 6 months"
    NUMERICAL_VALUE = "NUMERICAL_VALUE"           # e.g., "ECOG is 1", "HbA1c is 7.2%"
    ELIGIBILITY_CONCLUSION = "ELIGIBILITY_CONCLUSION"  # e.g., "Patient meets inclusion criterion"
    INFERRED_CLAIM = "INFERRED_CLAIM"             # e.g., "Patient likely tolerates immunotherapy"


class ContradictionStatus(str, Enum):
    """
    Specific contradiction classification when conflict occurs.
    """
    NO_CONTRADICTION = "NO_CONTRADICTION"
    DIRECT_CONTRADICTION = "DIRECT_CONTRADICTION"         # e.g., asserted PRESENT but evidence says ABSENT
    ASSERTION_CONFLICT = "ASSERTION_CONFLICT"             # e.g., negated in facts but affirmed in claim
    TEMPORAL_CONFLICT = "TEMPORAL_CONFLICT"               # e.g., occurred 3 years ago vs. required <= 1 year
    NUMERICAL_CONFLICT = "NUMERICAL_CONFLICT"             # e.g., reported 45 vs. required >= 50


class EvidenceSourceType(str, Enum):
    """
    Origin of verified ground-truth evidence.
    """
    PATIENT_FACT = "PATIENT_FACT"
    PATIENT_NOTE = "PATIENT_NOTE"
    PATIENT_DEMOGRAPHICS = "PATIENT_DEMOGRAPHICS"
    TRIAL_CRITERION = "TRIAL_CRITERION"
    TRIAL_SUMMARY = "TRIAL_SUMMARY"
    RETRIEVED_PROTOCOL = "RETRIEVED_PROTOCOL"


class HallucinationCategory(str, Enum):
    """
    Standardized Phase 8 10-Class Hallucination Error Taxonomy (H1-H10).
    """
    H1_FABRICATED_PATIENT_FACT = "H1_FABRICATED_PATIENT_FACT"
    H2_FABRICATED_TRIAL_CRITERION = "H2_FABRICATED_TRIAL_CRITERION"
    H3_FABRICATED_NUMERICAL_VALUE = "H3_FABRICATED_NUMERICAL_VALUE"
    H4_FABRICATED_TEMPORAL_FACT = "H4_FABRICATED_TEMPORAL_FACT"
    H5_UNSUPPORTED_CLINICAL_INFERENCE = "H5_UNSUPPORTED_CLINICAL_INFERENCE"
    H6_CONTRADICTION_OF_SOURCE_EVIDENCE = "H6_CONTRADICTION_OF_SOURCE_EVIDENCE"
    H7_PROVENANCE_CITATION_MISMATCH = "H7_PROVENANCE_CITATION_MISMATCH"
    H8_UNSUPPORTED_ELIGIBILITY_CONCLUSION = "H8_UNSUPPORTED_ELIGIBILITY_CONCLUSION"
    H9_EVIDENCE_OMISSION = "H9_EVIDENCE_OMISSION"
    H10_UNSUPPORTED_CERTAINTY = "H10_UNSUPPORTED_CERTAINTY"


# =============================================================================
# 2. Canonical Evidence Representation
# =============================================================================

class GroundingEvidence(BaseModel):
    """
    Verified atomic piece of evidence available to the reasoning system.
    """
    model_config = ConfigDict(extra="forbid")

    evidence_id: str = Field(..., description="Unique evidence ID (e.g., fact-001, crit-001)")
    source_type: EvidenceSourceType = Field(..., description="Source origin category")
    source_id: str = Field(..., description="Parent entity identifier (fact_id, trial_id, note_id)")
    text: str = Field(..., min_length=1, description="Verbatim evidence text snippet")
    document_reference: Optional[str] = Field(default=None, description="Document/Trial reference pointer")
    criterion_reference: Optional[str] = Field(default=None, description="Specific criterion ID pointer")
    start_char: int = Field(default=-1, ge=-1, description="Character offset start, or -1 if unlocatable")
    end_char: int = Field(default=-1, ge=-1, description="Character offset end, or -1 if unlocatable")
    retrieval_method: Optional[str] = Field(default=None, description="Phase 5 retrieval engine method if retrieved")
    retrieval_rank: Optional[int] = Field(default=None, ge=1, description="Retrieval rank if applicable")
    retrieval_score: Optional[float] = Field(default=None, description="Retrieval score if applicable")
    assertion: Optional[str] = Field(default=None, description="Assertion status (PRESENT, ABSENT, UNKNOWN)")


# =============================================================================
# 3. Canonical Claim Representation
# =============================================================================

class GroundingClaim(BaseModel):
    """
    Atomic proposition extracted from generated clinical reasoning text.
    """
    model_config = ConfigDict(extra="forbid")

    claim_id: str = Field(..., description="Unique claim identifier within evaluation")
    claim_text: str = Field(..., min_length=1, description="Verbatim text of the extracted proposition")
    claim_type: ClaimType = Field(..., description="Taxonomic claim category")
    support_status: SupportStatus = Field(default=SupportStatus.UNSUPPORTED, description="Epistemic support state")
    supporting_evidence_ids: List[str] = Field(default_factory=list, description="IDs of entailing GroundingEvidence")
    source_reference: Optional[str] = Field(default=None, description="Document or section citation")
    evidence_span: Optional[Tuple[int, int]] = Field(default=None, description="Character offset span if locatable")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Evaluator certainty score")
    contradiction_status: ContradictionStatus = Field(
        default=ContradictionStatus.NO_CONTRADICTION, description="Contradiction type if present"
    )
    hallucination_category: Optional[HallucinationCategory] = Field(
        default=None, description="Taxonomy classification if claim is unsupported or contradicted"
    )
    rationale: Optional[str] = Field(default=None, description="Detailed justification for the support determination")


# =============================================================================
# 4. Citation & Provenance Validation Representation
# =============================================================================

class CitationValidationRecord(BaseModel):
    """
    Audit record for an individual citation attached to reasoning output.
    """
    model_config = ConfigDict(extra="forbid")

    citation_index: int = Field(..., ge=0, description="Ordinal index of citation in evidence_citations list")
    cited_fact_id: Optional[str] = Field(default=None, description="Claimed fact identifier")
    cited_source_field: str = Field(..., description="Claimed source reference")
    cited_snippet: str = Field(..., description="Claimed snippet text")
    cited_start_char: int = Field(default=-1, description="Claimed character start")
    cited_end_char: int = Field(default=-1, description="Claimed character end")
    is_valid: bool = Field(..., description="Whether citation passes all existence and accuracy checks")
    error_type: Optional[str] = Field(default=None, description="Error classification if invalid")
    error_message: Optional[str] = Field(default=None, description="Descriptive explanation of failure")


# =============================================================================
# 5. Comprehensive Grounding Evaluation Summary
# =============================================================================

class GroundingEvaluation(BaseModel):
    """
    Comprehensive grounding and faithfulness evaluation for a criterion-level reasoning record.
    """
    model_config = ConfigDict(extra="forbid")

    evaluation_id: str = Field(..., description="Unique evaluation identifier")
    trial_id: str = Field(..., description="Target clinical trial ID")
    criterion_id: str = Field(..., description="Target criterion ID")
    raw_reasoning_text: str = Field(..., description="Full text of the reasoning evaluated")
    claims: List[GroundingClaim] = Field(default_factory=list, description="All extracted atomic propositions")
    citations_audited: List[CitationValidationRecord] = Field(default_factory=list, description="Audited citations")
    
    # Counts
    total_claims: int = Field(default=0, ge=0, description="Total extracted claims")
    supported_claim_count: int = Field(default=0, ge=0, description="Count of SUPPORTED claims")
    partially_supported_claim_count: int = Field(default=0, ge=0, description="Count of PARTIALLY_SUPPORTED claims")
    unsupported_claim_count: int = Field(default=0, ge=0, description="Count of UNSUPPORTED claims")
    contradicted_claim_count: int = Field(default=0, ge=0, description="Count of CONTRADICTED claims")
    insufficient_evidence_count: int = Field(default=0, ge=0, description="Count of INSUFFICIENT_EVIDENCE claims")
    
    # Metrics
    claim_support_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="supported / evaluable claims")
    unsupported_claim_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="unsupported / evaluable claims")
    contradiction_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="contradicted / evaluable claims")
    citation_validity_rate: float = Field(default=1.0, ge=0.0, le=1.0, description="valid / total citations")
    evidence_coverage: float = Field(default=0.0, ge=0.0, le=1.0, description="supported claims / claims requiring evidence")
    grounding_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Composite grounding score")
    hallucination_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="hallucinated propositions / total claims")
    
    # Invariant flags
    has_hallucinations: bool = Field(default=False, description="True if any unsupported or contradicted claims exist")
    is_faithful: bool = Field(default=True, description="True if reasoning is strictly supported without contradiction")
    evaluator_version: str = Field(default="1.0.0", description="Evaluator software version")
    evaluated_at_utc: str = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp"
    )

    @model_validator(mode="after")
    def validate_counts_consistency(self) -> GroundingEvaluation:
        """Enforces that total claims equals sum of status buckets."""
        computed_total = (
            self.supported_claim_count
            + self.partially_supported_claim_count
            + self.unsupported_claim_count
            + self.contradicted_claim_count
            + self.insufficient_evidence_count
        )
        if len(self.claims) != self.total_claims:
            raise ValueError(f"total_claims ({self.total_claims}) does not match len(claims) ({len(self.claims)})")
        if self.total_claims != computed_total:
            raise ValueError(
                f"total_claims ({self.total_claims}) does not equal sum of status counts ({computed_total})"
            )
        return self
