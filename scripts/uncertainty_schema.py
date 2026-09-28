"""
MedMatch Canonical Uncertainty Representation Schemas & Contracts.
Phase 9: Formal Uncertainty & Human Review Foundation.

Defines strongly-typed Pydantic models for:
- UncertaintyStatus: RESOLVED, MISSING, CONFLICTING, AMBIGUOUS, STALE, LOW_CONFIDENCE, INSUFFICIENT_EVIDENCE
- UncertaintySeverity: LOW, MEDIUM, HIGH, CRITICAL
- UncertaintyType: Taxonomic categorization of uncertainty origin
- ConflictEvidenceItem: Fine-grained representation of discrepant data points
- UncertaintyRecord: Canonical audit record of an individual clinical uncertainty
- UncertaintyProfile: Aggregated container of uncertainties for a patient-trial evaluation
"""

from __future__ import annotations

import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# =============================================================================
# 1. Canonical Enumerations
# =============================================================================

class UncertaintyStatus(str, Enum):
    """
    Formal epistemic uncertainty status of a clinical fact, criterion assessment,
    or retrieval evidence item. Reconciles Phase 4, Phase 6, and Phase 8 states.
    """
    RESOLVED = "RESOLVED"                          # Deterministically verified by sufficient evidence
    MISSING = "MISSING"                            # Required fact is absent from patient record (NOT_MENTIONED)
    CONFLICTING = "CONFLICTING"                    # Incompatible evidence items across sources or timestamps
    AMBIGUOUS = "AMBIGUOUS"                        # Vague, indeterminate interval, borderline value, or relative timing
    STALE = "STALE"                                # Outdated measurement exceeding temporal validity threshold
    LOW_CONFIDENCE = "LOW_CONFIDENCE"              # Explicit clinician doubt or low retrieval similarity
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE" # Context insufficient to safely reach a definitive conclusion


class UncertaintySeverity(str, Enum):
    """
    Severity rating representing potential clinical risk or decision distortion.
    """
    LOW = "LOW"            # Non-blocking uncertainty on non-essential supporting context
    MEDIUM = "MEDIUM"      # Affects secondary criterion; requires routine chart confirmation
    HIGH = "HIGH"          # Directly blocks conclusive eligibility determination; primary criterion
    CRITICAL = "CRITICAL"  # Active safety contradiction, conflicting contraindication, or major data conflict


class UncertaintyType(str, Enum):
    """
    Specific taxonomic origin of clinical uncertainty.
    """
    MISSING_PATIENT_FACT = "MISSING_PATIENT_FACT"         # e.g., missing biomarker, unrecorded staging
    CONFLICTING_PATIENT_FACTS = "CONFLICTING_PATIENT_FACTS" # e.g., allergy confirmed in note but denied in intake
    CONFLICTING_DOCUMENTS = "CONFLICTING_DOCUMENTS"       # e.g., pathology report vs discharge summary
    TEMPORAL_AMBIGUITY = "TEMPORAL_AMBIGUITY"             # e.g., "recent surgery" vs trial requirement "< 6 months"
    NUMERICAL_AMBIGUITY = "NUMERICAL_AMBIGUITY"           # e.g., "HbA1c ~8%", uncalibrated assay units
    UNSUPPORTED_INFERENCE = "UNSUPPORTED_INFERENCE"       # e.g., machine assumes tolerability without evidence (H5/H8)
    GROUNDING_CONTRADICTION = "GROUNDING_CONTRADICTION"   # e.g., machine asserts PASS despite negative evidence (H6)
    INSUFFICIENT_RETRIEVAL = "INSUFFICIENT_RETRIEVAL"     # e.g., retriever returned zero chunks or score < threshold
    STALE_CLINICAL_DATA = "STALE_CLINICAL_DATA"           # e.g., serum creatinine from 3 years ago for trial requiring 30 days
    CLINICAL_AMBIGUITY = "CLINICAL_AMBIGUITY"             # e.g., qualitative disease activity, quiescent vs active boundary


# =============================================================================
# 2. Conflict Representation
# =============================================================================

class ConflictEvidenceItem(BaseModel):
    """
    Represents an individual evidence point involved in a clinical conflict.
    """
    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(..., min_length=1, description="Document ID, fact ID, or passage ID")
    source_type: str = Field(..., min_length=1, description="e.g., CLINICIAN_NOTE, PATHOLOGY_REPORT, PATIENT_INTAKE")
    asserted_value: str = Field(..., min_length=1, description="Value or status asserted by this source")
    timestamp: Optional[str] = Field(default=None, description="ISO timestamp or date string of this record")
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Source extraction confidence")
    snippet: Optional[str] = Field(default=None, description="Exact textual excerpt demonstrating the value")
    start_char: int = Field(default=-1, ge=-1, description="Character offset start, or -1 if unlocatable")
    end_char: int = Field(default=-1, ge=-1, description="Character offset end, or -1 if unlocatable")


# =============================================================================
# 3. Canonical Uncertainty Record
# =============================================================================

class UncertaintyRecord(BaseModel):
    """
    Canonical audit record representing an explicit uncertainty in the evaluation pipeline.
    Never fabricates facts; ties directly to verifiable entities and criteria.
    """
    model_config = ConfigDict(extra="forbid")

    uncertainty_id: str = Field(..., min_length=1, description="Unique uncertainty identifier, e.g., UNC-001")
    subject: str = Field(..., min_length=1, description="Clinical concept or variable name, e.g., HER2_neu_status")
    fact_or_criterion_ref: str = Field(..., min_length=1, description="Fact ID or Criterion ID experiencing uncertainty")
    status: UncertaintyStatus = Field(..., description="Epistemic status of the uncertainty")
    uncertainty_type: UncertaintyType = Field(..., description="Taxonomic classification of the uncertainty")
    description: str = Field(..., min_length=1, description="Human-readable explanation of why uncertainty exists")
    evidence_references: List[str] = Field(default_factory=list, description="List of fact/passage/doc IDs cited")
    source_provenance: Optional[str] = Field(default=None, description="Provenance descriptor, e.g., doc_id or section")
    temporal_context: Optional[str] = Field(default=None, description="Temporal window or anchor associated with fact")
    affected_criterion: Optional[str] = Field(default=None, description="Criterion ID whose evaluation is impaired")
    severity: UncertaintySeverity = Field(default=UncertaintySeverity.MEDIUM, description="Decision severity rating")
    review_required: bool = Field(default=True, description="Whether human review is strictly required")
    machine_decision_allowed: bool = Field(default=False, description="Whether machine can proceed autonomously")
    reason: str = Field(..., min_length=1, description="Detailed rationale explaining review routing")
    conflict_details: Optional[List[ConflictEvidenceItem]] = Field(
        default=None,
        description="Detailed itemization of conflicting evidence points if status == CONFLICTING"
    )

    @model_validator(mode="after")
    def validate_conflict_details_consistency(self) -> "UncertaintyRecord":
        """
        Ensures that CONFLICTING uncertainties provide conflict items,
        and that machine_decision_allowed is never True if severity is HIGH or CRITICAL.
        """
        if self.status == UncertaintyStatus.CONFLICTING and self.conflict_details:
            if len(self.conflict_details) < 2:
                raise ValueError("CONFLICTING status requires at least 2 conflicting evidence items in conflict_details.")

        if self.severity in (UncertaintySeverity.HIGH, UncertaintySeverity.CRITICAL):
            if self.machine_decision_allowed and self.status != UncertaintyStatus.RESOLVED:
                raise ValueError(
                    f"Unresolved uncertainty with severity {self.severity.value} "
                    f"cannot permit machine_decision_allowed=True."
                )

        if self.status != UncertaintyStatus.RESOLVED and self.review_required is False:
            if self.severity in (UncertaintySeverity.HIGH, UncertaintySeverity.CRITICAL):
                raise ValueError("HIGH or CRITICAL uncertainty must have review_required=True.")

        return self


# =============================================================================
# 4. Uncertainty Profile
# =============================================================================

class UncertaintyProfile(BaseModel):
    """
    Comprehensive collection of uncertainty records associated with an evaluation session.
    """
    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(..., min_length=1, description="Patient case or evaluation ID")
    trial_id: Optional[str] = Field(default=None, description="Trial identifier")
    records: List[UncertaintyRecord] = Field(default_factory=list, description="All registered uncertainty records")
    total_uncertainties: int = Field(default=0, ge=0)
    unresolved_count: int = Field(default=0, ge=0)
    critical_count: int = Field(default=0, ge=0)
    review_required: bool = Field(default=False)
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    @model_validator(mode="after")
    def recompute_summary_counts(self) -> "UncertaintyProfile":
        """
        Automatically aligns counts with records.
        """
        self.total_uncertainties = len(self.records)
        self.unresolved_count = sum(1 for r in self.records if r.status != UncertaintyStatus.RESOLVED)
        self.critical_count = sum(1 for r in self.records if r.severity == UncertaintySeverity.CRITICAL)
        self.review_required = any(r.review_required for r in self.records if r.status != UncertaintyStatus.RESOLVED)
        return self
