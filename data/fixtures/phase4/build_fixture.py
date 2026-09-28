"""
Builds the canonical Phase 4 development fixture JSON files deterministically
with exact character offset calculations and validation.
"""

import json
from pathlib import Path
import sys

# Ensure root and scripts are in sys.path
root_dir = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(root_dir / "scripts"))

from patient_schema import (
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
from validate_patient_profile import PatientProfileValidator


RAW_NOTE_TEXT = (
    "CLINICAL ONCOLOGY CONSULTATION NOTE\n"
    "Patient: John Doe | MRN: MRN-100234 | Age: 63 | Gender: Male\n"
    "Date of Note: 2026-09-28\n\n"
    "HISTORY OF PRESENT ILLNESS:\n"
    "The patient is a 63-year-old male with histologically confirmed non-small cell lung cancer adenocarcinoma. "
    "Brain MRI completed on 2026-09-20 shows no active brain or leptomeningeal metastases. "
    "Past history is notable for childhood asthma resolved 15 years ago.\n\n"
    "CURRENT MEDICATIONS & ALLERGIES:\n"
    "1. Amlodipine 5mg oral daily for hypertension.\n"
    "2. Patient reports penicillin allergy causing mild childhood rash.\n\n"
    "TREATMENT HISTORY:\n"
    "Patient previously completed first-line Carboplatin and Pemetrexed chemotherapy. "
    "Stereotactic body radiation therapy was completed 27 days ago. "
    "Primary pulmonary wedge resection was performed on 2025-11-10.\n\n"
    "PHYSICAL EXAMINATION & PERFORMANCE STATUS:\n"
    "Attending oncologist documented ECOG performance status 1. "
    "Overall fair general condition noted at this visit.\n\n"
    "LABORATORY & MOLECULAR PROFILING:\n"
    "1. Absolute neutrophil count (ANC): 2.1 x 10^9/L.\n"
    "2. Next-generation sequencing: EGFR exon 19 deletion detected.\n\n"
    "IMAGING & UNCERTAIN FINDINGS:\n"
    "Chest and abdominal CT reveals a 1.2 cm suspicious adrenal nodule, indeterminate between adenoma versus metastasis. "
    "Furthermore, chest CT report on 2026-09-25 notes moderate right pleural effusion, whereas ultrasound on 2026-09-26 notes minimal to no pleural fluid.\n\n"
    "SUMMARY:\n"
    "Stage IV lung adenocarcinoma in a former smoker (40 pack-years)."
)


def generate_fixtures():
    patient_id = "PATIENT_SYNTH_001"
    note_id = "NOTE_ONC_20260928_001"
    ts = "2026-09-28T12:00:00Z"

    def _get_offsets(sub: str):
        start = RAW_NOTE_TEXT.find(sub)
        if start == -1:
            raise ValueError(f"Substring not found in RAW_NOTE_TEXT: '{sub}'")
        end = start + len(sub)
        return start, end

    # 1. Positive diagnosis
    s1 = "histologically confirmed non-small cell lung cancer adenocarcinoma"
    c1_s, c1_e = _get_offsets(s1)
    fact_1 = ClinicalFact(
        fact_id="FACT_001",
        patient_id=patient_id,
        concept="non_small_cell_lung_cancer_adenocarcinoma",
        value=True,
        assertion=AssertionType.AFFIRMED,
        temporality=TemporalContext(temporality_type=TemporalityType.CURRENT),
        uncertainty=UncertaintyStatus.KNOWN,
        evidence_source=EvidenceSource.PATHOLOGY_REPORT,
        source_text=s1,
        provenance=FactProvenance(
            note_id=note_id,
            patient_id=patient_id,
            source_text=s1,
            start_char=c1_s,
            end_char=c1_e,
            source_section="HISTORY OF PRESENT ILLNESS",
            extraction_timestamp=ts,
        ),
    )

    # 2. Negated diagnosis
    s2 = "no active brain or leptomeningeal metastases"
    c2_s, c2_e = _get_offsets(s2)
    fact_2 = ClinicalFact(
        fact_id="FACT_002",
        patient_id=patient_id,
        concept="brain_or_leptomeningeal_metastases",
        value=False,
        assertion=AssertionType.NEGATED,
        temporality=TemporalContext(temporality_type=TemporalityType.CURRENT),
        uncertainty=UncertaintyStatus.KNOWN,
        evidence_source=EvidenceSource.IMAGING_REPORT,
        source_text=s2,
        provenance=FactProvenance(
            note_id=note_id,
            patient_id=patient_id,
            source_text=s2,
            start_char=c2_s,
            end_char=c2_e,
            source_section="HISTORY OF PRESENT ILLNESS",
            extraction_timestamp=ts,
        ),
    )

    # 3. Historical diagnosis
    s3 = "childhood asthma resolved 15 years ago"
    c3_s, c3_e = _get_offsets(s3)
    fact_3 = ClinicalFact(
        fact_id="FACT_003",
        patient_id=patient_id,
        concept="childhood_asthma",
        value="resolved",
        assertion=AssertionType.HISTORICAL,
        temporality=TemporalContext(
            temporality_type=TemporalityType.HISTORICAL,
            relative_interval="15 years ago",
        ),
        uncertainty=UncertaintyStatus.KNOWN,
        evidence_source=EvidenceSource.CLINICIAN_NOTE,
        source_text=s3,
        provenance=FactProvenance(
            note_id=note_id,
            patient_id=patient_id,
            source_text=s3,
            start_char=c3_s,
            end_char=c3_e,
            source_section="HISTORY OF PRESENT ILLNESS",
            extraction_timestamp=ts,
        ),
    )

    # 4. Current medication
    s4 = "Amlodipine 5mg oral daily for hypertension"
    c4_s, c4_e = _get_offsets(s4)
    fact_4 = ClinicalFact(
        fact_id="FACT_004",
        patient_id=patient_id,
        concept="amlodipine",
        value="5mg daily",
        assertion=AssertionType.AFFIRMED,
        temporality=TemporalContext(temporality_type=TemporalityType.CURRENT),
        uncertainty=UncertaintyStatus.KNOWN,
        evidence_source=EvidenceSource.MEDICATION_RECONCILIATION,
        source_text=s4,
        provenance=FactProvenance(
            note_id=note_id,
            patient_id=patient_id,
            source_text=s4,
            start_char=c4_s,
            end_char=c4_e,
            source_section="CURRENT MEDICATIONS & ALLERGIES",
            extraction_timestamp=ts,
        ),
    )

    # 5. Historical medication
    s5 = "first-line Carboplatin and Pemetrexed chemotherapy"
    c5_s, c5_e = _get_offsets(s5)
    fact_5 = ClinicalFact(
        fact_id="FACT_005",
        patient_id=patient_id,
        concept="carboplatin_pemetrexed_chemotherapy",
        value="completed",
        assertion=AssertionType.HISTORICAL,
        temporality=TemporalContext(temporality_type=TemporalityType.HISTORICAL),
        uncertainty=UncertaintyStatus.KNOWN,
        evidence_source=EvidenceSource.CLINICIAN_NOTE,
        source_text=s5,
        provenance=FactProvenance(
            note_id=note_id,
            patient_id=patient_id,
            source_text=s5,
            start_char=c5_s,
            end_char=c5_e,
            source_section="TREATMENT HISTORY",
            extraction_timestamp=ts,
        ),
    )

    # 6. Laboratory result with unit
    s6 = "Absolute neutrophil count (ANC): 2.1 x 10^9/L"
    c6_s, c6_e = _get_offsets(s6)
    fact_6 = ClinicalFact(
        fact_id="FACT_006",
        patient_id=patient_id,
        concept="absolute_neutrophil_count",
        value=2.1,
        normalized_value=2.1,
        unit="x 10^9/L",
        assertion=AssertionType.AFFIRMED,
        temporality=TemporalContext(temporality_type=TemporalityType.CURRENT),
        uncertainty=UncertaintyStatus.KNOWN,
        evidence_source=EvidenceSource.LABORATORY_REPORT,
        source_text=s6,
        provenance=FactProvenance(
            note_id=note_id,
            patient_id=patient_id,
            source_text=s6,
            start_char=c6_s,
            end_char=c6_e,
            source_section="LABORATORY & MOLECULAR PROFILING",
            extraction_timestamp=ts,
        ),
    )

    # 7. Biomarker status
    s7 = "EGFR exon 19 deletion detected"
    c7_s, c7_e = _get_offsets(s7)
    fact_7 = ClinicalFact(
        fact_id="FACT_007",
        patient_id=patient_id,
        concept="egfr_exon_19_deletion",
        value=True,
        assertion=AssertionType.AFFIRMED,
        temporality=TemporalContext(temporality_type=TemporalityType.CURRENT),
        uncertainty=UncertaintyStatus.KNOWN,
        evidence_source=EvidenceSource.PATHOLOGY_REPORT,
        source_text=s7,
        provenance=FactProvenance(
            note_id=note_id,
            patient_id=patient_id,
            source_text=s7,
            start_char=c7_s,
            end_char=c7_e,
            source_section="LABORATORY & MOLECULAR PROFILING",
            extraction_timestamp=ts,
        ),
    )

    # 8. Uncertain information
    s8 = "suspicious adrenal nodule, indeterminate between adenoma versus metastasis"
    c8_s, c8_e = _get_offsets(s8)
    fact_8 = ClinicalFact(
        fact_id="FACT_008",
        patient_id=patient_id,
        concept="adrenal_metastasis",
        value="indeterminate",
        assertion=AssertionType.POSSIBLE,
        temporality=TemporalContext(temporality_type=TemporalityType.CURRENT),
        uncertainty=UncertaintyStatus.UNCERTAIN,
        evidence_source=EvidenceSource.IMAGING_REPORT,
        source_text=s8,
        provenance=FactProvenance(
            note_id=note_id,
            patient_id=patient_id,
            source_text=s8,
            start_char=c8_s,
            end_char=c8_e,
            source_section="IMAGING & UNCERTAIN FINDINGS",
            extraction_timestamp=ts,
        ),
    )

    # 9. Conflicting evidence
    s9 = "chest CT report on 2026-09-25 notes moderate right pleural effusion, whereas ultrasound on 2026-09-26 notes minimal to no pleural fluid"
    c9_s, c9_e = _get_offsets(s9)
    fact_9 = ClinicalFact(
        fact_id="FACT_009",
        patient_id=patient_id,
        concept="pleural_effusion",
        value="discrepant",
        assertion=AssertionType.POSSIBLE,
        temporality=TemporalContext(temporality_type=TemporalityType.CURRENT),
        uncertainty=UncertaintyStatus.CONFLICTING,
        evidence_source=EvidenceSource.IMAGING_REPORT,
        source_text=s9,
        provenance=FactProvenance(
            note_id=note_id,
            patient_id=patient_id,
            source_text=s9,
            start_char=c9_s,
            end_char=c9_e,
            source_section="IMAGING & UNCERTAIN FINDINGS",
            extraction_timestamp=ts,
        ),
    )

    # 10. Temporal event
    s10 = "Primary pulmonary wedge resection was performed on 2025-11-10"
    c10_s, c10_e = _get_offsets(s10)
    fact_10 = ClinicalFact(
        fact_id="FACT_010",
        patient_id=patient_id,
        concept="pulmonary_wedge_resection",
        value=True,
        assertion=AssertionType.HISTORICAL,
        temporality=TemporalContext(
            temporality_type=TemporalityType.DATE_SPECIFIC,
            reference_date="2025-11-10",
            anchor_event="primary_surgical_resection",
        ),
        uncertainty=UncertaintyStatus.KNOWN,
        evidence_source=EvidenceSource.SURGICAL_REPORT,
        source_text=s10,
        provenance=FactProvenance(
            note_id=note_id,
            patient_id=patient_id,
            source_text=s10,
            start_char=c10_s,
            end_char=c10_e,
            source_section="TREATMENT HISTORY",
            extraction_timestamp=ts,
        ),
    )

    # 11. Relative temporal statement
    s11 = "Stereotactic body radiation therapy was completed 27 days ago"
    c11_s, c11_e = _get_offsets(s11)
    fact_11 = ClinicalFact(
        fact_id="FACT_011",
        patient_id=patient_id,
        concept="stereotactic_body_radiation_therapy",
        value="completed",
        assertion=AssertionType.HISTORICAL,
        temporality=TemporalContext(
            temporality_type=TemporalityType.RELATIVE_INTERVAL,
            relative_interval="27 days ago",
            relative_days_offset=-27,
            anchor_event="radiation_completion",
        ),
        uncertainty=UncertaintyStatus.KNOWN,
        evidence_source=EvidenceSource.CLINICIAN_NOTE,
        source_text=s11,
        provenance=FactProvenance(
            note_id=note_id,
            patient_id=patient_id,
            source_text=s11,
            start_char=c11_s,
            end_char=c11_e,
            source_section="TREATMENT HISTORY",
            extraction_timestamp=ts,
        ),
    )

    # 12. Patient-reported information
    s12 = "Patient reports penicillin allergy causing mild childhood rash"
    c12_s, c12_e = _get_offsets(s12)
    fact_12 = ClinicalFact(
        fact_id="FACT_012",
        patient_id=patient_id,
        concept="penicillin_allergy",
        value="mild childhood rash",
        assertion=AssertionType.AFFIRMED,
        temporality=TemporalContext(temporality_type=TemporalityType.HISTORICAL),
        uncertainty=UncertaintyStatus.PATIENT_REPORTED,
        evidence_source=EvidenceSource.PATIENT_PORTAL,
        source_text=s12,
        provenance=FactProvenance(
            note_id=note_id,
            patient_id=patient_id,
            source_text=s12,
            start_char=c12_s,
            end_char=c12_e,
            source_section="CURRENT MEDICATIONS & ALLERGIES",
            extraction_timestamp=ts,
        ),
    )

    # 13. Clinician-documented information
    s13 = "Attending oncologist documented ECOG performance status 1"
    c13_s, c13_e = _get_offsets(s13)
    fact_13 = ClinicalFact(
        fact_id="FACT_013",
        patient_id=patient_id,
        concept="ecog_performance_status",
        value=1,
        normalized_value=1,
        assertion=AssertionType.AFFIRMED,
        temporality=TemporalContext(temporality_type=TemporalityType.CURRENT),
        uncertainty=UncertaintyStatus.CLINICIAN_DOCUMENTED,
        evidence_source=EvidenceSource.CLINICIAN_NOTE,
        source_text=s13,
        provenance=FactProvenance(
            note_id=note_id,
            patient_id=patient_id,
            source_text=s13,
            start_char=c13_s,
            end_char=c13_e,
            source_section="PHYSICAL EXAMINATION & PERFORMANCE STATUS",
            extraction_timestamp=ts,
        ),
    )

    # 14 & 15. Multiple facts in one sentence
    s14_15 = "Stage IV lung adenocarcinoma in a former smoker (40 pack-years)"
    c14_s, c14_e = _get_offsets(s14_15)

    fact_14 = ClinicalFact(
        fact_id="FACT_014",
        patient_id=patient_id,
        concept="disease_stage",
        value="Stage IV",
        assertion=AssertionType.AFFIRMED,
        temporality=TemporalContext(temporality_type=TemporalityType.CURRENT),
        uncertainty=UncertaintyStatus.KNOWN,
        evidence_source=EvidenceSource.CLINICIAN_NOTE,
        source_text=s14_15,
        provenance=FactProvenance(
            note_id=note_id,
            patient_id=patient_id,
            source_text=s14_15,
            start_char=c14_s,
            end_char=c14_e,
            source_section="SUMMARY",
            extraction_timestamp=ts,
        ),
    )

    fact_15 = ClinicalFact(
        fact_id="FACT_015",
        patient_id=patient_id,
        concept="smoking_history",
        value="former smoker (40 pack-years)",
        assertion=AssertionType.HISTORICAL,
        temporality=TemporalContext(temporality_type=TemporalityType.HISTORICAL),
        uncertainty=UncertaintyStatus.KNOWN,
        evidence_source=EvidenceSource.CLINICIAN_NOTE,
        source_text=s14_15,
        provenance=FactProvenance(
            note_id=note_id,
            patient_id=patient_id,
            source_text=s14_15,
            start_char=c14_s,
            end_char=c14_e,
            source_section="SUMMARY",
            extraction_timestamp=ts,
        ),
    )

    # 16. Ambiguous clinical statement
    s16 = "Overall fair general condition noted at this visit"
    c16_s, c16_e = _get_offsets(s16)
    fact_16 = ClinicalFact(
        fact_id="FACT_016",
        patient_id=patient_id,
        concept="general_health_status",
        value="fair",
        assertion=AssertionType.POSSIBLE,
        temporality=TemporalContext(temporality_type=TemporalityType.CURRENT),
        uncertainty=UncertaintyStatus.UNCERTAIN,
        evidence_source=EvidenceSource.CLINICIAN_NOTE,
        source_text=s16,
        provenance=FactProvenance(
            note_id=note_id,
            patient_id=patient_id,
            source_text=s16,
            start_char=c16_s,
            end_char=c16_e,
            source_section="PHYSICAL EXAMINATION & PERFORMANCE STATUS",
            extraction_timestamp=ts,
        ),
    )

    # Build Profile
    profile = PatientClinicalProfile(
        patient_id=patient_id,
        profile_version="0.4.0",
        source_reference=note_id,
        demographics=PatientDemographics(
            age=63,
            gender="Male",
            birth_date="1963-04-12",
        ),
        diagnoses=[fact_1],
        medications=[fact_4],
        allergies=[fact_12],
        laboratory_results=[fact_6],
        biomarkers=[fact_7],
        disease_stage=fact_14,
        performance_status=fact_13,
        comorbidities=[fact_2, fact_3, fact_15],
        treatment_history=[fact_5, fact_10, fact_11],
        uncertainty_records=[fact_8, fact_9, fact_16],
        missing_information=[
            "PD-L1 tumor proportion score (TPS) expression status",
            "KRAS G12C mutation status",
            "Baseline serum creatinine / creatinine clearance",
        ],
    )

    # Validate with validator
    validator = PatientProfileValidator()
    is_valid, issues = validator.validate_profile(profile)
    assert is_valid, f"Generated patient profile failed validation: {[i.to_dict() for i in issues]}"

    # Build Extraction Contract
    all_facts = profile.all_facts()
    affirmed_count = sum(1 for f in all_facts if f.assertion == AssertionType.AFFIRMED)
    negated_count = sum(1 for f in all_facts if f.assertion == AssertionType.NEGATED)
    uncertain_count = sum(1 for f in all_facts if f.assertion in (AssertionType.POSSIBLE, AssertionType.UNKNOWN))
    historical_count = sum(1 for f in all_facts if f.assertion == AssertionType.HISTORICAL)
    conflicting_count = sum(1 for f in all_facts if f.uncertainty == UncertaintyStatus.CONFLICTING)

    contract = PatientExtractionContract(
        status="SUCCESS",
        profile=profile,
        total_facts=len(all_facts),
        affirmed_count=affirmed_count,
        negated_count=negated_count,
        uncertain_count=uncertain_count,
        historical_count=historical_count,
        conflicting_count=conflicting_count,
        missing_concepts_count=len(profile.missing_information),
        validation_passed=True,
        validation_messages=["Patient profile passed all clinical fact integrity and provenance verifications."],
    )

    out_dir = Path(__file__).resolve().parent
    profile_path = out_dir / "patient_clinical_profile_fixture.json"
    contract_path = out_dir / "patient_extraction_contract.json"

    with open(profile_path, "w", encoding="utf-8") as f:
        json.dump(profile.model_dump(), f, indent=2)

    with open(contract_path, "w", encoding="utf-8") as f:
        json.dump(contract.model_dump(), f, indent=2)

    print(f"Generated Phase 4 fixtures successfully:\n  {profile_path}\n  {contract_path}")


if __name__ == "__main__":
    generate_fixtures()
