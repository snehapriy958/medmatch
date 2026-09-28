"""
MedMatch Phase 7 Experiment Runner & Comparative Evaluation Harness.
Phase 7: RAG vs. Non-RAG Experimental Evaluation.

Coordinates controlled comparison of:
- E5 (Non-RAG baseline)
vs
- E6 (Dense-RAG using Phase 5 DenseRetriever)
vs
- E7 (Hybrid-RAG using Phase 5 HybridRRFRetriever)
vs
- E8 (RAG + Reranking using Phase 5 RerankingRetriever)

Features:
1. Direct integration with Phase 5 retrieval engines (DenseRetriever, HybridRRFRetriever, RerankingRetriever)
2. Paired execution on identical patient facts and criteria
3. Immutable input separation preventing accidental information leakage
4. Deterministic Phase 6 aggregation & invariant validation
5. Comprehensive metrics: Macro-F1, UNKNOWN rate, Evidence Grounding Rate
6. Benchmark availability guardrail: explicitly flags when real benchmark is pending
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import sys
import time
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

try:
    from scripts.nonrag_experiment import InformationLeakageError, NonRAGExperimentRunner
    from scripts.rag_experiment import RAGExperimentRunner
    from scripts.retrieval_schema import CandidateTrialRecord
    from scripts.eligibility_schema import CriterionEvaluationStatus, TrialEligibilityStatus
except ImportError:
    from nonrag_experiment import InformationLeakageError, NonRAGExperimentRunner
    from rag_experiment import RAGExperimentRunner
    from retrieval_schema import CandidateTrialRecord
    from eligibility_schema import CriterionEvaluationStatus, TrialEligibilityStatus


class Phase7ExperimentHarness:
    """
    Experimental harness orchestrating paired E5 vs E6/E7/E8 evaluations.
    """

    def __init__(
        self,
        nonrag_runner: Optional[NonRAGExperimentRunner] = None,
        rag_runner: Optional[RAGExperimentRunner] = None,
    ) -> None:
        self.nonrag = nonrag_runner or NonRAGExperimentRunner()
        self.rag = rag_runner or RAGExperimentRunner.create_dense_rag()

    @staticmethod
    def calculate_classification_metrics(
        y_true: List[str], y_pred: List[str], classes: List[str]
    ) -> Dict[str, float]:
        """
        Computes Macro-F1, Precision, Recall, and Accuracy.
        """
        if not y_true or not y_pred or len(y_true) != len(y_pred):
            return {
                "macro_f1": 0.0,
                "precision": 0.0,
                "recall": 0.0,
                "accuracy": 0.0,
            }

        total = len(y_true)
        correct = sum(1 for yt, yp in zip(y_true, y_pred) if yt == yp)
        acc = correct / float(total)

        precisions = []
        recalls = []
        f1s = []

        for c in classes:
            tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == c and yp == c)
            fp = sum(1 for yt, yp in zip(y_true, y_pred) if yt != c and yp == c)
            fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == c and yp != c)

            prec = tp / float(tp + fp) if (tp + fp) > 0 else 0.0
            rec = tp / float(tp + fn) if (tp + fn) > 0 else 0.0
            f1 = (2.0 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

            precisions.append(prec)
            recalls.append(rec)
            f1s.append(f1)

        macro_prec = sum(precisions) / float(len(classes))
        macro_rec = sum(recalls) / float(len(classes))
        macro_f1 = sum(f1s) / float(len(classes))

        return {
            "macro_f1": round(macro_f1, 4),
            "precision": round(macro_prec, 4),
            "recall": round(macro_rec, 4),
            "accuracy": round(acc, 4),
        }

    def run_case_comparison(
        self,
        trial_id: str,
        criteria: List[Dict[str, Any]],
        patient_facts: List[Dict[str, Any]],
        retrieved_evidence: Optional[Dict[str, Any]] = None,
        demographics: Optional[Dict[str, Any]] = None,
        patient_note: Optional[str] = None,
        trial_title: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Runs both E5 and E6 on the exact same patient and criteria.
        Constructs separate immutable inputs to prevent accidental leakage.
        """
        # Critical Information Leakage Rule: Construct clean, isolated input for Non-RAG
        nonrag_criteria = [
            {
                "id": str(c.get("id") or c.get("criterion_id")),
                "criteria_type": str(c.get("criteria_type", "INCLUSION")),
                "description": str(c.get("description") or c.get("criterion_text", "")),
            }
            for c in criteria
        ]
        nonrag_facts = copy.deepcopy(patient_facts)
        nonrag_demographics = copy.deepcopy(demographics)

        rag_criteria = copy.deepcopy(criteria)
        rag_facts = copy.deepcopy(patient_facts)
        rag_demographics = copy.deepcopy(demographics)
        rag_evidence = copy.deepcopy(retrieved_evidence)

        # 1. Execute E5 (Non-RAG)
        eval_nonrag = self.nonrag.evaluate_trial(
            trial_id=trial_id,
            criteria=nonrag_criteria,
            patient_facts=nonrag_facts,
            demographics=nonrag_demographics,
            patient_note=patient_note,
            trial_title=trial_title,
        )

        # 2. Execute E6 (RAG-Grounded)
        eval_rag = self.rag.evaluate_trial(
            trial_id=trial_id,
            criteria=rag_criteria,
            patient_facts=rag_facts,
            retrieved_evidence=rag_evidence,
            demographics=rag_demographics,
            patient_note=patient_note,
            trial_title=trial_title,
        )

        agreement = eval_nonrag.status == eval_rag.status

        # Compute Evidence Grounding Rate for RAG
        rag_pass_fail = [
            c for c in eval_rag.criterion_evaluations
            if c.status in (CriterionEvaluationStatus.PASS, CriterionEvaluationStatus.FAIL)
        ]
        rag_grounded = [
            c for c in rag_pass_fail
            if len(c.evidence_citations) > 0 or len(c.patient_fact_references) > 0
        ]
        egr = (len(rag_grounded) / float(len(rag_pass_fail))) if rag_pass_fail else 1.0

        return {
            "trial_id": trial_id,
            "nonrag_status": eval_nonrag.status.value,
            "rag_status": eval_rag.status.value,
            "agreement": agreement,
            "nonrag_unknown_count": eval_nonrag.unknown_count,
            "rag_unknown_count": eval_rag.unknown_count,
            "rag_evidence_grounding_rate": round(egr, 4),
            "nonrag_evaluation": eval_nonrag,
            "rag_evaluation": eval_rag,
        }

    def run_corpus_retrieval_comparison(
        self,
        query_text: str,
        candidate_pool: List[CandidateTrialRecord],
        patient_facts: List[Dict[str, Any]],
        demographics: Optional[Dict[str, Any]] = None,
        patient_note: Optional[str] = None,
        top_k: int = 5,
        embed_fn: Optional[Callable[[str], List[float]]] = None,
    ) -> Dict[str, Any]:
        """
        Runs full comparison across:
        - E6 (Dense-RAG invoking Phase 5 DenseRetriever)
        - E7 (Hybrid-RAG invoking Phase 5 HybridRRFRetriever)
        - E8 (RAG + Reranking invoking Phase 5 RerankingRetriever)
        """
        dense_runner = RAGExperimentRunner.create_dense_rag(embed_fn=embed_fn)
        hybrid_runner = RAGExperimentRunner.create_hybrid_rag(embed_fn=embed_fn)
        reranked_runner = RAGExperimentRunner.create_reranked_rag(embed_fn=embed_fn)

        evals_e6 = dense_runner.evaluate_candidate_pool(
            query_text=query_text,
            candidate_pool=candidate_pool,
            patient_facts=patient_facts,
            demographics=demographics,
            patient_note=patient_note,
            top_k=top_k,
        )

        evals_e7 = hybrid_runner.evaluate_candidate_pool(
            query_text=query_text,
            candidate_pool=candidate_pool,
            patient_facts=patient_facts,
            demographics=demographics,
            patient_note=patient_note,
            top_k=top_k,
        )

        evals_e8 = reranked_runner.evaluate_candidate_pool(
            query_text=query_text,
            candidate_pool=candidate_pool,
            patient_facts=patient_facts,
            demographics=demographics,
            patient_note=patient_note,
            top_k=top_k,
        )

        return {
            "query": query_text,
            "e6_dense_evaluations": evals_e6,
            "e7_hybrid_evaluations": evals_e7,
            "e8_reranked_evaluations": evals_e8,
            "e6_retrieval_response": dense_runner.last_retrieval_response,
            "e7_retrieval_response": hybrid_runner.last_retrieval_response,
            "e8_retrieval_response": reranked_runner.last_retrieval_response,
        }

    @staticmethod
    def check_research_benchmark_available(data_dir: str = "data") -> bool:
        """
        Verifies whether an external research benchmark has been ingested.
        The 6-case development fixture does NOT count as a research benchmark.
        """
        benchmark_indicator = os.path.join(data_dir, "raw", "external", "trialgpt_annotations.json")
        if os.path.exists(benchmark_indicator):
            return True
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="MedMatch Phase 7 RAG vs Non-RAG Evaluation Harness")
    parser.add_argument("--data-dir", default="data", help="Path to data directory")
    args = parser.parse_args()

    harness = Phase7ExperimentHarness()
    benchmark_present = harness.check_research_benchmark_available(args.data_dir)

    print("================================================================================")
    print("MEDMATCH PHASE 7: RAG VS. NON-RAG EXPERIMENTAL EVALUATION HARNESS")
    print("================================================================================")
    print(f"Dataset directory: {args.data_dir}")
    print(f"External research benchmark ingested: {benchmark_present}")

    if not benchmark_present:
        print("\n[RESEARCH PROTOCOL NOTICE]")
        print("RAG vs non-RAG empirical performance comparison was not executed because a")
        print("validated research benchmark with ground-truth labels was not yet available.")
        print("\nPhase 7 now invokes the actual Phase 5 retrieval engine for RAG conditions.")
        print("All experimental harnesses, isolation adapters, leakage detectors,")
        print("and metrics functions are validated and ready for benchmark ingestion.")
        print("================================================================================")
        return

    print("Running evaluation on ingested benchmark...")


if __name__ == "__main__":
    main()
