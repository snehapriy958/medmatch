"""
Unit tests for MedMatch Machine-Checkable Safety Invariants (INV-01 to INV-15).
Phase 12: Clinical Safety.
"""

from __future__ import annotations

import pytest
from scripts.safety_schema import SafetyInvariantID
from scripts.safety_validator import MachineCheckableSafetyValidator


def test_inv_01_no_fabricated_patient_facts():
    raw_note = "Patient is a 62yo female diagnosed with stage IV non-small cell lung cancer."
    valid_facts = [
        {"concept": "NSCLC", "snippet": "non-small cell lung cancer", "start_offset": 39, "end_offset": 67}
    ]
    is_valid, violations = MachineCheckableSafetyValidator.validate_all_invariants(
        patient_facts=valid_facts,
        trial_criteria=[],
        criterion_evaluations=[],
        final_trial_decision="ELIGIBLE",
        raw_note=raw_note,
    )
    assert is_valid is True
    assert len(violations) == 0

    # Fabricated fact
    fabricated_facts = [
        {"concept": "HER2 Amplification", "snippet": "HER2 3+ confirmed by FISH", "start_offset": 100, "end_offset": 124}
    ]
    is_valid_fab, violations_fab = MachineCheckableSafetyValidator.validate_all_invariants(
        patient_facts=fabricated_facts,
        trial_criteria=[],
        criterion_evaluations=[],
        final_trial_decision="ELIGIBLE",
        raw_note=raw_note,
    )
    assert is_valid_fab is False
    assert any(v["invariant_id"] == SafetyInvariantID.INV_01.value for v in violations_fab)


def test_inv_02_no_fabricated_trial_criteria():
    raw_note = "Valid clinical note text."
    trial_criteria = [
        {"criterion_id": "CRIT_01", "trial_id": "NCT02484404", "criteria_type": "INCLUSION"}
    ]
    evals = [{"criterion_id": "CRIT_99", "status": "UNKNOWN", "evidence": []}]
    is_valid, violations = MachineCheckableSafetyValidator.validate_all_invariants(
        patient_facts=[],
        trial_criteria=trial_criteria,
        criterion_evaluations=evals,
        final_trial_decision="NEEDS_REVIEW",
        raw_note=raw_note,
    )
    assert is_valid is False
    assert any(v["invariant_id"] == SafetyInvariantID.INV_02.value for v in violations)


def test_inv_03_no_unknown_to_pass_conversion():
    evals = [
        {"criterion_id": "C1", "status": "UNKNOWN", "evidence": []}
    ]
    is_valid, violations = MachineCheckableSafetyValidator.validate_all_invariants(
        patient_facts=[],
        trial_criteria=[{"criterion_id": "C1"}],
        criterion_evaluations=evals,
        final_trial_decision="ELIGIBLE",  # Invalid! Cannot be ELIGIBLE with UNKNOWN
        raw_note="Note",
    )
    assert is_valid is False
    assert any(v["invariant_id"] == SafetyInvariantID.INV_03.value for v in violations)


def test_inv_04_and_05_unsupported_pass_or_missing_info():
    # PASS with empty evidence
    evals = [
        {"criterion_id": "C1", "status": "PASS", "evidence": []}
    ]
    is_valid, violations = MachineCheckableSafetyValidator.validate_all_invariants(
        patient_facts=[],
        trial_criteria=[{"criterion_id": "C1"}],
        criterion_evaluations=evals,
        final_trial_decision="ELIGIBLE",
        raw_note="Note",
    )
    assert is_valid is False
    assert any(v["invariant_id"] == SafetyInvariantID.INV_04.value for v in violations)
    assert any(v["invariant_id"] == SafetyInvariantID.INV_05.value for v in violations)


def test_inv_06_unsupported_definitive_decision():
    # ELIGIBLE with a FAIL criterion
    evals = [
        {"criterion_id": "C1", "status": "FAIL", "evidence": ["contraindication noted"]}
    ]
    is_valid, violations = MachineCheckableSafetyValidator.validate_all_invariants(
        patient_facts=[],
        trial_criteria=[{"criterion_id": "C1"}],
        criterion_evaluations=evals,
        final_trial_decision="ELIGIBLE",
        raw_note="Note",
    )
    assert is_valid is False
    assert any(v["invariant_id"] == SafetyInvariantID.INV_06.value for v in violations)


def test_inv_07_traceable_evidence():
    evals = [
        {"criterion_id": "C1", "status": "PASS", "evidence": ["valid text"], "traceable": False}
    ]
    is_valid, violations = MachineCheckableSafetyValidator.validate_all_invariants(
        patient_facts=[],
        trial_criteria=[{"criterion_id": "C1"}],
        criterion_evaluations=evals,
        final_trial_decision="ELIGIBLE",
        raw_note="valid text",
    )
    assert is_valid is False
    assert any(v["invariant_id"] == SafetyInvariantID.INV_07.value for v in violations)


def test_inv_08_provenance_offset_integrity():
    raw_note = "Hemoglobin 14.2 g/dL."
    evals = [
        {
            "criterion_id": "C1",
            "status": "PASS",
            "evidence_citations": [
                {"snippet": "Platelets 150k", "start_offset": 0, "end_offset": 10}  # note[0:10] is "Hemoglobin"
            ],
        }
    ]
    is_valid, violations = MachineCheckableSafetyValidator.validate_all_invariants(
        patient_facts=[],
        trial_criteria=[{"criterion_id": "C1"}],
        criterion_evaluations=evals,
        final_trial_decision="ELIGIBLE",
        raw_note=raw_note,
    )
    assert is_valid is False
    assert any(v["invariant_id"] == SafetyInvariantID.INV_08.value for v in violations)


def test_inv_09_conflict_disclosure():
    facts = [
        {"concept": "EGFR Exon 19", "assertion": "PRESENT", "snippet": "EGFR+"},
        {"concept": "EGFR Exon 19", "assertion": "ABSENT", "snippet": "EGFR-"},
    ]
    # Decision is ELIGIBLE instead of NEEDS_REVIEW
    is_valid, violations = MachineCheckableSafetyValidator.validate_all_invariants(
        patient_facts=facts,
        trial_criteria=[],
        criterion_evaluations=[],
        final_trial_decision="ELIGIBLE",
        raw_note="EGFR+ and EGFR- found in conflicting reports.",
    )
    assert is_valid is False
    assert any(v["invariant_id"] == SafetyInvariantID.INV_09.value for v in violations)


def test_inv_10_temporal_validation():
    evals = [
        {"criterion_id": "C_WASH", "status": "PASS", "evidence": ["ev"], "has_temporal_constraint": True, "temporal_validated": False}
    ]
    is_valid, violations = MachineCheckableSafetyValidator.validate_all_invariants(
        patient_facts=[],
        trial_criteria=[{"criterion_id": "C_WASH"}],
        criterion_evaluations=evals,
        final_trial_decision="ELIGIBLE",
        raw_note="ev",
    )
    assert is_valid is False
    assert any(v["invariant_id"] == SafetyInvariantID.INV_10.value for v in violations)


def test_inv_11_numerical_validation():
    evals = [
        {"criterion_id": "C_NUM", "status": "PASS", "evidence": ["ev"], "has_numerical_constraint": True, "numerical_validated": False}
    ]
    is_valid, violations = MachineCheckableSafetyValidator.validate_all_invariants(
        patient_facts=[],
        trial_criteria=[{"criterion_id": "C_NUM"}],
        criterion_evaluations=evals,
        final_trial_decision="ELIGIBLE",
        raw_note="ev",
    )
    assert is_valid is False
    assert any(v["invariant_id"] == SafetyInvariantID.INV_11.value for v in violations)


def test_inv_12_and_13_override_auditing():
    # Missing original machine status
    bad_override_1 = {"original_machine_status": None, "reviewer_id": "REV_01", "rationale": "Clear clinical justification."}
    is_valid_1, violations_1 = MachineCheckableSafetyValidator.validate_all_invariants(
        patient_facts=[],
        trial_criteria=[],
        criterion_evaluations=[],
        final_trial_decision="ELIGIBLE",
        raw_note="Note",
        override_record=bad_override_1,
    )
    assert is_valid_1 is False
    assert any(v["invariant_id"] == SafetyInvariantID.INV_12.value for v in violations_1)

    # Missing rationale (< 10 chars)
    bad_override_2 = {"original_machine_status": "NEEDS_REVIEW", "reviewer_id": "REV_01", "rationale": "ok"}
    is_valid_2, violations_2 = MachineCheckableSafetyValidator.validate_all_invariants(
        patient_facts=[],
        trial_criteria=[],
        criterion_evaluations=[],
        final_trial_decision="ELIGIBLE",
        raw_note="Note",
        override_record=bad_override_2,
    )
    assert is_valid_2 is False
    assert any(v["invariant_id"] == SafetyInvariantID.INV_13.value for v in violations_2)


def test_inv_14_explanation_bounded_by_graph():
    # Brain scan claim without brain in note
    claims = ["Brain scan unremarkable, no intracranial metastases."]
    is_valid, violations = MachineCheckableSafetyValidator.validate_all_invariants(
        patient_facts=[],
        trial_criteria=[],
        criterion_evaluations=[],
        final_trial_decision="ELIGIBLE",
        raw_note="Patient has localized colon adenocarcinoma.",
        explanation_claims=claims,
    )
    assert is_valid is False
    assert any(v["invariant_id"] == SafetyInvariantID.INV_14.value for v in violations)


def test_inv_15_tenant_isolation():
    is_valid, violations = MachineCheckableSafetyValidator.validate_all_invariants(
        patient_facts=[],
        trial_criteria=[],
        criterion_evaluations=[],
        final_trial_decision="ELIGIBLE",
        raw_note="Note",
        user_hospital_id="HOSP_A",
        retrieved_hospital_id="HOSP_B",
    )
    assert is_valid is False
    assert any(v["invariant_id"] == SafetyInvariantID.INV_15.value for v in violations)
