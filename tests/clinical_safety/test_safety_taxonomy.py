"""
Unit tests for MedMatch Canonical Safety Error Taxonomy (S1 to S24).
Phase 12: Clinical Safety.
"""

from __future__ import annotations

import pytest
from scripts.safety_schema import (
    DefenseTier,
    SafetyGateID,
    SafetyInvariantID,
    SafetySeverity,
    SafetyTaxonomyCode,
)


def test_taxonomy_codes_completeness():
    """Verify that all 24 canonical safety taxonomy codes exist."""
    codes = [e.value for e in SafetyTaxonomyCode]
    assert len(codes) == 24
    for i in range(1, 25):
        assert f"S{i}" in codes


def test_taxonomy_severity_tiers():
    """Verify severity tiers exist and cover critical clinical risks."""
    severities = {e.value for e in SafetySeverity}
    assert "CRITICAL" in severities
    assert "HIGH" in severities
    assert "MEDIUM" in severities
    assert "LOW" in severities


def test_defense_tiers_completeness():
    """Verify all 4 canonical defense tiers exist."""
    tiers = {e.value for e in DefenseTier}
    assert "PREVENTION" in tiers
    assert "DETECTION" in tiers
    assert "MITIGATION" in tiers
    assert "HUMAN_REVIEW" in tiers


def test_safety_invariants_completeness():
    """Verify all 15 machine-checkable invariants exist."""
    invs = [e.value for e in SafetyInvariantID]
    assert len(invs) == 15
    for i in range(1, 16):
        assert f"INV-{i:02d}" in invs


def test_critical_taxonomy_mappings():
    """Verify critical safety error mappings to severity and defense tier."""
    # S1 (Fabricated Patient Fact) -> CRITICAL / PREVENTION
    from scripts.safety_gates import DeterministicSafetyGates
    res_s1 = DeterministicSafetyGates.gate_01_patient_fact_provenance(
        {"concept": "Metastasis", "snippet": "absent snippet"}, "patient note"
    )
    assert res_s1.taxonomy_code == SafetyTaxonomyCode.S1
    assert res_s1.severity == SafetySeverity.CRITICAL
    assert res_s1.defense_tier == DefenseTier.PREVENTION

    # S8 (Negation Error) -> CRITICAL / MITIGATION
    res_s8 = DeterministicSafetyGates.gate_08_negation_integrity("denies chest pain", "PRESENT")
    assert res_s8.taxonomy_code == SafetyTaxonomyCode.S8
    assert res_s8.severity == SafetySeverity.CRITICAL
    assert res_s8.defense_tier == DefenseTier.MITIGATION

    # S7 (Contradictory Evidence) -> HIGH / HUMAN_REVIEW
    res_s7 = DeterministicSafetyGates.gate_09_contradiction_escalation(
        [{"concept": "PDL1", "assertion": "PRESENT"}, {"concept": "PDL1", "assertion": "ABSENT"}]
    )
    assert res_s7.taxonomy_code == SafetyTaxonomyCode.S7
    assert res_s7.defense_tier == DefenseTier.HUMAN_REVIEW

    # S21 (Tenant Isolation) -> CRITICAL / PREVENTION
    res_s21 = DeterministicSafetyGates.gate_19_tenant_isolation("HOSP_A", "HOSP_B")
    assert res_s21.taxonomy_code == SafetyTaxonomyCode.S21
    assert res_s21.severity == SafetySeverity.CRITICAL
    assert res_s21.defense_tier == DefenseTier.PREVENTION
