"""
Tests for Canonical Patient Clinical Profile Schemas.
Phase 4: Patient Clinical Information Extraction.
"""

import json
from pathlib import Path
import pytest
from pydantic import ValidationError

from scripts.patient_schema import (
    AssertionType,
    ClinicalFact,
    EvidenceSource,
    FactProvenance,
    PatientClinicalProfile,
    PatientDemographics,
    PatientExtractionContract,
    TemporalContext,
    TemporalityType,
    UncertaintyStatus,
)


def _make_valid_fact(
    fact_id: str = "FACT_001",
    patient_id: str = "PAT_001",
    concept: str = "lung_adenocarcinoma",
    value: str = "Stage IV",
) -> ClinicalFact:
    prov = FactProvenance(
        note_id="NOTE_001",
        patient_id=patient_id,
        source_text="Confirmed Stage IV lung adenocarcinoma.",
        start_char=0,
        end_char=40,
        extraction_timestamp="2026-09-28T12:00:00Z",
    )
    return ClinicalFact(
        fact_id=fact_id,
        patient_id=patient_id,
        concept=concept,
        value=value,
        assertion=AssertionType.AFFIRMED,
        source_text="Confirmed Stage IV lung adenocarcinoma.",
        provenance=prov,
    )


class TestPatientSchema:
    """Test suite for canonical patient profile and fact schemas."""

    def test_patient_fact_valid_instantiation(self):
        fact = _make_valid_fact()
        assert fact.fact_id == "FACT_001"
        assert fact.patient_id == "PAT_001"
        assert fact.concept == "lung_adenocarcinoma"
        assert fact.assertion == AssertionType.AFFIRMED
        assert fact.provenance.note_id == "NOTE_001"

    def test_patient_id_provenance_mismatch_raises_error(self):
        """Fact patient_id must match provenance patient_id."""
        prov = FactProvenance(
            note_id="NOTE_001",
            patient_id="PAT_DIFFERENT",  # Mismatch!
            source_text="Confirmed adenocarcinoma",
            extraction_timestamp="2026-09-28T12:00:00Z",
        )
        with pytest.raises(ValidationError) as exc_info:
            ClinicalFact(
                fact_id="FACT_001",
                patient_id="PAT_001",
                concept="lung_adenocarcinoma",
                source_text="Confirmed adenocarcinoma",
                provenance=prov,
            )
        assert "Provenance patient_id" in str(exc_info.value)

    def test_demographics_age_bounds(self):
        """Demographics age must be within 0-130 range."""
        with pytest.raises(ValidationError):
            PatientDemographics(age=150)
        with pytest.raises(ValidationError):
            PatientDemographics(age=-5)
        demo = PatientDemographics(age=65, gender="Female")
        assert demo.age == 65
        assert demo.gender == "Female"

    def test_profile_all_facts_aggregation(self):
        """Profile all_facts() must collect facts across all categories."""
        f1 = _make_valid_fact("FACT_001", "PAT_001", "nsclc", True)
        f2 = _make_valid_fact("FACT_002", "PAT_001", "ecog", 1)
        f3 = _make_valid_fact("FACT_003", "PAT_001", "hypertension", True)

        profile = PatientClinicalProfile(
            patient_id="PAT_001",
            diagnoses=[f1],
            performance_status=f2,
            comorbidities=[f3],
        )

        facts = profile.all_facts()
        assert len(facts) == 3
        fact_ids = [f.fact_id for f in facts]
        assert "FACT_001" in fact_ids
        assert "FACT_002" in fact_ids
        assert "FACT_003" in fact_ids

    def test_json_roundtrip(self):
        """Patient profile must serialize and deserialize without loss."""
        f1 = _make_valid_fact("FACT_001", "PAT_001", "egfr", "exon 19 deletion")
        profile = PatientClinicalProfile(
            patient_id="PAT_001",
            demographics=PatientDemographics(age=58, gender="Male"),
            biomarkers=[f1],
            missing_information=["PD-L1 TPS"],
        )

        json_str = profile.model_dump_json()
        parsed = PatientClinicalProfile.model_validate_json(json_str)

        assert parsed.patient_id == profile.patient_id
        assert parsed.demographics.age == 58
        assert parsed.biomarkers[0].concept == "egfr"
        assert parsed.missing_information == ["PD-L1 TPS"]

    def test_extraction_contract_envelope(self):
        """Extraction contract should compute and validate fact summary counts."""
        f1 = _make_valid_fact("FACT_001", "PAT_001", "diagnosis", "adenocarcinoma")
        profile = PatientClinicalProfile(
            patient_id="PAT_001",
            diagnoses=[f1],
        )
        contract = PatientExtractionContract(
            status="SUCCESS",
            profile=profile,
            total_facts=1,
            affirmed_count=1,
            negated_count=0,
            uncertain_count=0,
            historical_count=0,
            conflicting_count=0,
            missing_concepts_count=0,
            validation_passed=True,
        )
        assert contract.total_facts == 1
        assert contract.affirmed_count == 1
