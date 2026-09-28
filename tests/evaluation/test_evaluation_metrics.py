"""
Tests for Phase 11 Evaluation Metrics Engine.
Phase 11: Evaluation & Ablation.
"""

from scripts.evaluation_metrics import EvaluationMetricsEngine


class TestEvaluationMetrics:
    """Verifies correctness and zero-denominator behavior across all metric dimensions."""

    def test_retrieval_metrics_populated(self):
        ranked = [["T1", "T2", "T3"], ["T2", "T1", "T4"]]
        golds = [{"T1"}, {"T1", "T4"}]
        metrics = EvaluationMetricsEngine.compute_retrieval_metrics(ranked, golds, k=2)

        assert metrics.total_queries == 2
        assert metrics.recall_at_k > 0.0
        assert metrics.precision_at_k > 0.0
        assert metrics.mrr > 0.0
        assert metrics.ndcg > 0.0

    def test_retrieval_metrics_zero_denominator_safeguards(self):
        metrics = EvaluationMetricsEngine.compute_retrieval_metrics([], [])
        assert metrics.total_queries == 0
        assert metrics.recall_at_k == 0.0
        assert metrics.precision_at_k == 0.0
        assert metrics.mrr == 0.0
        assert metrics.ndcg == 0.0

    def test_classification_metrics_populated(self):
        y_true = ["ELIGIBLE", "INELIGIBLE", "NEEDS_REVIEW", "ELIGIBLE"]
        y_pred = ["ELIGIBLE", "INELIGIBLE", "ELIGIBLE", "ELIGIBLE"]
        classes = ["ELIGIBLE", "INELIGIBLE", "NEEDS_REVIEW"]

        res = EvaluationMetricsEngine.compute_classification_metrics(y_true, y_pred, classes)
        assert res["accuracy"] == 0.75
        assert 0.0 <= res["macro_f1"] <= 1.0
        assert "f1_ELIGIBLE" in res
        assert "f1_INELIGIBLE" in res
        assert "f1_NEEDS_REVIEW" in res

    def test_classification_metrics_zero_denominator_safeguards(self):
        res = EvaluationMetricsEngine.compute_classification_metrics([], [])
        assert res["accuracy"] == 0.0
        assert res["macro_f1"] == 0.0

    def test_grounding_metrics_populated(self):
        gm = EvaluationMetricsEngine.compute_grounding_metrics(
            total_claims=10,
            supported_claims=8,
            unsupported_claims=1,
            contradicted_claims=1,
            total_citations=5,
            valid_citations=5,
            evaluated_criteria=10,
            grounded_criteria=8,
        )
        assert gm.claim_support_rate == 0.8
        assert gm.unsupported_claim_rate == 0.1
        assert gm.contradiction_rate == 0.1
        assert gm.citation_validity_rate == 1.0
        assert gm.evidence_coverage == 0.8
        assert 0.0 <= gm.grounding_score <= 1.0

    def test_grounding_metrics_zero_denominator_safeguards(self):
        gm = EvaluationMetricsEngine.compute_grounding_metrics(
            total_claims=0,
            supported_claims=0,
            unsupported_claims=0,
            contradicted_claims=0,
            total_citations=0,
            valid_citations=0,
            evaluated_criteria=0,
            grounded_criteria=0,
        )
        assert gm.claim_support_rate == 1.0
        assert gm.unsupported_claim_rate == 0.0
        assert gm.contradiction_rate == 0.0
        assert gm.citation_validity_rate == 1.0
        assert gm.evidence_coverage == 1.0

    def test_uncertainty_metrics_zero_denominator_safeguards(self):
        um = EvaluationMetricsEngine.compute_uncertainty_metrics(0, 0, 0, 0)
        assert um.total_evaluations == 0
        assert um.uncertainty_rate == 0.0
        assert um.review_routing_rate == 0.0

    def test_explainability_metrics_zero_denominator_safeguards(self):
        em = EvaluationMetricsEngine.compute_explainability_metrics(
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
        )
        assert em.evidence_coverage == 1.0
        assert em.decision_traceability_rate == 1.0
        assert em.unsupported_claim_rate == 0.0
        assert em.graph_integrity_rate == 1.0
