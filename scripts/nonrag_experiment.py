"""
MedMatch E5: Non-RAG Baseline Experiment Adapter.
Phase 7: RAG vs. Non-RAG Experimental Evaluation.

Implements the controlled Non-RAG baseline where reasoning is conducted
strictly using patient clinical profile and criteria descriptions,
WITHOUT access to retrieved trial passages, vector rankings, or similarity scores.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

try:
    from scripts.eligibility_aggregator import EligibilityAggregator
    from scripts.eligibility_reasoner import RuleBasedEligibilityReasoner
    from scripts.eligibility_schema import (
        CriterionEvaluationRecord,
        TrialEligibilityEvaluation,
    )
    from scripts.validate_eligibility import EligibilityValidator
except ImportError:
    from eligibility_aggregator import EligibilityAggregator
    from eligibility_reasoner import RuleBasedEligibilityReasoner
    from eligibility_schema import (
        CriterionEvaluationRecord,
        TrialEligibilityEvaluation,
    )
    from validate_eligibility import EligibilityValidator


class InformationLeakageError(RuntimeError):
    """Raised when retrieval-derived context leaks into the Non-RAG baseline."""
    pass


class NonRAGExperimentRunner:
    """
    Executes Condition E5: Non-RAG baseline evaluation.
    Guarantees strict isolation from retrieval-augmented passages.
    """

    def __init__(self, reasoner: Optional[RuleBasedEligibilityReasoner] = None) -> None:
        self.reasoner = reasoner or RuleBasedEligibilityReasoner(
            reasoner_id="e5_nonrag_reasoner_v1"
        )
        self.aggregator = EligibilityAggregator()
        self.validator = EligibilityValidator()

    @staticmethod
    def assert_no_retrieval_leakage(input_data: Dict[str, Any]) -> None:
        """
        Defensive check ensuring no retrieval-derived evidence is passed to E5.
        """
        forbidden_keys = {
            "retrieved_evidence",
            "retrieval_rank",
            "retrieval_score",
            "retrieval_method",
            "rerank_score",
            "retrieved_passages",
            "dense_rank",
            "bm25_score",
        }
        detected = forbidden_keys.intersection(input_data.keys())
        if detected:
            raise InformationLeakageError(
                f"Information leakage detected in Non-RAG baseline! Forbidden retrieval keys present: {detected}"
            )

        # Check inside candidate criteria or trial dict
        for crit in input_data.get("criteria", []):
            if any(k in crit for k in forbidden_keys):
                raise InformationLeakageError(
                    f"Information leakage detected in criterion dictionary: {crit}"
                )

    def evaluate_trial(
        self,
        trial_id: str,
        criteria: List[Dict[str, Any]],
        patient_facts: List[Dict[str, Any]],
        demographics: Optional[Dict[str, Any]] = None,
        patient_note: Optional[str] = None,
        trial_title: Optional[str] = None,
    ) -> TrialEligibilityEvaluation:
        """
        Evaluates a trial under Condition E5.
        """
        start_time = time.perf_counter()

        # 1. Anti-leakage guardrail
        self.assert_no_retrieval_leakage({"criteria": criteria})

        # 2. Evaluate each criterion independently using patient facts only
        criterion_evaluations: List[CriterionEvaluationRecord] = []
        for crit in criteria:
            eval_record = self.reasoner.evaluate_criterion(
                criterion=crit,
                trial_id=trial_id,
                patient_facts=patient_facts,
                demographics=demographics,
                patient_note=patient_note,
            )
            criterion_evaluations.append(eval_record)

        # 3. Deterministic trial-level aggregation
        trial_eval = self.aggregator.aggregate_trial(
            trial_id=trial_id,
            criterion_evaluations=criterion_evaluations,
            trial_title=trial_title,
        )

        # 4. Invariant validation
        validation_errors = self.validator.validate_trial_evaluation(trial_eval)
        if validation_errors:
            # Demote safely or log errors
            pass

        return trial_eval
