"""
MedMatch Canonical Patient Clinical Profile & Clinical Fact Schemas.
Phase 4: Patient Clinical Information Extraction.

Defines Pydantic models for:
- Canonical PatientClinicalProfile representation
- ClinicalFact model (concept, value, unit, assertion, temporality, uncertainty)
- FactProvenance and character offset tracking
- Formal TemporalContext representation (relative intervals, anchors, durations)
- UncertaintyStatus and EvidenceSource taxonomies
- Extraction contracts and modular interfaces
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator


# ==========================================
# 1. Enumerations & Taxonomies
# ==========================================

class AssertionType(str, Enum):
    """Clinical assertion / polarity state."""
    AFFIRMED = "affirmed"          # Clinically confirmed / present
    NEGATED = "negated"            # Explicitly absent, denied, or ruled out
    POSSIBLE = "possible"          # Suspected, differential diagnosis, unconfirmed
    HISTORICAL = "historical"      # Prior condition, resolved or past episode
    UNKNOWN = "unknown"            # Indeterminate, unmentioned, or ambiguous


class TemporalityType(str, Enum):
    """Temporal classification of clinical information."""
    CURRENT = "current"                      # Active, baseline, or present
    HISTORICAL = "historical"                # Prior episode, completed regimen
    DATE_SPECIFIC = "date_specific"          # Exact absolute calendar date known
    DURATION = "duration"                    # Ongoing for specified length of time
    BEFORE_EVENT = "before_event"            # Occurred prior to an anchor event
    AFTER_EVENT = "after_event"              # Occurred subsequent to an anchor event
    RELATIVE_INTERVAL = "relative_interval"  # Relative time offset (e.g., "27 days ago")
    UNKNOWN = "unknown"                      # Timing cannot be determined


class UncertaintyStatus(str, Enum):
    """Epistemic uncertainty and information completeness status."""
    KNOWN = "known"                          # Definitive clinical fact
    UNKNOWN = "unknown"                      # Explicitly acknowledged as unknown / pending
    NOT_MENTIONED = "not_mentioned"          # Not referenced anywhere in patient record
    UNCERTAIN = "uncertain"                  # Probable, ambiguous, or clinician doubt expressed
    CONFLICTING = "conflicting"              # Discrepant evidence across reports/dates
    PATIENT_REPORTED = "patient_reported"    # Self-reported by patient (subject to recall bias)
    CLINICIAN_DOCUMENTED = "clinician_documented"  # Documented by medical professional


class EvidenceSource(str, Enum):
    """Source domain of clinical evidence."""
    CLINICIAN_NOTE = "clinician_note"
    PATHOLOGY_REPORT = "pathology_report"
    LABORATORY_REPORT = "laboratory_report"
    IMAGING_REPORT = "imaging_report"
    SURGICAL_REPORT = "surgical_report"
    PATIENT_PORTAL = "patient_portal"
    MEDICATION_RECONCILIATION = "medication_reconciliation"
    UNKNOWN = "unknown"


# ==========================================
# 2. Provenance Models
# ==========================================

class FactProvenance(BaseModel):
    """
    Source evidence attribution for an extracted clinical fact.
    Never fabricates character offsets; uses -1 if offset is unavailable.
    """
    note_id: str = Field(..., description="Unique identifier of source note or document")
    patient_id: str = Field(..., description="Parent patient identifier")
    source_text: str = Field(..., min_length=1, description="Verbatim text span supporting the fact")
    start_char: Optional[int] = Field(
        default=None, ge=-1, description="0-based start character offset in source text (-1 if unavailable)"
    )
    end_char: Optional[int] = Field(
        default=None, ge=-1, description="0-based end character offset in source text (-1 if unavailable)"
    )
    source_section: Optional[str] = Field(
        default=None, description="Section heading in source note, e.g., 'Past Medical History'"
    )
    extraction_version: str = Field(default="0.4.0", description="Extraction engine software version")
    extraction_timestamp: str = Field(..., description="ISO-8601 UTC timestamp of extraction")
    model_identifier: Optional[str] = Field(
        default=None, description="Model ID or rule engine version that performed extraction"
    )

    @model_validator(mode="after")
    def validate_offsets(self) -> FactProvenance:
        if self.start_char is not None and self.end_char is not None:
            if self.start_char == -1 or self.end_char == -1:
                pass  # Explicit indicator that offsets were not recoverable
            elif self.start_char < 0 or self.end_char < 0:
                raise ValueError(f"Offsets cannot be negative unless -1 (unknown). Got start={self.start_char}, end={self.end_char}")
            elif self.start_char > self.end_char:
                raise ValueError(f"start_char ({self.start_char}) cannot exceed end_char ({self.end_char})")
        return self


# ==========================================
# 3. Temporal Context Model
# ==========================================

class TemporalContext(BaseModel):
    """
    Temporal representation preserving event anchors, durations, and relative statements.
    Does not convert relative dates to absolute dates unless the reference anchor is verified.
    """
    temporality_type: TemporalityType = Field(default=TemporalityType.UNKNOWN)
    reference_date: Optional[str] = Field(
        default=None, description="ISO-8601 calendar date if explicitly known (YYYY-MM-DD)"
    )
    relative_interval: Optional[str] = Field(
        default=None, description="Verbatim relative interval, e.g., '27 days ago', '3 weeks prior'"
    )
    duration_days: Optional[int] = Field(
        default=None, ge=0, description="Duration in days if applicable"
    )
    relative_days_offset: Optional[int] = Field(
        default=None, description="Signed offset in days relative to anchor event (e.g. -27 for 27 days prior)"
    )
    anchor_event: Optional[str] = Field(
        default=None, description="Anchor event name, e.g. 'chemotherapy_completion', 'screening'"
    )
    is_approximate: bool = Field(default=False, description="True if temporal statement is approximate")


# ==========================================
# 4. Clinical Fact Model
# ==========================================

class ClinicalFact(BaseModel):
    """
    Atomic clinical fact extracted from patient records.
    """
    fact_id: str = Field(..., description="Unique fact identifier, e.g. 'FACT_001'")
    patient_id: str = Field(..., description="Parent patient identifier")
    concept: str = Field(..., min_length=2, description="Normalized clinical variable or entity identifier")
    value: Union[float, int, str, bool, List[Union[float, int, str]], None] = Field(
        default=None, description="Recorded value, laboratory measurement, or status"
    )
    normalized_value: Optional[Union[float, int, str, bool]] = Field(
        default=None, description="Standardized / unit-normalized value"
    )
    unit: Optional[str] = Field(default=None, description="Standard clinical measurement unit")
    assertion: AssertionType = Field(
        default=AssertionType.AFFIRMED, description="Assertion / polarity status"
    )
    temporality: TemporalContext = Field(
        default_factory=TemporalContext, description="Temporal anchor and context"
    )
    uncertainty: UncertaintyStatus = Field(
        default=UncertaintyStatus.KNOWN, description="Information uncertainty / completeness"
    )
    evidence_source: EvidenceSource = Field(
        default=EvidenceSource.CLINICIAN_NOTE, description="Originating document type"
    )
    source_text: str = Field(..., min_length=1, description="Verbatim text span supporting the fact")
    provenance: FactProvenance = Field(..., description="Traceable provenance back to source note")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Extraction confidence score")

    @model_validator(mode="after")
    def validate_ids_match_provenance(self) -> ClinicalFact:
        if self.provenance.patient_id != self.patient_id:
            raise ValueError(
                f"Provenance patient_id '{self.provenance.patient_id}' != fact patient_id '{self.patient_id}'"
            )
        return self


# ==========================================
# 5. Patient Demographics & Profile
# ==========================================

class PatientDemographics(BaseModel):
    """Basic demographic profile attributes."""
    age: Optional[int] = Field(default=None, ge=0, le=130)
    gender: Optional[str] = Field(default=None)
    race: Optional[str] = Field(default=None)
    ethnicity: Optional[str] = Field(default=None)
    birth_date: Optional[str] = Field(default=None)


class PatientClinicalProfile(BaseModel):
    """
    Canonical structured clinical representation of a patient.
    Missing fields remain None / empty rather than assuming negative facts.
    """
    patient_id: str = Field(..., description="Unique patient identifier")
    profile_version: str = Field(default="0.4.0", description="Profile schema version")
    source_reference: Optional[str] = Field(
        default=None, description="Identifier of the primary clinical document or bundle"
    )
    demographics: Optional[PatientDemographics] = Field(default=None)
    
    # Clinical categories
    diagnoses: List[ClinicalFact] = Field(default_factory=list)
    symptoms: List[ClinicalFact] = Field(default_factory=list)
    medications: List[ClinicalFact] = Field(default_factory=list)
    allergies: List[ClinicalFact] = Field(default_factory=list)
    laboratory_results: List[ClinicalFact] = Field(default_factory=list)
    vital_signs: List[ClinicalFact] = Field(default_factory=list)
    procedures: List[ClinicalFact] = Field(default_factory=list)
    surgeries: List[ClinicalFact] = Field(default_factory=list)
    imaging_findings: List[ClinicalFact] = Field(default_factory=list)
    biomarkers: List[ClinicalFact] = Field(default_factory=list)
    disease_stage: Optional[ClinicalFact] = Field(default=None)
    performance_status: Optional[ClinicalFact] = Field(default=None)
    comorbidities: List[ClinicalFact] = Field(default_factory=list)
    treatment_history: List[ClinicalFact] = Field(default_factory=list)
    treatment_response: List[ClinicalFact] = Field(default_factory=list)
    clinical_events: List[ClinicalFact] = Field(default_factory=list)
    
    # Uncertainty & metadata tracking
    uncertainty_records: List[ClinicalFact] = Field(
        default_factory=list, description="Clinical facts explicitly flagged with uncertainty or conflict"
    )
    missing_information: List[str] = Field(
        default_factory=list, description="Explicit list of unmentioned concepts critical for oncology trials"
    )

    def all_facts(self) -> List[ClinicalFact]:
        """Aggregate all extracted clinical facts across categories."""
        facts: List[ClinicalFact] = []
        facts.extend(self.diagnoses)
        facts.extend(self.symptoms)
        facts.extend(self.medications)
        facts.extend(self.allergies)
        facts.extend(self.laboratory_results)
        facts.extend(self.vital_signs)
        facts.extend(self.procedures)
        facts.extend(self.surgeries)
        facts.extend(self.imaging_findings)
        facts.extend(self.biomarkers)
        if self.disease_stage is not None:
            facts.append(self.disease_stage)
        if self.performance_status is not None:
            facts.append(self.performance_status)
        facts.extend(self.comorbidities)
        facts.extend(self.treatment_history)
        facts.extend(self.treatment_response)
        facts.extend(self.clinical_events)
        facts.extend(self.uncertainty_records)
        return facts


# ==========================================
# 6. Extraction Contract Envelope
# ==========================================

class PatientExtractionContract(BaseModel):
    """
    Stable output contract between patient extraction engines and downstream services.
    """
    status: str = Field(default="SUCCESS", description="'SUCCESS', 'PARTIAL_SUCCESS', 'FAILED'")
    profile: PatientClinicalProfile
    total_facts: int = Field(..., ge=0)
    affirmed_count: int = Field(..., ge=0)
    negated_count: int = Field(..., ge=0)
    uncertain_count: int = Field(..., ge=0)
    historical_count: int = Field(..., ge=0)
    conflicting_count: int = Field(..., ge=0)
    missing_concepts_count: int = Field(..., ge=0)
    validation_passed: bool = Field(default=True)
    validation_messages: List[str] = Field(default_factory=list)
