"""
Tests for Grounding & Faithfulness Metrics Engine.
Phase 8: Grounding Evaluation & Faithfulness Auditing.
"""

import pytest

from scripts.grounding_metrics import GroundingMetricsEngine
from scripts.grounding_schema import GroundingEvaluation


class TestGroundingMetricsEngine:
    """Verifies mathematical correctness and edge-case handling of all grounding metrics."""

    def test_claim_support_rate_normal_and_zero_denominator(self):
        """CSR returns correct ratio or 1.0 on zero claims."""
        assert GroundingMetricsEngine.calculate_claim_support_rate(3, 4) == 0.75
        assert GroundingMetricsEngine.calculate_claim_support_rate(0, 0) == 1.0

    def test_unsupported_claim_rate(self):
        """UCR returns correct ratio or 0.0 on zero claims."""
        assert GroundingMetricsEngine.calculate_unsupported_claim_rate(1, 4) == 0.25
        assert GroundingMetricsEngine.calculate_unsupported_claim_rate(0, 0) == 0.0

    def test_contradiction_rate(self):
        """CR returns correct ratio or 0.0 on zero claims."""
        assert GroundingMetricsEngine.calculate_contradiction_rate(1, 4) == 0.25
        assert GroundingMetricsEngine.calculate_contradiction_rate(0, 0) == 0.0

    def test_citation_validity_rate(self):
        """CVR returns valid / total or 1.0 if no citations exist."""
        assert GroundingMetricsEngine.calculate_citation_validity_rate(3, 4) == 0.75
        assert GroundingMetricsEngine.calculate_citation_validity_rate(0, 0) == 1.0

    def test_evidence_coverage(self):
        """EC returns supported / claims requiring evidence."""
        assert GroundingMetricsEngine.calculate_evidence_coverage(2, 2) == 1.0
        assert GroundingMetricsEngine.calculate_evidence_coverage(0, 0) == 1.0
        assert GroundingMetricsEngine.calculate_evidence_coverage(1, 2) == 0.5

    def test_hallucination_rate(self):
        """HR returns (unsupported + contradicted) / evaluable claims."""
        assert GroundingMetricsEngine.calculate_hallucination_rate(1, 1, 4) == 0.5
        assert GroundingMetricsEngine.calculate_hallucination_rate(0, 0, 0) == 0.0

    def test_grounding_score_penalizes_contradiction(self):
        """Grounding score applies severe penalty for contradictions."""
        perfect_gs = GroundingMetricsEngine.calculate_grounding_score(csr=1.0, cvr=1.0, ec=1.0, cr=0.0)
        assert perfect_gs == 1.0

        contradicted_gs = GroundingMetricsEngine.calculate_grounding_score(csr=0.5, cvr=1.0, ec=0.5, cr=0.5)
        # 0.5*0.5 + 0.25*1.0 + 0.25*0.5 - 1.0*0.5 = 0.25 + 0.25 + 0.125 - 0.5 = 0.125
        assert contradicted_gs == 0.125

    def test_aggregate_evaluations_macro_metrics(self):
        """Macro-averaging calculates arithmetic means across evaluations."""
        from scripts.grounding_schema import ClaimType, GroundingClaim, SupportStatus

        cl1 = GroundingClaim(
            claim_id="cl-1",
            claim_text="Supported claim",
            claim_type=ClaimType.PATIENT_FACT,
            support_status=SupportStatus.SUPPORTED,
        )
        cl2 = GroundingClaim(
            claim_id="cl-2",
            claim_text="Unsupported claim",
            claim_type=ClaimType.PATIENT_FACT,
            support_status=SupportStatus.UNSUPPORTED,
        )

        ev1 = GroundingEvaluation(
            evaluation_id="e1",
            trial_id="T1",
            criterion_id="c1",
            raw_reasoning_text="Reasoning 1",
            claims=[cl1],
            claim_support_rate=1.0,
            unsupported_claim_rate=0.0,
            contradiction_rate=0.0,
            citation_validity_rate=1.0,
            evidence_coverage=1.0,
            grounding_score=1.0,
            hallucination_rate=0.0,
            is_faithful=True,
            total_claims=1,
            supported_claim_count=1,
        )
        ev2 = GroundingEvaluation(
            evaluation_id="e2",
            trial_id="T1",
            criterion_id="c2",
            raw_reasoning_text="Reasoning 2",
            claims=[cl2],
            claim_support_rate=0.0,
            unsupported_claim_rate=1.0,
            contradiction_rate=0.0,
            citation_validity_rate=1.0,
            evidence_coverage=0.0,
            grounding_score=0.25,
            hallucination_rate=1.0,
            is_faithful=False,
            total_claims=1,
            unsupported_claim_count=1,
        )

        agg = GroundingMetricsEngine.aggregate_evaluations([ev1, ev2])
        assert agg["total_evaluations"] == 2
        assert agg["macro_claim_support_rate"] == 0.5
        assert agg["macro_unsupported_claim_rate"] == 0.5
        assert agg["macro_grounding_score"] == 0.625
        assert agg["faithful_evaluation_count"] == 1
        assert agg["faithfulness_percentage"] == 50.0
