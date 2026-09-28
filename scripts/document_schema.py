"""
MedMatch Canonical Clinical Trial Document Intelligence Schemas.
Phase 3: Clinical Trial Document Intelligence.

Defines Pydantic models for:
- Canonical TrialDocument and TrialSection hierarchy
- CriterionProvenance tracking (page, offsets, section, document)
- Atomic Criterion model (concept, operator, value, unit, temporal window)
- Structured section taxonomy and normalization
- Output contracts for extraction and validation
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator


# ==========================================
# 1. Enumerations & Taxonomies
# ==========================================

class SectionType(str, Enum):
    INCLUSION_CRITERIA = "INCLUSION_CRITERIA"
    EXCLUSION_CRITERIA = "EXCLUSION_CRITERIA"
    ELIGIBILITY_CRITERIA = "ELIGIBILITY_CRITERIA"  # Combined / General
    STUDY_POPULATION = "STUDY_POPULATION"
    DISEASE_CHARACTERISTICS = "DISEASE_CHARACTERISTICS"
    PRIOR_CONCURRENT_THERAPY = "PRIOR_CONCURRENT_THERAPY"
    PATIENT_CHARACTERISTICS = "PATIENT_CHARACTERISTICS"
    UNKNOWN_AMBIGUOUS = "UNKNOWN_AMBIGUOUS"


class CriterionType(str, Enum):
    INCLUSION = "inclusion"
    EXCLUSION = "exclusion"
    AMBIGUOUS = "ambiguous"


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
    CONCOMITANT_MEDS = "concomitant_medications"
    ETHICAL_CONSENT = "ethical_consent"
    OTHER = "other"


class CriterionOperator(str, Enum):
    GTE = ">="
    LTE = "<="
    GT = ">"
    LT = "<"
    EQ = "=="
    NEQ = "!="
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"
    BETWEEN = "between"


class LogicalRelation(str, Enum):
    AND = "AND"
    OR = "OR"
    DEPENDENT_CLAUSE = "DEPENDENT_CLAUSE"
    EXCEPTION = "EXCEPTION"


# ==========================================
# 2. Provenance Models
# ==========================================

class CriterionProvenance(BaseModel):
    document_id: str = Field(..., description="Unique document ID")
    trial_id: str = Field(..., description="Parent clinical trial NCT identifier")
    section_id: str = Field(..., description="Parent section ID")
    page_number: Optional[int] = Field(default=None, ge=1, description="1-based PDF page number if known")
    start_char: Optional[int] = Field(default=None, ge=-1, description="0-based start character offset in section/doc text")
    end_char: Optional[int] = Field(default=None, ge=-1, description="0-based end character offset in section/doc text")
    source_text: str = Field(..., min_length=1, description="Verbatim text span supporting extraction")
    extraction_version: str = Field(default="0.3.0", description="Extraction pipeline software version")


# ==========================================
# 3. Atomic Criterion & Constraints
# ==========================================

class AtomicConstraint(BaseModel):
    """
    Structured atomic clinical condition.
    E.g. concept="platelet_count", operator=">=", value=100.0, unit="x 10^9/L"
    """
    concept: str = Field(..., min_length=2, description="Normalized clinical variable or entity")
    operator: CriterionOperator = Field(..., description="Comparison or membership operator")
    value: Union[float, int, str, bool, List[Union[float, int, str]]] = Field(
        ..., description="Constraint threshold, target category, or range"
    )
    unit: Optional[str] = Field(default=None, description="Standardized clinical unit")
    temporal_window_days: Optional[int] = Field(
        default=None, ge=0, description="Time duration or washout window in days"
    )
    temporal_anchor: Optional[str] = Field(
        default=None, description="Anchor event, e.g. 'prior_to_day_1', 'prior_to_screening'"
    )
    is_negated: bool = Field(default=False, description="True if condition is clinically negated")


class TrialCriterion(BaseModel):
    """
    Extracted eligibility criterion with atomicity and provenance tracking.
    """
    criterion_id: str = Field(..., description="Unique criterion ID, e.g. 'NCT02484404_INC_001'")
    trial_id: str = Field(..., description="Parent trial NCT ID")
    section_id: str = Field(..., description="Parent section ID")
    criterion_type: CriterionType = Field(..., description="'inclusion', 'exclusion', or 'ambiguous'")
    domain: CriterionDomain = Field(default=CriterionDomain.OTHER, description="Clinical semantic domain")
    raw_text: str = Field(..., min_length=3, description="Verbatim unedited criteria text from source")
    normalized_text: str = Field(..., min_length=3, description="Cleaned, standardized text")
    is_atomic: bool = Field(default=True, description="True if criterion represents a single indivisible condition")
    can_decompose: bool = Field(
        default=True, description="False if decomposition is unsafe due to complex clinical dependencies"
    )
    decomposition_block_reason: Optional[str] = Field(
        default=None, description="Clinical rationale if decomposition was intentionally blocked"
    )
    compound_relation: Optional[LogicalRelation] = Field(
        default=None, description="Logical operator if this represents a compound multi-intent criterion"
    )
    atomic_constraints: List[AtomicConstraint] = Field(
        default_factory=list, description="Structured parsed atomic constraints"
    )
    provenance: CriterionProvenance = Field(..., description="Exact textual provenance")
    extraction_confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Model extraction confidence")

    @model_validator(mode="after")
    def validate_ids_match_provenance(self) -> TrialCriterion:
        if self.provenance.trial_id != self.trial_id:
            raise ValueError(
                f"Provenance trial_id '{self.provenance.trial_id}' != criterion trial_id '{self.trial_id}'"
            )
        if self.provenance.section_id != self.section_id:
            raise ValueError(
                f"Provenance section_id '{self.provenance.section_id}' != criterion section_id '{self.section_id}'"
            )
        return self


# ==========================================
# 4. Trial Section & Document Hierarchy
# ==========================================

class TrialSection(BaseModel):
    """
    A structural section extracted from a clinical trial document.
    """
    section_id: str = Field(..., description="Unique section ID, e.g. 'SEC_001'")
    section_type: SectionType = Field(..., description="Taxonomically normalized section type")
    heading: str = Field(..., min_length=1, description="Original raw section heading text")
    text: str = Field(..., description="Complete text body of the section")
    page_start: Optional[int] = Field(default=None, ge=1, description="1-based start page in source PDF")
    page_end: Optional[int] = Field(default=None, ge=1, description="1-based end page in source PDF")
    source_order: int = Field(..., ge=1, description="1-based sequential order in document")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Section classification confidence")
    criteria: List[TrialCriterion] = Field(default_factory=list, description="Extracted criteria in this section")

    @model_validator(mode="after")
    def validate_page_range(self) -> TrialSection:
        if self.page_start is not None and self.page_end is not None:
            if self.page_start > self.page_end:
                raise ValueError(f"page_start ({self.page_start}) cannot exceed page_end ({self.page_end})")
        return self


class TrialDocument(BaseModel):
    """
    Canonical representation of a processed clinical trial document.
    """
    document_id: str = Field(..., description="Unique document ID, e.g. 'DOC_NCT02484404_001'")
    trial_id: str = Field(..., description="Primary clinical trial accession (NCT ID)")
    source_uri: str = Field(..., description="File path, URL, or registry URI of source document")
    document_type: str = Field(default="protocol_pdf", description="'protocol_pdf', 'registry_json', 'summary_text'")
    extraction_version: str = Field(default="0.3.0", description="Extraction engine software version")
    processing_timestamp: str = Field(..., description="ISO-8601 UTC processing timestamp")
    document_hash: str = Field(..., description="Cryptographic SHA-256 hash of original source document")
    sections: List[TrialSection] = Field(default_factory=list, description="Extracted sections")

    @model_validator(mode="after")
    def validate_document_hierarchy(self) -> TrialDocument:
        for sec in self.sections:
            for crit in sec.criteria:
                if crit.trial_id != self.trial_id:
                    raise ValueError(
                        f"Criterion '{crit.criterion_id}' trial_id '{crit.trial_id}' != document trial_id '{self.trial_id}'"
                    )
                if crit.section_id != sec.section_id:
                    raise ValueError(
                        f"Criterion '{crit.criterion_id}' section_id '{crit.section_id}' != parent section_id '{sec.section_id}'"
                    )
                if crit.provenance.document_id != self.document_id:
                    raise ValueError(
                        f"Criterion '{crit.criterion_id}' provenance document_id '{crit.provenance.document_id}' != '{self.document_id}'"
                    )
        return self


# ==========================================
# 5. Extraction Output Contract
# ==========================================

class DocumentExtractionContract(BaseModel):
    """
    Stable output contract between document intelligence extraction and downstream services.
    """
    status: str = Field(default="SUCCESS", description="'SUCCESS', 'PARTIAL_SUCCESS', 'FAILED'")
    document: TrialDocument
    total_sections: int = Field(..., ge=0)
    total_criteria: int = Field(..., ge=0)
    inclusion_count: int = Field(..., ge=0)
    exclusion_count: int = Field(..., ge=0)
    ambiguous_count: int = Field(..., ge=0)
    atomic_count: int = Field(..., ge=0)
    compound_count: int = Field(..., ge=0)
    validation_passed: bool = Field(default=True)
    validation_messages: List[str] = Field(default_factory=list)
