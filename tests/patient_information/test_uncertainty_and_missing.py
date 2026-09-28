"""
Tests for Patient Uncertainty and Missing Information Representation.
Phase 4: Patient Clinical Information Extraction.
"""

import pytest
from scripts.patient_schema import (
    AssertionType,
    ClinicalFact,
    EvidenceSource,
    FactProvenance,
    PatientClinicalProfile,
    UncertaintyStatus,
)


def _make_fact_with_uncertainty(
    fact_id: str,
    concept: str,
    uncertainty: UncertaintyStatus,
    assertion: AssertionType = AssertionType.AFFIRMED,
) -> ClinicalFact:
    prov = FactProvenance(
        note_id="NOTE_001",
        patient_id="PAT_001",
        source_text="Verbatim text",
        extraction_timestamp="2026-09-28T12:00:00Z",
    )
    return ClinicalFact(
        fact_id=fact_id,
        patient_id="PAT_001",
        concept=concept,
        assertion=assertion,
        uncertainty=uncertainty,
        source_text="Verbatim text",
        provenance=prov,
    )


class TestUncertaintyAndMissingInformation:
    """Test suite for epistemic uncertainty, non-collapsing states, and missing information."""

    def test_non_collapsing_epistemic_states(self):
        """Verify that KNOWN, UNKNOWN, NOT_MENTIONED, UNCERTAIN, and CONFLICTING remain distinct."""
        f_known = _make_fact_with_uncertainty("F1", "egfr", UncertaintyStatus.KNOWN)
        f_unknown = _make_fact_with_uncertainty("F2", "her2", UncertaintyStatus.UNKNOWN, assertion=AssertionType.UNKNOWN)
        f_uncertain = _make_fact_with_uncertainty("F3", "adrenal_nodule", UncertaintyStatus.UNCERTAIN, assertion=AssertionType.POSSIBLE)
        f_conflicting = _make_fact_with_uncertainty("F4", "pleural_effusion", UncertaintyStatus.CONFLICTING, assertion=AssertionType.POSSIBLE)

        assert f_known.uncertainty != f_unknown.uncertainty
        assert f_unknown.uncertainty != f_uncertain.uncertainty
        assert f_uncertain.uncertainty != f_conflicting.uncertainty

    def test_unmentioned_concept_is_distinct_from_negated_concept(self):
        """Absence of mention must NEVER collapse into a negative clinical fact."""
        # Unmentioned concepts are recorded in missing_information
        profile = PatientClinicalProfile(
            patient_id="PAT_001",
            missing_information=["alk_translocation", "pd_l1_expression"],
        )
        assert "alk_translocation" in profile.missing_information
        # It must NOT appear in diagnoses or biomarkers as negated
        biomarker_concepts = [b.concept for b in profile.biomarkers]
        assert "alk_translocation" not in biomarker_concepts

    def test_conflicting_evidence_preservation(self):
        """Both discrepant reports must be preserved with CONFLICTING uncertainty."""
        prov1 = FactProvenance(
            note_id="CT_REPORT_01",
            patient_id="PAT_001",
            source_text="Moderate right pleural effusion noted.",
            extraction_timestamp="2026-09-28T12:00:00Z",
        )
        prov2 = FactProvenance(
            note_id="US_REPORT_01",
            patient_id="PAT_001",
            source_text="Ultrasound shows trace to no pleural fluid.",
            extraction_timestamp="2026-09-28T12:00:00Z",
        )
        f1 = ClinicalFact(
            fact_id="FACT_EFFUSION_CT",
            patient_id="PAT_001",
            concept="pleural_effusion",
            value="moderate",
            assertion=AssertionType.POSSIBLE,
            uncertainty=UncertaintyStatus.CONFLICTING,
            evidence_source=EvidenceSource.IMAGING_REPORT,
            source_text="Moderate right pleural effusion noted.",
            provenance=prov1,
        )
        f2 = ClinicalFact(
            fact_id="FACT_EFFUSION_US",
            patient_id="PAT_001",
            concept="pleural_effusion",
            value="none_or_trace",
            assertion=AssertionType.POSSIBLE,
            uncertainty=UncertaintyStatus.CONFLICTING,
            evidence_source=EvidenceSource.IMAGING_REPORT,
            source_text="Ultrasound shows trace to no pleural fluid.",
            provenance=prov2,
        )

        profile = PatientClinicalProfile(
            patient_id="PAT_001",
            uncertainty_records=[f1, f2],
        )
        assert len(profile.uncertainty_records) == 2
        assert all(f.uncertainty == UncertaintyStatus.CONFLICTING for f in profile.uncertainty_records)

    def test_patient_reported_vs_clinician_documented(self):
        """Self-reported history must be distinct from clinician documentation."""
        f_pt = _make_fact_with_uncertainty("F_PT", "penicillin_allergy", UncertaintyStatus.PATIENT_REPORTED)
        f_dr = _make_fact_with_uncertainty("F_DR", "ecog_ps", UncertaintyStatus.CLINICIAN_DOCUMENTED)

        assert f_pt.uncertainty == UncertaintyStatus.PATIENT_REPORTED
        assert f_dr.uncertainty == UncertaintyStatus.CLINICIAN_DOCUMENTED
