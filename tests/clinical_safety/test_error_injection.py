"""
Unit tests for MedMatch Deterministic Error Injection Suite (INJ-01 to INJ-14).
Phase 12: Clinical Safety.
"""

from __future__ import annotations

import pytest
from scripts.error_injector import DeterministicErrorInjector
from scripts.safety_metrics import SafetyMetricsEngine
from scripts.safety_schema import DefenseTier, SafetyGateID, SafetyTaxonomyCode


def test_all_14_injections_execute_and_intercept():
    """Verify that all 14 error injections execute and achieve 100% interception."""
    results = DeterministicErrorInjector.run_all_injections()
    assert len(results) == 14

    for r in results:
        # Every injected fault must be either detected, prevented, mitigated, or escalated
        assert r.detected or r.prevented or r.mitigated or r.escalated_to_review, f"Injection {r.injection_id} escaped interception!"
        assert r.target_gate is not None
        assert r.taxonomy_code is not None


def test_injection_tiers_distribution():
    """Verify error injection covers all 4 defense tiers."""
    results = DeterministicErrorInjector.run_all_injections()
    tiers = {r.defense_tier for r in results}
    assert DefenseTier.PREVENTION in tiers
    assert DefenseTier.DETECTION in tiers
    assert DefenseTier.MITIGATION in tiers
    assert DefenseTier.HUMAN_REVIEW in tiers


def test_error_injection_multi_tiered_summary():
    """Verify detailed multi-tiered error injection breakdown (no collapsed single metric)."""
    results = DeterministicErrorInjector.run_all_injections()
    summary = SafetyMetricsEngine.compute_error_injection_summary(results)

    assert summary.total_injections == 14
    # Prevention count and rate
    assert summary.prevented_count == 6
    assert summary.prevention_rate == round(6 / 14, 4)

    # Detection count and rate
    assert summary.detected_count == 14
    assert summary.detection_rate == 1.0

    # Mitigation count and rate
    assert summary.mitigated_count == 6
    assert summary.mitigation_rate == round(6 / 14, 4)

    # Human review routing count and rate
    assert summary.escalated_to_review_count == 3
    assert summary.human_review_routing_rate == round(3 / 14, 4)

    # Missed count and rate
    assert summary.missed_count == 0
    assert summary.missed_injection_rate == 0.0

    # Aggregate coverage
    assert summary.aggregate_interception_count == 14
    assert summary.aggregate_interception_rate == 1.0


def test_specific_injections():
    results = {r.injection_id: r for r in DeterministicErrorInjector.run_all_injections()}

    # INJ-01: Fabricated Fact -> PREVENTION
    assert results["INJ-01"].target_gate == SafetyGateID.GATE_01
    assert results["INJ-01"].taxonomy_code == SafetyTaxonomyCode.S1
    assert results["INJ-01"].prevented is True

    # INJ-04: Negation Flip -> MITIGATION
    assert results["INJ-04"].target_gate == SafetyGateID.GATE_08
    assert results["INJ-04"].taxonomy_code == SafetyTaxonomyCode.S8
    assert results["INJ-04"].mitigated is True

    # INJ-06: Numerical Boundary -> MITIGATION (S10)
    assert results["INJ-06"].target_gate == SafetyGateID.GATE_06
    assert results["INJ-06"].taxonomy_code == SafetyTaxonomyCode.S10

    # INJ-07: Incompatible Unit -> PREVENTION (S11)
    assert results["INJ-07"].target_gate == SafetyGateID.GATE_06
    assert results["INJ-07"].taxonomy_code == SafetyTaxonomyCode.S11
    assert results["INJ-07"].prevented is True

    # INJ-08: Contradiction Injection -> HUMAN_REVIEW (S7)
    assert results["INJ-08"].target_gate == SafetyGateID.GATE_09
    assert results["INJ-08"].escalated_to_review is True
    assert results["INJ-08"].taxonomy_code == SafetyTaxonomyCode.S7

    # INJ-12: Blank Override -> PREVENTION (GATE-16, S19)
    assert results["INJ-12"].target_gate == SafetyGateID.GATE_16
    assert results["INJ-12"].taxonomy_code == SafetyTaxonomyCode.S19
    assert results["INJ-12"].prevented is True

    # INJ-13: Cross-Tenant Injection -> PREVENTION (GATE-19, S21)
    assert results["INJ-13"].target_gate == SafetyGateID.GATE_19
    assert results["INJ-13"].taxonomy_code == SafetyTaxonomyCode.S21
    assert results["INJ-13"].prevented is True
