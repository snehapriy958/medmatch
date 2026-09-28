"""
MedMatch Canonical Dataset & Ground Truth Schemas.
Phase 2: Dataset + Ground Truth Specification.

Defines Pydantic models for:
- Canonical Trial & Criteria
- Canonical Patient Record
- Criterion-Level Ground Truth
- Trial-Level Ground Truth
- Deterministic Clinical Aggregation
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class CriterionType(str, Enum):
    INCLUSION = "inclusion"
    EXCLUSION = "exclusion"


class CriterionDomain(str, Enum):
    AGE = "age"
    SEX = "sex"
    DIAGNOSIS_STAGE = "diagnosis_stage"
    BIOMARKER_GENOMICS = "biomarker_genomics"
    PRIOR_TREATMENT = "prior_treatment"
    LABORATORY_VALUES = "laboratory_values"
    PERFORMANCE_STATUS = "performance_status"
    COMORBIDITIES = "comorbidities"
    ORGAN_FUNCTION = "organ_function"
    OTHER = "other"


class CriterionVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


class TrialEligibilityVerdict(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    INELIGIBLE = "INELIGIBLE"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class AnnotationSource(str, Enum):
    VERIFIED = "verified"
    DERIVED = "derived"
    SYNTHETIC = "synthetic"


# ==========================================
# 1. Canonical Trial & Criterion Schemas
# ==========================================

class CriterionLocation(BaseModel):
    section: str = Field(default="Eligibility Criteria", description="Protocol section header")
    page: Optional[int] = Field(default=None, description="Page number if extracted from PDF")


class CanonicalCriterion(BaseModel):
    criterion_id: str = Field(..., description="Unique criterion identifier, e.g. 'NCT02484404_INC_001'")
    trial_id: str = Field(..., description="Parent trial NCT identifier")
    criterion_type: CriterionType = Field(..., description="'inclusion' or 'exclusion'")
    domain: CriterionDomain = Field(default=CriterionDomain.OTHER, description="Clinical domain classification")
    source_text: str = Field(..., min_length=3, description="Verbatim protocol criteria string")
    normalized_form: Optional[Dict[str, Any]] = Field(default=None, description="Structured parsed rule representation")
    source_location: CriterionLocation = Field(default_factory=CriterionLocation)


class CanonicalTrial(BaseModel):
    trial_id: str = Field(..., description="Standardized trial identifier, e.g. 'NCT02484404'")
    source: str = Field(default="clinicaltrials.gov", description="Originating registry or corpus")
    source_id: str = Field(..., description="Original accession ID in source registry")
    title: str = Field(..., min_length=5, description="Official brief protocol title")
    condition: List[str] = Field(default_factory=list, description="Target diseases/indications")
    intervention: List[str] = Field(default_factory=list, description="Investigational drugs/therapies")
    phase: Optional[str] = Field(default=None, description="Clinical trial phase (e.g. Phase 2)")
    eligibility_text: str = Field(..., min_length=10, description="Full raw eligibility criteria narrative")
    criteria: List[CanonicalCriterion] = Field(default_factory=list, description="Parsed atomic criteria")

    @model_validator(mode="after")
    def validate_criteria_parent_ids(self) -> CanonicalTrial:
        for crit in self.criteria:
            if crit.trial_id != self.trial_id:
                raise ValueError(f"Criterion {crit.criterion_id} has mismatched trial_id '{crit.trial_id}' != '{self.trial_id}'")
        return self


# ==========================================
# 2. Canonical Patient Schema
# ==========================================

class LabValue(BaseModel):
    test_name: str
    value: float
    unit: str
    reference_range: Optional[str] = None
    date_offset_days: Optional[int] = None  # Days relative to screening date


class CanonicalPatient(BaseModel):
    patient_id: str = Field(..., description="Unique patient identifier, e.g. 'P001'")
    source: str = Field(..., description="'synthetic', 'trialgpt', 'trec_ct'")
    age: Optional[int] = Field(default=None, ge=0, le=125, description="Patient age in years")
    sex: Optional[str] = Field(default=None, description="'male', 'female', 'other'")
    diagnoses: List[str] = Field(default_factory=list, description="Primary and secondary histological diagnoses")
    stage: Optional[str] = Field(default=None, description="Cancer stage (e.g. 'Stage IV', 'T3N1M0')")
    biomarkers: Dict[str, str] = Field(default_factory=dict, description="Genomic alterations (e.g. {'EGFR': 'Exon 19 del'})")
    medications: List[str] = Field(default_factory=list, description="Current or recent medications")
    comorbidities: List[str] = Field(default_factory=list, description="Documented past medical history")
    laboratory_values: List[LabValue] = Field(default_factory=list, description="Quantitative lab measurements")
    prior_treatments: List[str] = Field(default_factory=list, description="Prior systemic therapies, surgery, radiation")
    ecog_performance_status: Optional[int] = Field(default=None, ge=0, le=5)
    clinical_note: str = Field(..., min_length=20, description="Full narrative progress note/discharge summary")


# ==========================================
# 3. Ground Truth Schemas
# ==========================================

class PatientEvidence(BaseModel):
    text: str = Field(..., description="Verbatim patient text supporting verdict (empty string if UNKNOWN)")
    start_char: Optional[int] = Field(default=None, ge=-1, description="0-based start character offset in clinical_note")
    end_char: Optional[int] = Field(default=None, ge=-1, description="0-based end character offset in clinical_note")
    source_section: Optional[str] = Field(default=None, description="Section header where evidence was located")


class CriterionEvidence(BaseModel):
    text: str = Field(..., description="Verbatim criterion rule string")


class CriterionGroundTruth(BaseModel):
    patient_id: str = Field(..., description="Patient identifier")
    trial_id: str = Field(..., description="Trial identifier")
    criterion_id: str = Field(..., description="Criterion identifier")
    criterion_type: CriterionType = Field(..., description="'inclusion' or 'exclusion'")
    ground_truth: CriterionVerdict = Field(..., description="PASS, FAIL, or UNKNOWN")
    patient_evidence: PatientEvidence = Field(..., description="Patient text span evidence")
    criterion_evidence: CriterionEvidence = Field(..., description="Protocol text span evidence")
    annotation_source: AnnotationSource = Field(..., description="'verified', 'derived', or 'synthetic'")
    annotator_id: Optional[str] = Field(default=None, description="Reviewer or generator ID")
    annotation_notes: str = Field(default="", description="Auditing rationale or generation scenario description")

    @model_validator(mode="after")
    def validate_evidence_consistency(self) -> CriterionGroundTruth:
        if self.ground_truth in (CriterionVerdict.PASS, CriterionVerdict.FAIL):
            if not self.patient_evidence.text or len(self.patient_evidence.text.strip()) == 0:
                raise ValueError(
                    f"Criterion {self.criterion_id} has verdict {self.ground_truth} but empty patient_evidence.text"
                )
        return self


class CriterionSummary(BaseModel):
    total: int = Field(..., ge=0)
    pass_count: int = Field(..., ge=0, alias="pass")
    fail_count: int = Field(..., ge=0, alias="fail")
    unknown_count: int = Field(..., ge=0, alias="unknown")

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def validate_sum(self) -> CriterionSummary:
        if self.total != (self.pass_count + self.fail_count + self.unknown_count):
            raise ValueError(
                f"CriterionSummary total ({self.total}) != sum of pass ({self.pass_count}) + "
                f"fail ({self.fail_count}) + unknown ({self.unknown_count})"
            )
        return self


class TrialGroundTruth(BaseModel):
    patient_id: str = Field(..., description="Patient identifier")
    trial_id: str = Field(..., description="Trial identifier")
    eligibility: TrialEligibilityVerdict = Field(..., description="ELIGIBLE, INELIGIBLE, or NEEDS_REVIEW")
    criterion_summary: CriterionSummary = Field(..., description="Summary counts of criterion evaluations")
    evidence: List[str] = Field(default_factory=list, description="Primary clinical evidence snippets")
    annotation_source: AnnotationSource = Field(..., description="'verified', 'derived', or 'synthetic'")
    annotator_id: Optional[str] = Field(default=None)
    annotation_notes: str = Field(default="")


# ==========================================
# 4. Deterministic Clinical Aggregation
# ==========================================

def compute_trial_eligibility(
    criterion_verdicts: List[CriterionVerdict],
) -> TrialEligibilityVerdict:
    """
    Computes deterministic trial-level eligibility from a list of criterion verdicts.
    
    Clinical Logic:
    - If ANY criterion evaluates to FAIL -> INELIGIBLE (a single violation disqualifies).
    - If NO criterion evaluates to FAIL, but AT LEAST ONE criterion is UNKNOWN -> NEEDS_REVIEW.
    - If EVERY criterion evaluates to PASS -> ELIGIBLE.
    """
    if not criterion_verdicts:
        return TrialEligibilityVerdict.NEEDS_REVIEW

    has_fail = any(v == CriterionVerdict.FAIL for v in criterion_verdicts)
    if has_fail:
        return TrialEligibilityVerdict.INELIGIBLE

    has_unknown = any(v == CriterionVerdict.UNKNOWN for v in criterion_verdicts)
    if has_unknown:
        return TrialEligibilityVerdict.NEEDS_REVIEW

    all_pass = all(v == CriterionVerdict.PASS for v in criterion_verdicts)
    if all_pass:
        return TrialEligibilityVerdict.ELIGIBLE

    return TrialEligibilityVerdict.NEEDS_REVIEW


def summarize_criterion_verdicts(
    criterion_verdicts: List[CriterionVerdict],
) -> CriterionSummary:
    """Computes total, pass, fail, unknown summary."""
    p_cnt = sum(1 for v in criterion_verdicts if v == CriterionVerdict.PASS)
    f_cnt = sum(1 for v in criterion_verdicts if v == CriterionVerdict.FAIL)
    u_cnt = sum(1 for v in criterion_verdicts if v == CriterionVerdict.UNKNOWN)
    return CriterionSummary(
        total=len(criterion_verdicts),
        **{"pass": p_cnt, "fail": f_cnt, "unknown": u_cnt}
    )
