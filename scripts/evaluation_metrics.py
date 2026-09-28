"""
MedMatch Comprehensive Evaluation Metrics Engine.
Phase 11: Evaluation & Ablation.

Computes metrics across all five evaluation dimensions:
1. Retrieval Metrics (Recall@K, Precision@K, MRR, nDCG)
2. Eligibility Reasoning Metrics (Accuracy, Precision, Recall, Macro-F1, Per-Class F1)
3. Grounding Metrics (Claim Support Rate, Unsupported Rate, Contradiction Rate, Citation Validity)
4. Uncertainty Metrics (Uncertainty Rate, Review Routing Rate, Unresolved Uncertainty)
5. Explainability Metrics (Traceability, Provenance Validity, Graph Integrity)

All metrics enforce explicit zero-denominator safeguards and mathematical defensibility.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence, Set

try:
    from scripts.evaluation_schema import (
        EligibilityMetrics,
        ExplainabilityMetricsSummary,
        GroundingMetricsSummary,
        RetrievalMetrics,
        UncertaintyMetricsSummary,
    )
except ImportError:
    from evaluation_schema import (
        EligibilityMetrics,
        ExplainabilityMetricsSummary,
        GroundingMetricsSummary,
        RetrievalMetrics,
        UncertaintyMetricsSummary,
    )


class EvaluationMetricsEngine:
    """
    Unified metrics engine for Phase 11 experimental evaluation.
    """

    # =========================================================================
    # 1. RETRIEVAL METRICS
    # =========================================================================

    @staticmethod
    def compute_retrieval_metrics(
        retrieved_ranked_ids: List[List[str]],
        gold_relevant_ids: List[Set[str]],
        k: int = 5,
    ) -> RetrievalMetrics:
        """
        Computes Recall@K, Precision@K, MRR, and nDCG@K across multiple queries.
        Zero-denominator behavior: if 0 queries, returns all 0.0.
        """
        if not retrieved_ranked_ids or not gold_relevant_ids:
            return RetrievalMetrics()

        num_queries = len(gold_relevant_ids)
        if num_queries == 0:
            return RetrievalMetrics()

        recalls: List[float] = []
        precisions: List[float] = []
        rr_list: List[float] = []
        ndcg_list: List[float] = []

        for preds, golds in zip(retrieved_ranked_ids, gold_relevant_ids):
            top_k_preds = preds[:k]
            if not golds:
                # If no relevant items exist for this query, skip or treat as vacuously 1.0 / 0.0
                recalls.append(1.0 if not top_k_preds else 0.0)
                precisions.append(1.0 if not top_k_preds else 0.0)
                rr_list.append(0.0)
                ndcg_list.append(0.0)
                continue

            hits = sum(1 for p in top_k_preds if p in golds)
            precision = hits / float(k) if k > 0 else 0.0
            recall = hits / float(len(golds)) if len(golds) > 0 else 0.0
            precisions.append(precision)
            recalls.append(recall)

            # MRR
            first_hit_rank = 0
            for rank, p in enumerate(preds, start=1):
                if p in golds:
                    first_hit_rank = rank
                    break
            rr = (1.0 / float(first_hit_rank)) if first_hit_rank > 0 else 0.0
            rr_list.append(rr)

            # nDCG@K (binary relevance: 1 if in golds, else 0)
            dcg = 0.0
            for rank, p in enumerate(top_k_preds, start=1):
                rel = 1.0 if p in golds else 0.0
                dcg += rel / math.log2(rank + 1)

            # Ideal DCG
            idcg = 0.0
            for rank in range(1, min(len(golds), k) + 1):
                idcg += 1.0 / math.log2(rank + 1)

            ndcg = (dcg / idcg) if idcg > 0.0 else 0.0
            ndcg_list.append(ndcg)

        return RetrievalMetrics(
            recall_at_k=round(sum(recalls) / float(num_queries), 4),
            precision_at_k=round(sum(precisions) / float(num_queries), 4),
            mrr=round(sum(rr_list) / float(num_queries), 4),
            ndcg=round(sum(ndcg_list) / float(num_queries), 4),
            total_queries=num_queries,
        )

    # =========================================================================
    # 2. ELIGIBILITY METRICS
    # =========================================================================

    @staticmethod
    def compute_classification_metrics(
        y_true: List[str],
        y_pred: List[str],
        classes: Optional[List[str]] = None,
    ) -> Dict[str, float]:
        """
        Computes Accuracy, Macro Precision, Macro Recall, and Macro-F1.
        Zero-denominator behavior: returns 0.0 if empty.
        """
        if not y_true or not y_pred or len(y_true) != len(y_pred):
            return {
                "accuracy": 0.0,
                "macro_precision": 0.0,
                "macro_recall": 0.0,
                "macro_f1": 0.0,
            }

        total = len(y_true)
        if total == 0:
            return {
                "accuracy": 0.0,
                "macro_precision": 0.0,
                "macro_recall": 0.0,
                "macro_f1": 0.0,
            }

        correct = sum(1 for yt, yp in zip(y_true, y_pred) if yt == yp)
        acc = correct / float(total)

        target_classes = classes or sorted(list(set(y_true + y_pred)))
        if not target_classes:
            return {"accuracy": round(acc, 4), "macro_precision": 0.0, "macro_recall": 0.0, "macro_f1": 0.0}

        precisions = []
        recalls = []
        f1s = []
        per_class: Dict[str, float] = {}

        for c in target_classes:
            tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == c and yp == c)
            fp = sum(1 for yt, yp in zip(y_true, y_pred) if yt != c and yp == c)
            fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == c and yp != c)

            prec = tp / float(tp + fp) if (tp + fp) > 0 else 0.0
            rec = tp / float(tp + fn) if (tp + fn) > 0 else 0.0
            f1 = (2.0 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

            precisions.append(prec)
            recalls.append(rec)
            f1s.append(f1)
            per_class[c] = round(f1, 4)

        macro_prec = sum(precisions) / float(len(target_classes))
        macro_rec = sum(recalls) / float(len(target_classes))
        macro_f1 = sum(f1s) / float(len(target_classes))

        return {
            "accuracy": round(acc, 4),
            "macro_precision": round(macro_prec, 4),
            "macro_recall": round(macro_rec, 4),
            "macro_f1": round(macro_f1, 4),
            **{f"f1_{c}": per_class[c] for c in per_class},
        }

    @classmethod
    def compute_eligibility_metrics(
        cls,
        trial_true: List[str],
        trial_pred: List[str],
        crit_true: Optional[List[str]] = None,
        crit_pred: Optional[List[str]] = None,
    ) -> EligibilityMetrics:
        trial_classes = ["ELIGIBLE", "INELIGIBLE", "NEEDS_REVIEW"]
        t_res = cls.compute_classification_metrics(trial_true, trial_pred, trial_classes)

        crit_classes = ["PASS", "FAIL", "UNKNOWN"]
        c_acc = 0.0
        c_f1 = 0.0
        crit_count = 0
        if crit_true and crit_pred:
            crit_count = len(crit_true)
            c_res = cls.compute_classification_metrics(crit_true, crit_pred, crit_classes)
            c_acc = c_res.get("accuracy", 0.0)
            c_f1 = c_res.get("macro_f1", 0.0)

        per_class_f1 = {
            c: t_res.get(f"f1_{c}", 0.0) for c in trial_classes if f"f1_{c}" in t_res
        }

        return EligibilityMetrics(
            accuracy=t_res["accuracy"],
            macro_precision=t_res["macro_precision"],
            macro_recall=t_res["macro_recall"],
            macro_f1=t_res["macro_f1"],
            per_class_f1=per_class_f1,
            trial_count=len(trial_true),
            criterion_count=crit_count,
            criterion_accuracy=round(c_acc, 4),
            criterion_macro_f1=round(c_f1, 4),
        )

    # =========================================================================
    # 3. GROUNDING METRICS
    # =========================================================================

    @staticmethod
    def compute_grounding_metrics(
        total_claims: int,
        supported_claims: int,
        unsupported_claims: int,
        contradicted_claims: int,
        total_citations: int,
        valid_citations: int,
        evaluated_criteria: int,
        grounded_criteria: int,
    ) -> GroundingMetricsSummary:
        """
        Zero-denominator behavior:
        - If total_claims == 0: support rate = 1.0, unsupported = 0.0, contradiction = 0.0, hallucination = 0.0
        - If total_citations == 0: validity rate = 1.0
        - If evaluated_criteria == 0: coverage = 1.0
        """
        csr = (supported_claims / float(total_claims)) if total_claims > 0 else 1.0
        ucr = (unsupported_claims / float(total_claims)) if total_claims > 0 else 0.0
        cr = (contradicted_claims / float(total_claims)) if total_claims > 0 else 0.0
        cvr = (valid_citations / float(total_citations)) if total_citations > 0 else 1.0
        ec = (grounded_criteria / float(evaluated_criteria)) if evaluated_criteria > 0 else 1.0

        # Grounding score: weighted blend
        # 40% support + 30% citation validity + 30% coverage - penalties for unsupported/contradictions
        raw_score = 0.4 * csr + 0.3 * cvr + 0.3 * ec - 0.5 * cr - 0.3 * ucr
        grounding_score = max(0.0, min(1.0, raw_score))
        hallucination_rate = ucr + cr

        return GroundingMetricsSummary(
            claim_support_rate=round(csr, 4),
            unsupported_claim_rate=round(ucr, 4),
            contradiction_rate=round(cr, 4),
            citation_validity_rate=round(cvr, 4),
            evidence_coverage=round(ec, 4),
            grounding_score=round(grounding_score, 4),
            hallucination_rate=round(hallucination_rate, 4),
        )

    # =========================================================================
    # 4. UNCERTAINTY METRICS
    # =========================================================================

    @staticmethod
    def compute_uncertainty_metrics(
        total_evaluations: int,
        uncertain_evaluations: int,
        routed_to_review: int,
        unresolved_uncertainty_cases: int,
    ) -> UncertaintyMetricsSummary:
        """
        Zero-denominator behavior: if 0 evaluations, all rates are 0.0.
        """
        if total_evaluations == 0:
            return UncertaintyMetricsSummary()

        ur = uncertain_evaluations / float(total_evaluations)
        rr = routed_to_review / float(total_evaluations)
        uur = unresolved_uncertainty_cases / float(total_evaluations)

        return UncertaintyMetricsSummary(
            uncertainty_rate=round(ur, 4),
            review_routing_rate=round(rr, 4),
            unresolved_uncertainty_rate=round(uur, 4),
            total_evaluations=total_evaluations,
        )

    # =========================================================================
    # 5. EXPLAINABILITY METRICS
    # =========================================================================

    @staticmethod
    def compute_explainability_metrics(
        total_criteria: int,
        evidence_backed_criteria: int,
        total_decisions: int,
        traceable_decisions: int,
        traceable_criteria: int,
        total_evidence_nodes: int,
        valid_provenance_nodes: int,
        total_explanation_claims: int,
        supported_explanation_claims: int,
        total_contradictions: int,
        disclosed_contradictions: int,
        total_graphs: int,
        valid_graphs: int,
    ) -> ExplainabilityMetricsSummary:
        """
        Zero-denominator behaviors:
        - If 0 items of a type, return 1.0 (or 0.0 for unsupported rate).
        """
        ec = (evidence_backed_criteria / float(total_criteria)) if total_criteria > 0 else 1.0
        dtr = (traceable_decisions / float(total_decisions)) if total_decisions > 0 else 1.0
        ctr = (traceable_criteria / float(total_criteria)) if total_criteria > 0 else 1.0
        pvr = (valid_provenance_nodes / float(total_evidence_nodes)) if total_evidence_nodes > 0 else 1.0
        esr = (supported_explanation_claims / float(total_explanation_claims)) if total_explanation_claims > 0 else 1.0
        uecr = ((total_explanation_claims - supported_explanation_claims) / float(total_explanation_claims)) if total_explanation_claims > 0 else 0.0
        cdr = (disclosed_contradictions / float(total_contradictions)) if total_contradictions > 0 else 1.0
        gir = (valid_graphs / float(total_graphs)) if total_graphs > 0 else 1.0

        return ExplainabilityMetricsSummary(
            evidence_coverage=round(ec, 4),
            decision_traceability_rate=round(dtr, 4),
            criterion_traceability_rate=round(ctr, 4),
            provenance_validity_rate=round(pvr, 4),
            explanation_support_rate=round(esr, 4),
            unsupported_claim_rate=round(uecr, 4),
            contradiction_disclosure_rate=round(cdr, 4),
            graph_integrity_rate=round(gir, 4),
        )
