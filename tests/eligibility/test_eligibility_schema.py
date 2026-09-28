"""
Tests for Canonical Eligibility Schemas & Data Contracts.
Phase 6: Eligibility Reasoning.
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
    EligibilityReasoningRequest,
    EligibilityReasoningResponse,
)


class TestEligibilitySchema:
    """Validates schema validation and invariants."""

    def test_criterion_evaluation_valid_pass(self):
        citation = EvidenceCitation(
            fact_id="fact-001",
            text_snippet="histologically confirmed adenocarcinoma",
            source_field="patient_facts",
            start_char=10,
            end_char=49,
            assertion_type="PRESENT",
        )
        record = CriterionEvaluationRecord(
            criterion_id="crit-101",
            trial_id="NCT01234567",
            criterion_type=CriterionType.INCLUSION,
            criterion_text="Histologically confirmed adenocarcinoma",
            status=CriterionEvaluationStatus.PASS,
            reasoning="Patient adenocarcinoma confirmed by histology.",
            evidence_citations=[citation],
            patient_fact_references=["fact-001"],
        )
        assert record.status == CriterionEvaluationStatus.PASS
        assert len(record.evidence_citations) == 1
        assert record.evidence_citations[0].fact_id == "fact-001"

    def test_pass_without_evidence_raises_validation_error(self):
        with pytest.raises(ValidationError) as exc_info:
            CriterionEvaluationRecord(
                criterion_id="crit-102",
                trial_id="NCT01234567",
                criterion_type=CriterionType.INCLUSION,
                criterion_text="Histologically confirmed adenocarcinoma",
                status=CriterionEvaluationStatus.PASS,
                reasoning="Assertion without evidence.",
                evidence_citations=[],
                patient_fact_references=[],
            )
        assert "without supporting evidence" in str(exc_info.value)

    def test_fail_without_evidence_raises_validation_error(self):
        with pytest.raises(ValidationError) as exc_info:
            CriterionEvaluationRecord(
                criterion_id="crit-103",
                trial_id="NCT01234567",
                criterion_type=CriterionType.INCLUSION,
                criterion_text="Age >= 18",
                status=CriterionEvaluationStatus.FAIL,
                reasoning="Assertion without evidence.",
                evidence_citations=[],
                patient_fact_references=[],
            )
        assert "without supporting evidence" in str(exc_info.value)

    def test_unknown_allowed_without_evidence_citations(self):
        record = CriterionEvaluationRecord(
            criterion_id="crit-104",
            trial_id="NCT01234567",
            criterion_type=CriterionType.INCLUSION,
            criterion_text="Prior treatment with EGFR TKI",
            status=CriterionEvaluationStatus.UNKNOWN,
            reasoning="Concept not documented in patient medical records.",
            uncertainty_notes="Missing treatment history.",
            evidence_citations=[],
            patient_fact_references=[],
        )
        assert record.status == CriterionEvaluationStatus.UNKNOWN
        assert len(record.evidence_citations) == 0

    def test_invalid_status_enum_rejected(self):
        with pytest.raises(ValidationError):
            CriterionEvaluationRecord(
                criterion_id="crit-105",
                trial_id="NCT01234567",
                criterion_type=CriterionType.INCLUSION,
                criterion_text="Some criterion",
                status="MAYBE",  # Invalid
                reasoning="Invalid status test",
            )

    def test_trial_eligibility_evaluation_serialization(self):
        eval_record = CriterionEvaluationRecord(
            criterion_id="crit-101",
            trial_id="NCT01234567",
            criterion_type=CriterionType.INCLUSION,
            criterion_text="Adult patient age >= 18",
            status=CriterionEvaluationStatus.PASS,
            reasoning="Patient age is 55.",
            evidence_citations=[EvidenceCitation(text_snippet="Age: 55", source_field="demographics")],
        )
        trial_eval = TrialEligibilityEvaluation(
            trial_id="NCT01234567",
            trial_title="Phase 2 Lung Cancer Study",
            status=TrialEligibilityStatus.ELIGIBLE,
            criterion_evaluations=[eval_record],
            total_criteria_evaluated=1,
            passed_count=1,
            failed_count=0,
            unknown_count=0,
            passed_criterion_ids=["crit-101"],
            clinical_summary="Eligible for trial.",
        )
        json_data = trial_eval.model_dump_json()
        restored = TrialEligibilityEvaluation.model_validate_json(json_data)
        assert restored.trial_id == "NCT01234567"
        assert restored.status == TrialEligibilityStatus.ELIGIBLE
        assert restored.passed_count == 1
