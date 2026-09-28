"""
Unit tests for MedMatch Clinical Safety Metrics Engine (M-S01 to M-S14).
Phase 12: Clinical Safety.
"""

from __future__ import annotations

import pytest
from scripts.safety_metrics import SafetyMetricsEngine
from scripts.safety_schema import DefenseTier, SafetyGateID, SafetyGateResult


def test_zero_denominator_safeguards():
    """Verify that empty collections evaluate safely without ZeroDivisionError."""
    metrics = SafetyMetricsEngine.compute_safety_metrics(
        gate_results=[],
        trial_evaluations=[],
        criterion_evaluations=[],
        citations=[],
        overrides=[],
        explanations=[],
        tenant_requests=0,
        tenant_violations=0,
    )
    assert metrics.safety_gate_pass_rate == 1.0
    assert metrics.unsafe_decision_rate == 0.0
    assert metrics.unsupported_definitive_decision_rate == 0.0
    assert metrics.unknown_to_pass_violation_rate == 0.0
    assert metrics.missing_to_negative_violation_rate == 0.0
    assert metrics.evidence_support_rate == 1.0
    assert metrics.provenance_validity_rate == 1.0
    assert metrics.contradiction_disclosure_rate == 1.0
    assert metrics.temporal_safety_rate == 1.0
    assert metrics.numerical_safety_rate == 1.0
    assert metrics.human_review_routing_recall == 1.0
    assert metrics.human_override_auditability_rate == 1.0
    assert metrics.explanation_safety_rate == 1.0
    assert metrics.tenant_isolation_violation_rate == 0.0


def test_safety_gate_pass_rate_and_unsafe_rate():
    gates = [
        SafetyGateResult(gate_id=SafetyGateID.GATE_01, gate_name="G1", passed=True, defense_tier=DefenseTier.PREVENTION),
        SafetyGateResult(gate_id=SafetyGateID.GATE_02, gate_name="G2", passed=False, defense_tier=DefenseTier.PREVENTION),
    ]
    trials = [
        {"is_unsafe": False, "status": "ELIGIBLE"},
        {"is_unsafe": True, "status": "ELIGIBLE"},
    ]
    metrics = SafetyMetricsEngine.compute_safety_metrics(
        gate_results=gates,
        trial_evaluations=trials,
        criterion_evaluations=[],
        citations=[],
        overrides=[],
        explanations=[],
    )
    assert metrics.safety_gate_pass_rate == 0.50
    assert metrics.unsafe_decision_rate == 0.50
    assert metrics.total_gate_checks == 2
    assert metrics.total_evaluations == 2


def test_unknown_to_pass_and_missing_to_neg():
    crits = [
        {"gold_truth": "UNKNOWN", "predicted_status": "PASS"},
        {"gold_truth": "UNKNOWN", "predicted_status": "UNKNOWN"},
        {"is_missing_entity": True, "inferred_assertion": "ABSENT"},
        {"is_missing_entity": True, "inferred_assertion": "UNKNOWN"},
    ]
    metrics = SafetyMetricsEngine.compute_safety_metrics(
        gate_results=[],
        trial_evaluations=[],
        criterion_evaluations=crits,
        citations=[],
        overrides=[],
        explanations=[],
    )
    assert metrics.unknown_to_pass_violation_rate == 0.50
    assert metrics.missing_to_negative_violation_rate == 0.50


def test_human_review_and_tenant_metrics():
    trials = [
        {"status": "NEEDS_REVIEW", "unknown_count": 1},
        {"status": "ELIGIBLE", "unknown_count": 1},  # Failure to route
    ]
    metrics = SafetyMetricsEngine.compute_safety_metrics(
        gate_results=[],
        trial_evaluations=trials,
        criterion_evaluations=[],
        citations=[],
        overrides=[],
        explanations=[],
        tenant_requests=10,
        tenant_violations=1,
    )
    assert metrics.human_review_routing_recall == 0.50
    assert metrics.tenant_isolation_violation_rate == 0.10
