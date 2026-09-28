"""
Unit tests for MedMatch canonical schemas and clinical aggregation logic.
Phase 2: Dataset + Ground Truth.
"""

import pytest
from pydantic import ValidationError

from scripts.dataset_schema import (
    AnnotationSource,
    CanonicalCriterion,
    CanonicalPatient,
    CanonicalTrial,
    CriterionDomain,
    CriterionEvidence,
    CriterionGroundTruth,
    CriterionSummary,
    CriterionType,
    CriterionVerdict,
    LabValue,
    PatientEvidence,
    TrialEligibilityVerdict,
    TrialGroundTruth,
    compute_trial_eligibility,
    summarize_criterion_verdicts,
)


def test_canonical_trial_valid():
    trial = CanonicalTrial(
        trial_id="NCT01234567",
        source="clinicaltrials.gov",
        source_id="NCT01234567",
        title="Valid Test Clinical Trial",
        condition=["Non-Small Cell Lung Cancer"],
        intervention=["Pembrolizumab"],
        eligibility_text="Inclusion:\n1. Age >= 18",
        criteria=[
            CanonicalCriterion(
                criterion_id="NCT01234567_INC_01",
                trial_id="NCT01234567",
                criterion_type=CriterionType.INCLUSION,
                domain=CriterionDomain.AGE,
                source_text="Age >= 18 years.",
            )
        ],
    )
    assert trial.trial_id == "NCT01234567"
    assert len(trial.criteria) == 1


def test_canonical_trial_mismatched_criterion_id():
    with pytest.raises(ValidationError, match="mismatched trial_id"):
        CanonicalTrial(
            trial_id="NCT01234567",
            source_id="NCT01234567",
            title="Invalid Criterion Trial",
            eligibility_text="Inclusion:\n1. Age >= 18",
            criteria=[
                CanonicalCriterion(
                    criterion_id="NCT99999999_INC_01",
                    trial_id="NCT99999999",  # Mismatched parent ID
                    criterion_type=CriterionType.INCLUSION,
                    source_text="Age >= 18 years.",
                )
            ],
        )


def test_canonical_patient_valid():
    patient = CanonicalPatient(
        patient_id="P001",
        source="synthetic",
        age=55,
        sex="female",
        diagnoses=["NSCLC Stage IV"],
        biomarkers={"EGFR": "L858R"},
        laboratory_values=[LabValue(test_name="Platelets", value=150.0, unit="x 10^9/L")],
        clinical_note="55-year-old female with metastatic NSCLC harboring EGFR L858R.",
    )
    assert patient.patient_id == "P001"
    assert patient.age == 55
    assert patient.biomarkers["EGFR"] == "L858R"


def test_canonical_patient_invalid_age():
    with pytest.raises(ValidationError):
        CanonicalPatient(
            patient_id="P_INV",
            source="synthetic",
            age=150,  # Invalid age > 125
            clinical_note="Note text exceeds minimum length requirement.",
        )


def test_criterion_ground_truth_validation():
    # Valid PASS with evidence text
    cgt = CriterionGroundTruth(
        patient_id="P001",
        trial_id="NCT01234567",
        criterion_id="NCT01234567_INC_01",
        criterion_type=CriterionType.INCLUSION,
        ground_truth=CriterionVerdict.PASS,
        patient_evidence=PatientEvidence(text="55-year-old female", start_char=0, end_char=18),
        criterion_evidence=CriterionEvidence(text="Age >= 18"),
        annotation_source=AnnotationSource.SYNTHETIC,
    )
    assert cgt.ground_truth == CriterionVerdict.PASS

    # Invalid: PASS with empty evidence text
    with pytest.raises(ValidationError, match="empty patient_evidence.text"):
        CriterionGroundTruth(
            patient_id="P001",
            trial_id="NCT01234567",
            criterion_id="NCT01234567_INC_01",
            criterion_type=CriterionType.INCLUSION,
            ground_truth=CriterionVerdict.PASS,
            patient_evidence=PatientEvidence(text=""),
            criterion_evidence=CriterionEvidence(text="Age >= 18"),
            annotation_source=AnnotationSource.SYNTHETIC,
        )


def test_criterion_summary_sum_validation():
    # Valid summary: total = pass + fail + unknown
    cs = CriterionSummary(total=5, **{"pass": 3, "fail": 1, "unknown": 1})
    assert cs.total == 5

    # Invalid summary: total != sum
    with pytest.raises(ValidationError, match="total .* != sum"):
        CriterionSummary(total=10, **{"pass": 3, "fail": 1, "unknown": 1})


def test_deterministic_clinical_aggregation_logic():
    # 1. All PASS -> ELIGIBLE
    v1 = [CriterionVerdict.PASS, CriterionVerdict.PASS, CriterionVerdict.PASS]
    assert compute_trial_eligibility(v1) == TrialEligibilityVerdict.ELIGIBLE

    # 2. At least one FAIL -> INELIGIBLE (regardless of PASS)
    v2 = [CriterionVerdict.PASS, CriterionVerdict.FAIL, CriterionVerdict.PASS]
    assert compute_trial_eligibility(v2) == TrialEligibilityVerdict.INELIGIBLE

    # 3. FAIL dominates UNKNOWN -> INELIGIBLE
    v3 = [CriterionVerdict.UNKNOWN, CriterionVerdict.FAIL, CriterionVerdict.PASS]
    assert compute_trial_eligibility(v3) == TrialEligibilityVerdict.INELIGIBLE

    # 4. No FAIL, but at least one UNKNOWN -> NEEDS_REVIEW
    v4 = [CriterionVerdict.PASS, CriterionVerdict.UNKNOWN, CriterionVerdict.PASS]
    assert compute_trial_eligibility(v4) == TrialEligibilityVerdict.NEEDS_REVIEW

    # 5. Empty verdicts -> NEEDS_REVIEW
    assert compute_trial_eligibility([]) == TrialEligibilityVerdict.NEEDS_REVIEW


def test_summarize_criterion_verdicts():
    verdicts = [CriterionVerdict.PASS, CriterionVerdict.PASS, CriterionVerdict.FAIL, CriterionVerdict.UNKNOWN]
    summary = summarize_criterion_verdicts(verdicts)
    assert summary.total == 4
    assert summary.pass_count == 2
    assert summary.fail_count == 1
    assert summary.unknown_count == 1
