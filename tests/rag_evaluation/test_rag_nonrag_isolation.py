"""
Tests for RAG vs. Non-RAG Information Isolation & Anti-Leakage.
Phase 7: RAG vs. Non-RAG Experimental Evaluation.
"""

import pytest

from scripts.nonrag_experiment import InformationLeakageError, NonRAGExperimentRunner
from scripts.rag_experiment import RAGExperimentRunner
from scripts.run_phase7_experiment import Phase7ExperimentHarness


class TestInformationIsolation:
    """Verifies strict information boundaries and anti-leakage invariants."""

    def setup_method(self):
        self.nonrag_runner = NonRAGExperimentRunner()
        self.rag_runner = RAGExperimentRunner()
        self.harness = Phase7ExperimentHarness(self.nonrag_runner, self.rag_runner)

    def test_nonrag_rejects_retrieval_leakage(self):
        """Test 1 & 10: NON-RAG raises error if retrieval keys are present."""
        leaky_input = {
            "retrieved_evidence": {"passage": "This is a retrieved clinical trial passage."},
            "criteria": [{"id": "c1", "description": "Age >= 18"}],
        }
        with pytest.raises(InformationLeakageError) as exc:
            self.nonrag_runner.assert_no_retrieval_leakage(leaky_input)
        assert "Information leakage detected" in str(exc.value)

    def test_nonrag_rejects_retrieval_keys_inside_criterion(self):
        """Test 1 & 10: Criterion-level retrieval metadata in Non-RAG triggers error."""
        leaky_criteria = {
            "criteria": [
                {
                    "id": "c1",
                    "description": "Age >= 18",
                    "retrieval_score": 0.85,  # Forbidden in Non-RAG
                }
            ]
        }
        with pytest.raises(InformationLeakageError) as exc:
            self.nonrag_runner.assert_no_retrieval_leakage(leaky_criteria)
        assert "retrieval_score" in str(exc.value)

    def test_rag_receives_and_uses_retrieval_evidence(self):
        """Test 2: RAG receives retrieval-derived evidence."""
        criteria = [{"id": "c1", "description": "Confirmed non-small cell lung cancer"}]
        facts = [
            {
                "fact_id": "f1",
                "concept": "non-small cell lung cancer",
                "assertion": "PRESENT",
                "snippet": "Biopsy proven NSCLC",
            }
        ]
        retrieved_evidence = {
            "trial_summary": "Phase 3 clinical trial evaluating osimertinib in NSCLC.",
            "retrieval_method": "hybrid_rrf",
            "retrieval_score": 0.045,
        }
        eval_rag = self.rag_runner.evaluate_trial(
            trial_id="TRIAL-RAG-01",
            criteria=criteria,
            patient_facts=facts,
            retrieved_evidence=retrieved_evidence,
        )
        assert eval_rag.total_criteria_evaluated == 1
        assert eval_rag.passed_count == 1
        assert eval_rag.criterion_evaluations[0].status.value == "PASS"

    def test_both_conditions_use_identical_patient_facts_and_criteria(self):
        """Test 3 & 4: Harness supplies identical patient facts and criteria to both."""
        patient_facts = [
            {"fact_id": "f1", "concept": "adenocarcinoma", "assertion": "PRESENT"},
        ]
        criteria = [
            {"id": "c1", "criteria_type": "INCLUSION", "description": "Adenocarcinoma"}
        ]
        comparison = self.harness.run_case_comparison(
            trial_id="TRIAL-TEST-01",
            criteria=criteria,
            patient_facts=patient_facts,
            retrieved_evidence={"trial_summary": "Adenocarcinoma trial"},
        )
        # Verify both evaluated the exact same trial and criterion count
        assert comparison["trial_id"] == "TRIAL-TEST-01"
        assert comparison["nonrag_evaluation"].total_criteria_evaluated == 1
        assert comparison["rag_evaluation"].total_criteria_evaluated == 1
        assert comparison["nonrag_evaluation"].criterion_evaluations[0].criterion_id == "c1"
        assert comparison["rag_evaluation"].criterion_evaluations[0].criterion_id == "c1"
