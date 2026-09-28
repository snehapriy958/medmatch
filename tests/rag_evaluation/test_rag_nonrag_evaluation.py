"""
Tests for RAG vs. Non-RAG Comparative Evaluation, Validation & Provenance.
Phase 7: RAG vs. Non-RAG Experimental Evaluation.
"""

import pytest
from pydantic import ValidationError

from scripts.eligibility_schema import (
    CriterionEvaluationRecord,
    CriterionEvaluationStatus,
    CriterionType,
    EvidenceCitation,
    TrialEligibilityEvaluation,
    TrialEligibilityStatus,
)
from scripts.nonrag_experiment import NonRAGExperimentRunner
from scripts.rag_experiment import RAGExperimentRunner
from scripts.run_phase7_experiment import Phase7ExperimentHarness
from scripts.validate_eligibility import EligibilityValidator


class TestComparativeEvaluation:
    """Verifies schema conformance, aggregation parity, and provenance preservation."""

    def setup_method(self):
        self.nonrag = NonRAGExperimentRunner()
        self.rag = RAGExperimentRunner()
        self.harness = Phase7ExperimentHarness(self.nonrag, self.rag)
        self.validator = EligibilityValidator()

    def test_outputs_conform_to_phase6_schema(self):
        """Test 5: Both E5 and E6 emit valid Phase 6 TrialEligibilityEvaluation models."""
        criteria = [{"id": "c1", "criteria_type": "INCLUSION", "description": "Age >= 18"}]
        demographics = {"age": 50}

        eval_nonrag = self.nonrag.evaluate_trial(
            trial_id="TRIAL-SCHEMA", criteria=criteria, patient_facts=[], demographics=demographics
        )
        eval_rag = self.rag.evaluate_trial(
            trial_id="TRIAL-SCHEMA", criteria=criteria, patient_facts=[], demographics=demographics
        )

        assert isinstance(eval_nonrag, TrialEligibilityEvaluation)
        assert isinstance(eval_rag, TrialEligibilityEvaluation)
        assert len(self.validator.validate_trial_evaluation(eval_nonrag)) == 0
        assert len(self.validator.validate_trial_evaluation(eval_rag)) == 0

    def test_deterministic_aggregation_is_identical_across_conditions(self):
        """Test 6: When criteria outcomes are identical, aggregation is mathematically identical."""
        # Condition 1: 1 FAIL -> INELIGIBLE for both
        crit_fail = [{"id": "c_fail", "criteria_type": "INCLUSION", "description": "Age >= 18"}]
        minor_demo = {"age": 15}

        res_nonrag = self.nonrag.evaluate_trial("TRIAL-AGG", crit_fail, [], demographics=minor_demo)
        res_rag = self.rag.evaluate_trial("TRIAL-AGG", crit_fail, [], demographics=minor_demo)

        assert res_nonrag.status == TrialEligibilityStatus.INELIGIBLE
        assert res_rag.status == TrialEligibilityStatus.INELIGIBLE
        assert res_nonrag.failed_count == res_rag.failed_count == 1

    def test_unsupported_pass_fails_validation(self):
        """Test 7: PASS without evidence is strictly rejected by schema validator."""
        with pytest.raises(ValidationError):
            CriterionEvaluationRecord(
                criterion_id="c_ungrounded",
                trial_id="TRIAL-UG",
                criterion_type=CriterionType.INCLUSION,
                criterion_text="Patient has cancer",
                status=CriterionEvaluationStatus.PASS,
                reasoning="Asserted without citation",
                evidence_citations=[],
                patient_fact_references=[],
            )

    def test_unsupported_fail_fails_validation(self):
        """Test 8: FAIL without evidence is strictly rejected by schema validator."""
        with pytest.raises(ValidationError):
            CriterionEvaluationRecord(
                criterion_id="c_ungrounded_fail",
                trial_id="TRIAL-UG",
                criterion_type=CriterionType.INCLUSION,
                criterion_text="Patient has cancer",
                status=CriterionEvaluationStatus.FAIL,
                reasoning="Asserted without citation",
                evidence_citations=[],
                patient_fact_references=[],
            )

    def test_provenance_preserved_for_rag(self):
        """Test 9: RAG evaluations preserve fact IDs, offsets, and source fields."""
        criteria = [{"id": "c1", "criteria_type": "INCLUSION", "description": "Metastatic melanoma"}]
        facts = [
            {
                "fact_id": "fact-mel-101",
                "concept": "metastatic melanoma",
                "assertion": "PRESENT",
                "snippet": "Patient with stage IV metastatic melanoma",
                "start_char": 15,
                "end_char": 57,
            }
        ]
        eval_rag = self.rag.evaluate_trial("TRIAL-PROV", criteria, facts)
        assert eval_rag.passed_count == 1
        record = eval_rag.criterion_evaluations[0]
        assert len(record.evidence_citations) == 1
        citation = record.evidence_citations[0]
        assert citation.fact_id == "fact-mel-101"
        assert citation.start_char == 15
        assert citation.end_char == 57
        assert "fact-mel-101" in record.patient_fact_references

    def test_experiment_execution_is_deterministic(self):
        """Test 13: Repeated executions yield identical output."""
        criteria = [{"id": "c1", "criteria_type": "INCLUSION", "description": "Age >= 18"}]
        demo = {"age": 45}

        run1 = self.harness.run_case_comparison("TRIAL-DET", criteria, [], demographics=demo)
        run2 = self.harness.run_case_comparison("TRIAL-DET", criteria, [], demographics=demo)

        assert run1["nonrag_status"] == run2["nonrag_status"]
        assert run1["rag_status"] == run2["rag_status"]
        assert run1["agreement"] == run2["agreement"]
