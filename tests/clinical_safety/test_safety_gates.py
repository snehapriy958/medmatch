"""
Unit tests for MedMatch Deterministic Safety Gates (GATE-01 to GATE-20).
Phase 12: Clinical Safety.
"""

from __future__ import annotations

import pytest
from scripts.safety_gates import DeterministicSafetyGates
from scripts.safety_schema import DefenseTier, SafetyGateID, SafetyTaxonomyCode


def test_gate_01_patient_fact_provenance():
    note = "Patient has Stage IV NSCLC confirmed on CT."
    # Valid fact in note
    valid_res = DeterministicSafetyGates.gate_01_patient_fact_provenance(
        {"concept": "Stage IV NSCLC", "snippet": "Stage IV NSCLC confirmed on CT"}, note
    )
    assert valid_res.passed is True

    # Fabricated fact
    fab_res = DeterministicSafetyGates.gate_01_patient_fact_provenance(
        {"concept": "HER2 3+", "snippet": "HER2 3+ amplified"}, note
    )
    assert fab_res.passed is False
    assert fab_res.taxonomy_code == SafetyTaxonomyCode.S1
    assert fab_res.defense_tier == DefenseTier.PREVENTION


def test_gate_02_criterion_schema_integrity():
    valid = {"criterion_id": "INC_01", "trial_id": "NCT02484404", "criteria_type": "INCLUSION"}
    assert DeterministicSafetyGates.gate_02_criterion_schema_integrity(valid).passed is True

    invalid = {"criterion_id": "", "trial_id": "NCT02484404"}
    res = DeterministicSafetyGates.gate_02_criterion_schema_integrity(invalid)
    assert res.passed is False
    assert res.taxonomy_code == SafetyTaxonomyCode.S2


def test_gate_03_retrieval_sufficiency():
    assert DeterministicSafetyGates.gate_03_retrieval_sufficiency([{"id": "c1"}]).passed is True
    res_empty = DeterministicSafetyGates.gate_03_retrieval_sufficiency([])
    assert res_empty.passed is False
    assert res_empty.taxonomy_code == SafetyTaxonomyCode.S13
    assert res_empty.defense_tier == DefenseTier.PREVENTION


def test_gate_04_temporal_validity():
    # Criterion-defined max_days = 30
    recent = {"concept": "platelets", "temporal": {"duration_days": 20}}
    assert DeterministicSafetyGates.gate_04_temporal_validity(recent, max_days=30).passed is True

    stale_criterion = {"concept": "platelets", "temporal": {"duration_days": 45}}
    res_crit = DeterministicSafetyGates.gate_04_temporal_validity(stale_criterion, max_days=30)
    assert res_crit.passed is False
    assert res_crit.taxonomy_code == SafetyTaxonomyCode.S22

    # Synthetic fixture default parameter (90d)
    stale_fixture = {"concept": "platelets", "temporal": {"duration_days": 180}}
    res_fix = DeterministicSafetyGates.gate_04_temporal_validity(stale_fixture)
    assert res_fix.passed is False
    assert res_fix.taxonomy_code == SafetyTaxonomyCode.S22


def test_gate_05_strict_tri_state():
    assert DeterministicSafetyGates.gate_05_strict_tri_state("PASS", ["evidence_span"]).passed is True
    # Pass with empty evidence violates gate
    res_empty = DeterministicSafetyGates.gate_05_strict_tri_state("PASS", [])
    assert res_empty.passed is False
    assert res_empty.taxonomy_code == SafetyTaxonomyCode.S5


def test_gate_06_numerical_boundary():
    # Platelets: 99.0 against >= 100.0
    res_below = DeterministicSafetyGates.gate_06_numerical_boundary(99.0, ">=", 100.0)
    assert res_below.metadata["inequality_satisfied"] is False

    # Platelets: 100.0 exact against >= 100.0
    res_exact = DeterministicSafetyGates.gate_06_numerical_boundary(100.0, ">=", 100.0)
    assert res_exact.metadata["inequality_satisfied"] is True

    # Unit conversion: 110 umol/L creatinine vs <= 1.5 mg/dL (110 umol/L = ~1.24 mg/dL <= 1.5)
    res_unit = DeterministicSafetyGates.gate_06_numerical_boundary(110.0, "<=", 1.5, "umol/L", "mg/dL")
    assert res_unit.metadata["inequality_satisfied"] is True

    # Incompatible/unsupported unit pair
    res_incomp = DeterministicSafetyGates.gate_06_numerical_boundary(100.0, "<=", 1.5, "U/L", "mg/dL")
    assert res_incomp.passed is False
    assert res_incomp.taxonomy_code == SafetyTaxonomyCode.S11


def test_gate_07_temporal_washout():
    # 20 days < 28 days -> FAIL
    res_viol = DeterministicSafetyGates.gate_07_temporal_washout(20, 28)
    assert res_viol.passed is False
    assert res_viol.taxonomy_code == SafetyTaxonomyCode.S9

    # 40 days >= 28 days -> PASS
    res_ok = DeterministicSafetyGates.gate_07_temporal_washout(40, 28)
    assert res_ok.passed is True


def test_gate_08_negation_integrity():
    res = DeterministicSafetyGates.gate_08_negation_integrity("Patient denies dyspnea", "PRESENT")
    assert res.passed is False
    assert res.taxonomy_code == SafetyTaxonomyCode.S8


def test_gate_09_contradiction_escalation():
    facts = [
        {"concept": "EGFR Exon 19", "assertion": "PRESENT"},
        {"concept": "EGFR Exon 19", "assertion": "ABSENT"},
    ]
    res = DeterministicSafetyGates.gate_09_contradiction_escalation(facts)
    assert res.passed is False
    assert res.taxonomy_code == SafetyTaxonomyCode.S7
    assert res.defense_tier == DefenseTier.HUMAN_REVIEW


def test_gate_10_protocol_discrepancy():
    syn = "Patients with active CNS metastases are excluded."
    body = "Patients with untreated or symptomatic brain metastases are excluded."
    res = DeterministicSafetyGates.gate_10_protocol_discrepancy(syn, body)
    assert res.passed is False
    assert res.taxonomy_code == SafetyTaxonomyCode.S2

    res_same = DeterministicSafetyGates.gate_10_protocol_discrepancy(syn, syn)
    assert res_same.passed is True


def test_gate_11_open_world_completeness():
    res_empty = DeterministicSafetyGates.gate_11_open_world_completeness([])
    assert res_empty.passed is False
    assert res_empty.taxonomy_code == SafetyTaxonomyCode.S4

    res_ev = DeterministicSafetyGates.gate_11_open_world_completeness(["brain MRI normal"])
    assert res_ev.passed is True


def test_gate_12_claim_grounding():
    nodes = [{"snippet": "Patient has confirmed Stage IV adenocarcinoma"}]
    # Supported claim
    assert DeterministicSafetyGates.gate_12_claim_grounding("Stage IV adenocarcinoma", nodes).passed is True

    # Ungrounded claim
    res_unsupp = DeterministicSafetyGates.gate_12_claim_grounding("Patient has brain metastases", nodes)
    assert res_unsupp.passed is False
    assert res_unsupp.taxonomy_code == SafetyTaxonomyCode.S3


def test_gate_14_deterministic_aggregation():
    # 1 fail -> INELIGIBLE
    _, status_fail = DeterministicSafetyGates.gate_14_deterministic_aggregation(["PASS", "FAIL", "PASS"])
    assert status_fail == "INELIGIBLE"

    # 1 unknown, 0 fail -> NEEDS_REVIEW
    _, status_unk = DeterministicSafetyGates.gate_14_deterministic_aggregation(["PASS", "UNKNOWN", "PASS"])
    assert status_unk == "NEEDS_REVIEW"

    # all pass -> ELIGIBLE
    _, status_elig = DeterministicSafetyGates.gate_14_deterministic_aggregation(["PASS", "PASS", "PASS"])
    assert status_elig == "ELIGIBLE"


def test_gate_15_mandatory_human_escalation():
    # Needs escalation when UNKNOWN present
    res_esc = DeterministicSafetyGates.gate_15_mandatory_human_escalation("NEEDS_REVIEW", unknown_count=1, has_conflicts=False)
    assert res_esc.passed is True
    assert res_esc.metadata["escalation_required"] is True

    # No escalation when clean ELIGIBLE
    res_clean = DeterministicSafetyGates.gate_15_mandatory_human_escalation("ELIGIBLE", unknown_count=0, has_conflicts=False)
    assert res_clean.passed is True
    assert res_clean.metadata["escalation_required"] is False


def test_gate_16_auditable_override():
    # Valid override
    valid = DeterministicSafetyGates.gate_16_auditable_override(
        "INELIGIBLE", "DR_LEE", "Confirmed tissue NGS re-run shows sensitizing mutation."
    )
    assert valid.passed is True

    # Empty rationale
    empty_rat = DeterministicSafetyGates.gate_16_auditable_override("INELIGIBLE", "DR_LEE", "")
    assert empty_rat.passed is False
    assert empty_rat.taxonomy_code == SafetyTaxonomyCode.S19


def test_gate_17_explanation_graph_alignment():
    nodes = [{"concept": "NSCLC", "snippet": "Stage IV NSCLC"}]
    # Hallucinated brain MRI
    res_hallu = DeterministicSafetyGates.gate_17_explanation_graph_alignment(
        "Patient is eligible; Brain MRI: clear with no metastases.", nodes
    )
    assert res_hallu.passed is False
    assert res_hallu.taxonomy_code == SafetyTaxonomyCode.S15

    # Aligned explanation
    res_aligned = DeterministicSafetyGates.gate_17_explanation_graph_alignment(
        "Patient has Stage IV NSCLC.", nodes
    )
    assert res_aligned.passed is True


def test_gate_18_verbatim_provenance():
    text = "Platelet count was 150 K/uL on 2026-03-01."
    # Valid match
    res_valid = DeterministicSafetyGates.gate_18_verbatim_provenance("Platelet count", text, 0, 14)
    assert res_valid.passed is True

    # Offset mismatch
    res_mismatch = DeterministicSafetyGates.gate_18_verbatim_provenance("Platelet count", text, 5, 25)
    assert res_mismatch.passed is False
    assert res_mismatch.taxonomy_code == SafetyTaxonomyCode.S16


def test_gate_19_tenant_isolation():
    # Matching tenant
    assert DeterministicSafetyGates.gate_19_tenant_isolation("HOSP_A", "HOSP_A", "HOSP_A").passed is True

    # User vs request mismatch
    mismatch = DeterministicSafetyGates.gate_19_tenant_isolation("HOSP_A", "HOSP_B")
    assert mismatch.passed is False
    assert mismatch.taxonomy_code == SafetyTaxonomyCode.S21
    assert mismatch.gate_name == "Tenant Boundary Enforcement Gate"

    # Cross-tenant candidate
    cross_cand = DeterministicSafetyGates.gate_19_tenant_isolation("HOSP_A", "HOSP_A", "HOSP_B")
    assert cross_cand.passed is False
    assert cross_cand.taxonomy_code == SafetyTaxonomyCode.S21


def test_gate_20_fail_closed_audit():
    assert DeterministicSafetyGates.gate_20_fail_closed_audit(True).passed is True
    res_fail = DeterministicSafetyGates.gate_20_fail_closed_audit(False)
    assert res_fail.passed is False
    assert res_fail.taxonomy_code == SafetyTaxonomyCode.S20
