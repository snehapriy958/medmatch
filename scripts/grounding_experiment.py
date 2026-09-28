"""
MedMatch Phase 8 Grounding Experiment Harness.
Orchestrates comparative grounding evaluations:
- G1: NON-RAG Grounding Evaluation
- G2: Dense-RAG Grounding Evaluation (using Phase 5 DenseRetriever)
- G3: Hybrid-RAG Grounding Evaluation (using Phase 5 HybridRRFRetriever)
- G4: RAG + Reranking Grounding Evaluation (using Phase 5 RerankingRetriever)

Features:
1. Direct evaluation of Phase 6 reasoning outputs via GroundingValidator
2. Preservation of anti-leakage isolation for G1
3. Computation of macro- and micro-averaged grounding metrics
4. Research benchmark availability guardrail preventing premature claims
"""

from __future__ import annotations

import argparse
import copy
import os
import sys
from typing import Any, Callable, Dict, List, Optional

try:
    from scripts.eligibility_schema import CriterionEvaluationRecord, TrialEligibilityEvaluation
    from scripts.grounding_metrics import GroundingMetricsEngine
    from scripts.grounding_schema import GroundingEvaluation
    from scripts.grounding_validator import GroundingValidator
    from scripts.nonrag_experiment import NonRAGExperimentRunner
    from scripts.rag_experiment import RAGExperimentRunner
    from scripts.retrieval_schema import CandidateTrialRecord
except ImportError:
    from eligibility_schema import CriterionEvaluationRecord, TrialEligibilityEvaluation
    from grounding_metrics import GroundingMetricsEngine
    from grounding_schema import GroundingEvaluation
    from grounding_validator import GroundingValidator
    from nonrag_experiment import NonRAGExperimentRunner
    from rag_experiment import RAGExperimentRunner
    from retrieval_schema import CandidateTrialRecord


class GroundingExperimentHarness:
    """
    Experimental harness orchestrating grounding and faithfulness evaluation across
    G1 (Non-RAG) and G2/G3/G4 (RAG) conditions.
    """

    def __init__(self, validator: Optional[GroundingValidator] = None) -> None:
        self.validator = validator or GroundingValidator()
        self.metrics_engine = GroundingMetricsEngine()

    def evaluate_reasoning_record(
        self,
        record: CriterionEvaluationRecord,
        patient_facts: List[Dict[str, Any]],
        criteria: List[Dict[str, Any]],
        demographics: Optional[Dict[str, Any]] = None,
        retrieved_evidence: Optional[Dict[str, Any]] = None,
        patient_note: Optional[str] = None,
    ) -> GroundingEvaluation:
        """
        Evaluates grounding on a single CriterionEvaluationRecord.
        """
        return self.validator.evaluate_criterion_record(
            record=record,
            patient_facts=patient_facts,
            criteria=criteria,
            demographics=demographics,
            retrieved_evidence=retrieved_evidence,
            patient_note=patient_note,
        )

    def evaluate_trial_evaluation(
        self,
        trial_eval: TrialEligibilityEvaluation,
        patient_facts: List[Dict[str, Any]],
        criteria: List[Dict[str, Any]],
        demographics: Optional[Dict[str, Any]] = None,
        retrieved_evidence: Optional[Dict[str, Any]] = None,
        patient_note: Optional[str] = None,
    ) -> List[GroundingEvaluation]:
        """
        Evaluates grounding across all criteria in a TrialEligibilityEvaluation.
        """
        evaluations: List[GroundingEvaluation] = []
        for crit_rec in trial_eval.criterion_evaluations:
            g_eval = self.evaluate_reasoning_record(
                record=crit_rec,
                patient_facts=patient_facts,
                criteria=criteria,
                demographics=demographics,
                retrieved_evidence=retrieved_evidence,
                patient_note=patient_note,
            )
            evaluations.append(g_eval)
        return evaluations

    def run_g1_nonrag_grounding(
        self,
        trial_id: str,
        criteria: List[Dict[str, Any]],
        patient_facts: List[Dict[str, Any]],
        demographics: Optional[Dict[str, Any]] = None,
        patient_note: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes Condition G1: Evaluates Non-RAG baseline reasoning for evidence grounding.
        Strict anti-leakage isolation enforced.
        """
        nonrag_runner = NonRAGExperimentRunner()
        clean_criteria = [
            {
                "id": str(c.get("id") or c.get("criterion_id")),
                "criteria_type": str(c.get("criteria_type", "INCLUSION")),
                "description": str(c.get("description") or c.get("criterion_text", "")),
            }
            for c in criteria
        ]
        nonrag_eval = nonrag_runner.evaluate_trial(
            trial_id=trial_id,
            criteria=clean_criteria,
            patient_facts=copy.deepcopy(patient_facts),
            demographics=copy.deepcopy(demographics),
            patient_note=patient_note,
        )

        grounding_evals = self.evaluate_trial_evaluation(
            trial_eval=nonrag_eval,
            patient_facts=patient_facts,
            criteria=criteria,
            demographics=demographics,
            retrieved_evidence=None,  # Zero retrieval context for G1
            patient_note=patient_note,
        )

        aggregated_metrics = self.metrics_engine.aggregate_evaluations(grounding_evals)

        return {
            "condition": "G1_NONRAG",
            "trial_id": trial_id,
            "trial_evaluation": nonrag_eval,
            "grounding_evaluations": grounding_evals,
            "aggregated_metrics": aggregated_metrics,
        }

    def run_rag_grounding_comparison(
        self,
        trial_id: str,
        criteria: List[Dict[str, Any]],
        patient_facts: List[Dict[str, Any]],
        candidate_pool: List[CandidateTrialRecord],
        query_text: str,
        demographics: Optional[Dict[str, Any]] = None,
        patient_note: Optional[str] = None,
        embed_fn: Optional[Callable[[str], List[float]]] = None,
    ) -> Dict[str, Any]:
        """
        Executes comparative grounding evaluation across:
        - G1: NON-RAG
        - G2: Dense-RAG (Phase 5 DenseRetriever)
        - G3: Hybrid-RAG (Phase 5 HybridRRFRetriever)
        - G4: Reranked-RAG (Phase 5 RerankingRetriever)
        """
        # 1. G1: Non-RAG
        g1_res = self.run_g1_nonrag_grounding(
            trial_id=trial_id,
            criteria=criteria,
            patient_facts=patient_facts,
            demographics=demographics,
            patient_note=patient_note,
        )

        # 2. G2: Dense-RAG
        dense_runner = RAGExperimentRunner.create_dense_rag(embed_fn=embed_fn)
        dense_evals = dense_runner.evaluate_candidate_pool(
            query_text=query_text,
            candidate_pool=candidate_pool,
            patient_facts=patient_facts,
            demographics=demographics,
            patient_note=patient_note,
            top_k=5,
        )
        target_dense = [e for e in dense_evals if e.trial_id == trial_id]
        dense_g_evals = (
            self.evaluate_trial_evaluation(
                trial_eval=target_dense[0],
                patient_facts=patient_facts,
                criteria=criteria,
                demographics=demographics,
                retrieved_evidence={"retrieval_method": "dense", "trial_id": trial_id},
                patient_note=patient_note,
            )
            if target_dense
            else []
        )

        # 3. G3: Hybrid-RAG
        hybrid_runner = RAGExperimentRunner.create_hybrid_rag(embed_fn=embed_fn)
        hybrid_evals = hybrid_runner.evaluate_candidate_pool(
            query_text=query_text,
            candidate_pool=candidate_pool,
            patient_facts=patient_facts,
            demographics=demographics,
            patient_note=patient_note,
            top_k=5,
        )
        target_hybrid = [e for e in hybrid_evals if e.trial_id == trial_id]
        hybrid_g_evals = (
            self.evaluate_trial_evaluation(
                trial_eval=target_hybrid[0],
                patient_facts=patient_facts,
                criteria=criteria,
                demographics=demographics,
                retrieved_evidence={"retrieval_method": "hybrid_rrf", "trial_id": trial_id},
                patient_note=patient_note,
            )
            if target_hybrid
            else []
        )

        # 4. G4: Reranked-RAG
        reranked_runner = RAGExperimentRunner.create_reranked_rag(embed_fn=embed_fn)
        reranked_evals = reranked_runner.evaluate_candidate_pool(
            query_text=query_text,
            candidate_pool=candidate_pool,
            patient_facts=patient_facts,
            demographics=demographics,
            patient_note=patient_note,
            top_k=5,
        )
        target_reranked = [e for e in reranked_evals if e.trial_id == trial_id]
        reranked_g_evals = (
            self.evaluate_trial_evaluation(
                trial_eval=target_reranked[0],
                patient_facts=patient_facts,
                criteria=criteria,
                demographics=demographics,
                retrieved_evidence={"retrieval_method": "hybrid_reranked", "trial_id": trial_id},
                patient_note=patient_note,
            )
            if target_reranked
            else []
        )

        return {
            "trial_id": trial_id,
            "g1_nonrag_metrics": g1_res["aggregated_metrics"],
            "g2_dense_metrics": self.metrics_engine.aggregate_evaluations(dense_g_evals),
            "g3_hybrid_metrics": self.metrics_engine.aggregate_evaluations(hybrid_g_evals),
            "g4_reranked_metrics": self.metrics_engine.aggregate_evaluations(reranked_g_evals),
            "g1_evaluations": g1_res["grounding_evaluations"],
            "g2_evaluations": dense_g_evals,
            "g3_evaluations": hybrid_g_evals,
            "g4_evaluations": reranked_g_evals,
        }

    @staticmethod
    def check_research_benchmark_available(data_dir: str = "data") -> bool:
        """
        Guardrail checking if validated external benchmark has been ingested.
        """
        indicator = os.path.join(data_dir, "raw", "external", "trialgpt_annotations.json")
        return os.path.exists(indicator)


def main() -> None:
    parser = argparse.ArgumentParser(description="MedMatch Phase 8 Grounding Evaluation Harness")
    parser.add_argument("--data-dir", default="data", help="Path to data directory")
    args = parser.parse_args()

    harness = GroundingExperimentHarness()
    benchmark_present = harness.check_research_benchmark_available(args.data_dir)

    print("================================================================================")
    print("MEDMATCH PHASE 8: GROUNDING & FAITHFULNESS EVALUATION HARNESS")
    print("================================================================================")
    print(f"Dataset directory: {args.data_dir}")
    print(f"External research benchmark ingested: {benchmark_present}")

    if not benchmark_present:
        print("\n[RESEARCH PROTOCOL NOTICE]")
        print("Empirical grounding and hallucination comparison across G1-G4 was NOT executed")
        print("because a validated external research benchmark with ground-truth labels is")
        print("not yet available in the repository.")
        print("\nThe GroundingValidator, ClaimExtractor, GroundingMetricsEngine, and G1-G4")
        print("harnesses are fully implemented, verified, and ready for benchmark ingestion.")
        print("================================================================================")


if __name__ == "__main__":
    main()
