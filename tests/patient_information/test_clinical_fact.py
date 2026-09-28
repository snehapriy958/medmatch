"""
Tests for ClinicalFact Representation, Assertion, and Negation.
Phase 4: Patient Clinical Information Extraction.
"""

import pytest
from pydantic import ValidationError

from scripts.patient_schema import (
    AssertionType,
    ClinicalFact,
    EvidenceSource,
    FactProvenance,
    PatientClinicalProfile,
    TemporalContext,
    TemporalityType,
    UncertaintyStatus,
)
from scripts.validate_patient_profile import PatientProfileValidator


def _make_fact_with_assertion(
    assertion: AssertionType,
    concept: str = "brain_metastases",
    value: object = False,
    confidence: float = 1.0,
) -> ClinicalFact:
    prov = FactProvenance(
        note_id="NOTE_001",
        patient_id="PAT_001",
        source_text="No active brain metastases on MRI.",
        extraction_timestamp="2026-09-28T12:00:00Z",
    )
    return ClinicalFact(
        fact_id="FACT_001",
        patient_id="PAT_001",
        concept=concept,
        value=value,
        assertion=assertion,
        confidence=confidence,
        source_text="No active brain metastases on MRI.",
        provenance=prov,
    )


class TestClinicalFact:
    """Test suite for clinical facts, assertions, negation, and confidence scoring."""

    def test_quantified_lab_fact_with_unit(self):
        """ClinicalFact representing numeric laboratory measurement with unit."""
        prov = FactProvenance(
            note_id="NOTE_001",
            patient_id="PAT_001",
            source_text="Absolute neutrophil count: 1.8 x 10^9/L.",
            extraction_timestamp="2026-09-28T12:00:00Z",
        )
        fact = ClinicalFact(
            fact_id="FACT_LAB",
            patient_id="PAT_001",
            concept="absolute_neutrophil_count",
            value=1.8,
            normalized_value=1.8,
            unit="x 10^9/L",
            assertion=AssertionType.AFFIRMED,
            source_text="Absolute neutrophil count: 1.8 x 10^9/L.",
            provenance=prov,
        )
        assert fact.value == 1.8
        assert fact.unit == "x 10^9/L"
        assert fact.assertion == AssertionType.AFFIRMED

    def test_negated_clinical_assertion(self):
        """Explicit clinical negation: assertion=NEGATED, value=False."""
        fact = _make_fact_with_assertion(AssertionType.NEGATED, "brain_metastases", False)
        assert fact.assertion == AssertionType.NEGATED
        assert fact.value is False

    def test_inconsistent_negation_flagged_by_validator(self):
        """Validator flags error if assertion is negated but value is True."""
        fact = _make_fact_with_assertion(AssertionType.NEGATED, "brain_metastases", True)
        profile = PatientClinicalProfile(
            patient_id="PAT_001",
            comorbidities=[fact],
        )
        validator = PatientProfileValidator()
        is_valid, issues = validator.validate_profile(profile)
        assert is_valid is False
        assert any(i.code == "INCONSISTENT_NEGATION_VALUE" for i in validator.errors)

    def test_possible_and_historical_assertions(self):
        """Possible/suspected condition vs historical resolved condition."""
        f_possible = _make_fact_with_assertion(AssertionType.POSSIBLE, "leptomeningeal_disease", "suspected")
        f_hist = _make_fact_with_assertion(AssertionType.HISTORICAL, "pulmonary_embolism", "resolved")

        assert f_possible.assertion == AssertionType.POSSIBLE
        assert f_hist.assertion == AssertionType.HISTORICAL

    def test_confidence_score_bounds(self):
        """Confidence score must be strictly between 0.0 and 1.0."""
        with pytest.raises(ValidationError):
            _make_fact_with_assertion(AssertionType.AFFIRMED, confidence=1.5)
        with pytest.raises(ValidationError):
            _make_fact_with_assertion(AssertionType.AFFIRMED, confidence=-0.1)

    def test_concept_min_length(self):
        """Concept must be at least 2 characters."""
        with pytest.raises(ValidationError):
            prov = FactProvenance(
                note_id="NOTE_001",
                patient_id="PAT_001",
                source_text="Some text",
                extraction_timestamp="2026-09-28T12:00:00Z",
            )
            ClinicalFact(
                fact_id="FACT_001",
                patient_id="PAT_001",
                concept="a",  # Too short!
                source_text="Some text",
                provenance=prov,
            )
