"""
Tests for Patient Profile Validator.
Phase 4: Patient Clinical Information Extraction.
"""

from pathlib import Path
import pytest

from scripts.patient_schema import (
    AssertionType,
    ClinicalFact,
    FactProvenance,
    PatientClinicalProfile,
    PatientDemographics,
)
from scripts.validate_patient_profile import (
    PatientProfileValidator,
    validate_patient_profile_file,
)


class TestProfileValidator:
    """Test suite for deterministic validation of patient clinical profiles."""

    def test_canonical_fixture_passes_cleanly(self):
        """The Phase 4 canonical development fixture must pass validation with 0 errors and 0 warnings."""
        fixture_path = Path("data/fixtures/phase4/patient_clinical_profile_fixture.json")
        assert fixture_path.exists(), f"Fixture file not found: {fixture_path}"

        is_valid, issues = validate_patient_profile_file(fixture_path)
        errors = [i for i in issues if i.severity == "ERROR"]
        warnings = [i for i in issues if i.severity == "WARNING"]

        assert is_valid is True
        assert len(errors) == 0
        assert len(warnings) == 0

    def test_missing_patient_id_caught(self):
        """Validator must report error on empty or missing patient_id."""
        validator = PatientProfileValidator()
        profile_dict = {
            "patient_id": "",  # Empty!
            "profile_version": "0.4.0",
        }
        is_valid, issues = validator.validate_profile(profile_dict)
        assert is_valid is False
        assert any(i.code == "MISSING_PATIENT_ID" for i in validator.errors)

    def test_duplicate_fact_id_caught(self):
        """Validator must flag error if two facts share the same fact_id."""
        prov = FactProvenance(
            note_id="NOTE_001",
            patient_id="PAT_001",
            source_text="Sample text",
            extraction_timestamp="2026-09-28T12:00:00Z",
        )
        f1 = ClinicalFact(
            fact_id="DUP_ID",
            patient_id="PAT_001",
            concept="hypertension",
            assertion=AssertionType.AFFIRMED,
            source_text="Sample text",
            provenance=prov,
        )
        f2 = ClinicalFact(
            fact_id="DUP_ID",  # Duplicate!
            patient_id="PAT_001",
            concept="diabetes",
            assertion=AssertionType.AFFIRMED,
            source_text="Sample text",
            provenance=prov,
        )

        profile = PatientClinicalProfile(
            patient_id="PAT_001",
            comorbidities=[f1, f2],
        )

        validator = PatientProfileValidator()
        is_valid, issues = validator.validate_profile(profile)
        assert is_valid is False
        assert any(i.code == "DUPLICATE_FACT_ID" for i in validator.errors)

    def test_inconsistent_negation_caught(self):
        """Fact with assertion=negated and value=True must fail validation."""
        prov = FactProvenance(
            note_id="NOTE_001",
            patient_id="PAT_001",
            source_text="Denies diabetes.",
            extraction_timestamp="2026-09-28T12:00:00Z",
        )
        fact = ClinicalFact(
            fact_id="FACT_001",
            patient_id="PAT_001",
            concept="diabetes",
            value=True,  # Inconsistent with negated!
            assertion=AssertionType.NEGATED,
            source_text="Denies diabetes.",
            provenance=prov,
        )
        profile = PatientClinicalProfile(
            patient_id="PAT_001",
            comorbidities=[fact],
        )

        validator = PatientProfileValidator()
        is_valid, issues = validator.validate_profile(profile)
        assert is_valid is False
        assert any(i.code == "INCONSISTENT_NEGATION_VALUE" for i in validator.errors)

    def test_invalid_demographic_age_caught(self):
        """Validator must report error if demographic age is outside 0-130 range."""
        validator = PatientProfileValidator()
        profile_dict = {
            "patient_id": "PAT_001",
            "demographics": {
                "age": 145,  # Invalid
            },
        }
        is_valid, issues = validator.validate_profile(profile_dict)
        assert is_valid is False
        assert any(i.code == "INVALID_DEMOGRAPHIC_AGE" or "less than or equal to 130" in i.message for i in validator.errors)

    def test_deterministic_validation(self):
        """Repeated validations of identical fixture must return identical issues."""
        fixture_path = Path("data/fixtures/phase4/patient_clinical_profile_fixture.json")
        res1, issues1 = validate_patient_profile_file(fixture_path)
        res2, issues2 = validate_patient_profile_file(fixture_path)

        assert res1 == res2
        assert [i.to_dict() for i in issues1] == [i.to_dict() for i in issues2]
