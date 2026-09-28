"""
Tests for Phase 10 Explainability Metrics Engine.
"""

from scripts.evidence_graph_builder import EvidenceGraphBuilder
from scripts.explainability_metrics import (
    ExplainabilityMetricsCalculator,
    ExplainabilityMetricsReport,
)
from scripts.explanation_generator import DeterministicExplanationGenerator


def test_zero_denominator_safeguards():
    """Verify that an empty input batch does not raise ZeroDivisionError and returns safe defaults."""
    report = ExplainabilityMetricsCalculator.calculate_metrics(graphs=[])

    assert isinstance(report, ExplainabilityMetricsReport)
    assert report.total_graphs == 0
    assert report.evidence_coverage == 0.0
    assert report.decision_traceability_rate == 0.0
    assert report.criterion_traceability_rate == 0.0
    assert report.provenance_validity_rate == 0.0
    assert report.explanation_support_rate == 0.0
    assert report.unsupported_explanation_claim_rate == 0.0
    assert report.contradiction_disclosure_rate == 1.0
    assert report.graph_integrity_rate == 0.0


def test_populated_metrics_calculation():
    """Verify metrics calculation across a valid populated graph and explanation."""
    builder = EvidenceGraphBuilder(graph_id="METRIC-G1", trial_id="T1", patient_id="P1")
    builder.add_trial_criterion("INC-1", "inclusion", "Age >= 18")
    frag_id = builder.add_source_fragment("FRAG-1", "DOC-1", "Age 30", start_char=0, end_char=6)
    builder.add_patient_fact("FACT-1", concept="age", value=30, source_fragment_id=frag_id)
    eval_id = builder.add_criterion_evaluation("EVAL-1", "INC-1", "PASS", "Valid age", supporting_fact_ids=["FACT-1"])
    dec_id = builder.add_eligibility_decision("DEC-1", "ELIGIBLE", "All met", contributing_eval_ids=[eval_id])
    graph = builder.build()

    exp = DeterministicExplanationGenerator.explain_criterion_evaluation(graph, eval_id)

    report = ExplainabilityMetricsCalculator.calculate_metrics(graphs=[graph], explanations=[exp])

    assert report.total_graphs == 1
    assert report.graph_integrity_rate == 1.0
    assert report.decision_traceability_rate == 1.0
    assert report.criterion_traceability_rate == 1.0
    assert report.evidence_coverage == 1.0
    assert report.explanation_support_rate == 1.0
    assert report.unsupported_explanation_claim_rate == 0.0
