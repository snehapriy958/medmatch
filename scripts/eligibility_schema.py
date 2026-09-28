"""
MedMatch Canonical Eligibility Reasoning Schemas & Contracts.
Phase 6: Eligibility Reasoning.

Defines strongly-typed Pydantic models for:
- CriterionEvaluationStatus (PASS, FAIL, UNKNOWN)
- TrialEligibilityStatus (ELIGIBLE, INELIGIBLE, NEEDS_REVIEW)
- CriterionEvaluationRecord (atomic criterion-level assessment)
- TrialEligibilityEvaluation (deterministic trial-level aggregated assessment)
- EligibilityReasoningRequest (input context: patient facts + trial criteria)
- EligibilityReasoningResponse (canonical output response)
"""

from __future__ import annotations

import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class CriterionType(str, Enum):
    """Clinical trial eligibility criterion type."""
    INCLUSION = "INCLUSION"
    EXCLUSION = "EXCLUSION"


class CriterionEvaluationStatus(str, Enum):
    """
    Strict 3-valued truth state for criterion-level evaluation.
    UNKNOWN must never be silently converted into PASS or FAIL.
    """
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


class TrialEligibilityStatus(str, Enum):
    """
    Deterministic trial-level aggregated status.
    - ELIGIBLE: Every required criterion PASSes.
    - INELIGIBLE: At least one criterion FAILs.
    - NEEDS_REVIEW: No criterion fails, but at least one criterion is UNKNOWN.
    """
    ELIGIBLE = "ELIGIBLE"
    INELIGIBLE = "INELIGIBLE"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class EvidenceCitation(BaseModel):
    """
    Grounding evidence citation referencing patient data and source offsets.
    """
    model_config = ConfigDict(extra="forbid")

    fact_id: Optional[str] = Field(default=None, description="PatientClinicalProfile fact ID")
    text_snippet: str = Field(..., min_length=1, description="Exact cited text from patient record or criteria")
    source_field: str = Field(default="patient_note", description="Source document or section reference")
    start_char: int = Field(default=-1, ge=-1, description="Character offset start, or -1 if unlocatable")
    end_char: int = Field(default=-1, ge=-1, description="Character offset end, or -1 if unlocatable")
    assertion_type: Optional[str] = Field(default=None, description="Assertion status (e.g. PRESENT, ABSENT)")


class CriterionEvaluationRecord(BaseModel):
    """
    Atomic criterion-level evaluation.
    Grounds reasoning in patient facts and explicit evidence citations.
    """
    model_config = ConfigDict(extra="forbid")

    criterion_id: str = Field(..., min_length=1, description="Unique trial criterion identifier")
    trial_id: str = Field(..., min_length=1, description="Associated clinical trial ID")
    criterion_type: CriterionType = Field(..., description="INCLUSION or EXCLUSION")
    criterion_text: str = Field(..., min_length=1, description="Canonical criterion text")
    status: CriterionEvaluationStatus = Field(..., description="Strict 3-valued status: PASS, FAIL, UNKNOWN")
    reasoning: str = Field(..., min_length=1, description="Clinical justification for the evaluation")
    evidence_citations: List[EvidenceCitation] = Field(default_factory=list, description="Grounding citations")
    patient_fact_references: List[str] = Field(default_factory=list, description="Referenced ClinicalFact IDs")
    trial_criterion_reference: Optional[str] = Field(default=None, description="Document/section pointer")
    is_negated: bool = Field(default=False, description="Whether criterion logic involves negation")
    temporal_constraint: Optional[str] = Field(default=None, description="Evaluated temporal window if applicable")
    numerical_threshold: Optional[str] = Field(default=None, description="Evaluated numerical condition if applicable")
    uncertainty_notes: Optional[str] = Field(default=None, description="Details if status is UNKNOWN")
    evaluator: str = Field(default="rule_based_reasoner", description="Model or reasoner identifier")
    schema_version: str = Field(default="1.0.0", description="Contract schema version")

    @field_validator("status")
    @classmethod
    def validate_status_values(cls, v: CriterionEvaluationStatus) -> CriterionEvaluationStatus:
        if v not in {CriterionEvaluationStatus.PASS, CriterionEvaluationStatus.FAIL, CriterionEvaluationStatus.UNKNOWN}:
            raise ValueError(f"Invalid status: {v}. Must be PASS, FAIL, or UNKNOWN.")
        return v

    @model_validator(mode="after")
    def validate_evidence_policy(self) -> CriterionEvaluationRecord:
        """
        Enforce Evidence Policy:
        PASS and FAIL evaluations must have at least one supporting evidence citation or fact reference.
        """
        if self.status in {CriterionEvaluationStatus.PASS, CriterionEvaluationStatus.FAIL}:
            if not self.evidence_citations and not self.patient_fact_references:
                raise ValueError(
                    f"Criterion {self.criterion_id} evaluated as {self.status} without supporting evidence. "
                    "Evidence citations or patient fact references are mandatory for PASS and FAIL."
                )
        return self


class TrialEligibilityEvaluation(BaseModel):
    """
    Deterministic aggregated trial-level eligibility evaluation.
    Computed via pure programmatic logic from atomic CriterionEvaluationRecords.
    """
    model_config = ConfigDict(extra="forbid")

    trial_id: str = Field(..., min_length=1, description="Clinical trial accession or ID")
    trial_title: Optional[str] = Field(default=None, description="Official title of the trial")
    status: TrialEligibilityStatus = Field(..., description="Deterministic status: ELIGIBLE, INELIGIBLE, NEEDS_REVIEW")
    criterion_evaluations: List[CriterionEvaluationRecord] = Field(default_factory=list)
    total_criteria_evaluated: int = Field(default=0, ge=0)
    passed_count: int = Field(default=0, ge=0)
    failed_count: int = Field(default=0, ge=0)
    unknown_count: int = Field(default=0, ge=0)
    failed_criterion_ids: List[str] = Field(default_factory=list)
    unknown_criterion_ids: List[str] = Field(default_factory=list)
    passed_criterion_ids: List[str] = Field(default_factory=list)
    clinical_summary: str = Field(default="", description="Aggregated clinical explanation")
    evaluator: str = Field(default="deterministic_aggregator", description="Aggregator component name")
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())


class EligibilityReasoningRequest(BaseModel):
    """
    Input request for eligibility evaluation.
    """
    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(..., min_length=1)
    patient_id: str = Field(..., min_length=1)
    tenant_id: Optional[str] = Field(default=None, description="Hospital or tenant identifier")
    patient_note: Optional[str] = Field(default=None, description="Raw narrative text")
    patient_facts: List[Dict[str, Any]] = Field(default_factory=list, description="Extracted ClinicalFacts")
    demographics: Optional[Dict[str, Any]] = Field(default=None, description="Age, sex, etc.")
    candidate_trials: List[Dict[str, Any]] = Field(default_factory=list, description="Candidate trials with criteria")
    reasoning_mode: str = Field(default="rule_based", description="Reasoning engine mode")


class EligibilityReasoningResponse(BaseModel):
    """
    Response envelope containing trial-level aggregated evaluations.
    """
    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(...)
    patient_id: str = Field(...)
    evaluations: List[TrialEligibilityEvaluation] = Field(default_factory=list)
    total_trials_evaluated: int = Field(default=0, ge=0)
    eligible_trials: List[str] = Field(default_factory=list)
    ineligible_trials: List[str] = Field(default_factory=list)
    needs_review_trials: List[str] = Field(default_factory=list)
    execution_time_ms: float = Field(default=0.0, ge=0.0)
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
