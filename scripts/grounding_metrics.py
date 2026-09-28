"""
MedMatch Grounding & Faithfulness Metrics Engine.
Phase 8: Grounding Evaluation & Faithfulness Auditing.

Defines pure, deterministic mathematical functions for:
1. Claim Support Rate (CSR)
2. Unsupported Claim Rate (UCR)
3. Contradiction Rate (CR)
4. Citation Validity Rate (CVR)
5. Evidence Coverage (EC)
6. Grounding Score (GS)
7. Hallucination Rate (HR)
8. Macro and Micro Aggregations across multiple evaluations

Handles edge cases:
- Zero total claims: returns 1.0 for rates where absence of violations is desired, 0.0 for coverage
- Zero citations: returns 1.0 (no invalid citations)
- Partially supported claims: treated as non-supported for strict CSR, but not penalized as hallucinations
- Contradicted claims: strictly counted in CR and HR, heavily penalized in GS
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

try:
    from scripts.grounding_schema import GroundingEvaluation, SupportStatus
except ImportError:
    from grounding_schema import GroundingEvaluation, SupportStatus


class GroundingMetricsEngine:
    """
    Mathematical metrics engine computing deterministic grounding and hallucination metrics.
    """

    @staticmethod
    def calculate_claim_support_rate(
        supported_count: int,
        total_evaluable_claims: int,
        include_partial: bool = False,
        partially_supported_count: int = 0,
    ) -> float:
        """
        Claim Support Rate (CSR) = (supported claims [+ 0.5 * partial]) / evaluable claims.
        Denominator handling: If total claims is 0, returns 1.0 (vacuously true).
        """
        if total_evaluable_claims <= 0:
            return 1.0
        numerator = float(supported_count)
        if include_partial:
            numerator += 0.5 * float(partially_supported_count)
        return round(min(1.0, max(0.0, numerator / float(total_evaluable_claims))), 4)

    @staticmethod
    def calculate_unsupported_claim_rate(
        unsupported_count: int, total_evaluable_claims: int
    ) -> float:
        """
        Unsupported Claim Rate (UCR) = unsupported claims / evaluable claims.
        Denominator handling: If total claims is 0, returns 0.0.
        """
        if total_evaluable_claims <= 0:
            return 0.0
        return round(min(1.0, max(0.0, float(unsupported_count) / float(total_evaluable_claims))), 4)

    @staticmethod
    def calculate_contradiction_rate(
        contradicted_count: int, total_evaluable_claims: int
    ) -> float:
        """
        Contradiction Rate (CR) = contradicted claims / evaluable claims.
        Denominator handling: If total claims is 0, returns 0.0.
        """
        if total_evaluable_claims <= 0:
            return 0.0
        return round(min(1.0, max(0.0, float(contradicted_count) / float(total_evaluable_claims))), 4)

    @staticmethod
    def calculate_citation_validity_rate(
        valid_citations: int, total_citations: int
    ) -> float:
        """
        Citation Validity Rate (CVR) = valid citations / total citations.
        Denominator handling: If no citations attached, returns 1.0 (no invalid citations).
        """
        if total_citations <= 0:
            return 1.0
        return round(min(1.0, max(0.0, float(valid_citations) / float(total_citations))), 4)

    @staticmethod
    def calculate_evidence_coverage(
        supported_factual_claims: int, claims_requiring_evidence: int
    ) -> float:
        """
        Evidence Coverage (EC) = supported factual claims / claims requiring evidence.
        Denominator handling: If no claims require evidence, returns 1.0.
        """
        if claims_requiring_evidence <= 0:
            return 1.0
        return round(min(1.0, max(0.0, float(supported_factual_claims) / float(claims_requiring_evidence))), 4)

    @staticmethod
    def calculate_hallucination_rate(
        unsupported_count: int, contradicted_count: int, total_evaluable_claims: int
    ) -> float:
        """
        Hallucination Rate (HR) = (unsupported + contradicted claims) / evaluable claims.
        Denominator handling: If total claims is 0, returns 0.0.
        """
        if total_evaluable_claims <= 0:
            return 0.0
        total_hallucinated = unsupported_count + contradicted_count
        return round(min(1.0, max(0.0, float(total_hallucinated) / float(total_evaluable_claims))), 4)

    @classmethod
    def calculate_grounding_score(
        cls,
        csr: float,
        cvr: float,
        ec: float,
        cr: float,
        weights: Optional[Dict[str, float]] = None,
    ) -> float:
        """
        Composite Grounding Score (GS) in [0.0, 1.0].
        Balances positive support and coverage against severe penalties for factual contradiction.
        GS = max(0.0, w_csr * CSR + w_cvr * CVR + w_ec * EC - w_cr * CR)
        Default weights: w_csr=0.5, w_cvr=0.25, w_ec=0.25, w_cr=1.0.
        """
        w = weights or {"csr": 0.5, "cvr": 0.25, "ec": 0.25, "cr": 1.0}
        score = (w["csr"] * csr) + (w["cvr"] * cvr) + (w["ec"] * ec) - (w["cr"] * cr)
        return round(min(1.0, max(0.0, score)), 4)

    @classmethod
    def aggregate_evaluations(
        cls, evaluations: List[GroundingEvaluation]
    ) -> Dict[str, Any]:
        """
        Computes macro- and micro-averaged metrics across a batch of GroundingEvaluations.
        """
        if not evaluations:
            return {
                "total_evaluations": 0,
                "macro_claim_support_rate": 0.0,
                "macro_unsupported_claim_rate": 0.0,
                "macro_contradiction_rate": 0.0,
                "macro_citation_validity_rate": 1.0,
                "macro_evidence_coverage": 0.0,
                "macro_grounding_score": 0.0,
                "macro_hallucination_rate": 0.0,
                "faithful_evaluation_count": 0,
                "faithfulness_percentage": 0.0,
            }

        n = float(len(evaluations))

        macro_csr = sum(e.claim_support_rate for e in evaluations) / n
        macro_ucr = sum(e.unsupported_claim_rate for e in evaluations) / n
        macro_cr = sum(e.contradiction_rate for e in evaluations) / n
        macro_cvr = sum(e.citation_validity_rate for e in evaluations) / n
        macro_ec = sum(e.evidence_coverage for e in evaluations) / n
        macro_gs = sum(e.grounding_score for e in evaluations) / n
        macro_hr = sum(e.hallucination_rate for e in evaluations) / n

        faithful_cnt = sum(1 for e in evaluations if e.is_faithful)
        faith_pct = round((faithful_cnt / n) * 100.0, 2)

        return {
            "total_evaluations": len(evaluations),
            "macro_claim_support_rate": round(macro_csr, 4),
            "macro_unsupported_claim_rate": round(macro_ucr, 4),
            "macro_contradiction_rate": round(macro_cr, 4),
            "macro_citation_validity_rate": round(macro_cvr, 4),
            "macro_evidence_coverage": round(macro_ec, 4),
            "macro_grounding_score": round(macro_gs, 4),
            "macro_hallucination_rate": round(macro_hr, 4),
            "faithful_evaluation_count": faithful_cnt,
            "faithfulness_percentage": faith_pct,
        }
