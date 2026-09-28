"""
Tests for Deterministic Eligibility Validator.
Phase 6: Eligibility Reasoning.
"""

from scripts.validate_eligibility import EligibilityValidator
from scripts.eligibility_schema import (
    CriterionEvaluationRecord,
    CriterionEvaluationStatus,
    CriterionType,
    EvidenceCitation,
    TrialEligibilityEvaluation,
    TrialEligibilityStatus,
)


class TestEligibilityValidator:
    """Verifies invariant checking across trial evaluations."""

    def test_valid_trial_evaluation_passes(self):
        eval_record = CriterionEvaluationRecord(
            criterion_id="c1",
            trial_id="TRIAL-1",
            criterion_type=CriterionType.INCLUSION,
            criterion_text="Patient age >= 18",
            status=CriterionEvaluationStatus.PASS,
            reasoning="Patient is 45.",
            evidence_citations=[EvidenceCitation(text_snippet="Age: 45", source_field="demographics")],
        )
        trial_eval = TrialEligibilityEvaluation(
            trial_id="TRIAL-1",
            status=TrialEligibilityStatus.ELIGIBLE,
            criterion_evaluations=[eval_record],
            total_criteria_evaluated=1,
            passed_count=1,
            failed_count=0,
            unknown_count=0,
            passed_criterion_ids=["c1"],
        )
        errors = EligibilityValidator.validate_trial_evaluation(trial_eval)
        assert len(errors) == 0

    def test_aggregation_invariant_violation_caught(self):
        # Criterion is FAIL, but trial status set to ELIGIBLE
        eval_record = CriterionEvaluationRecord(
            criterion_id="c1",
            trial_id="TRIAL-1",
            criterion_type=CriterionType.INCLUSION,
            criterion_text="No active infection",
            status=CriterionEvaluationStatus.FAIL,
            reasoning="Active sepsis documented.",
            evidence_citations=[EvidenceCitation(text_snippet="Active sepsis", source_field="notes")],
        )
        invalid_trial_eval = TrialEligibilityEvaluation(
            trial_id="TRIAL-1",
            status=TrialEligibilityStatus.ELIGIBLE,  # Invariant violation!
            criterion_evaluations=[eval_record],
            total_criteria_evaluated=1,
            passed_count=0,
            failed_count=1,
            unknown_count=0,
            failed_criterion_ids=["c1"],
        )
        errors = EligibilityValidator.validate_trial_evaluation(invalid_trial_eval)
        assert len(errors) == 1
        assert "Aggregation invariant violation" in errors[0]

    def test_count_mismatch_caught(self):
        eval_record = CriterionEvaluationRecord(
            criterion_id="c1",
            trial_id="TRIAL-1",
            criterion_type=CriterionType.INCLUSION,
            criterion_text="Age >= 18",
            status=CriterionEvaluationStatus.PASS,
            reasoning="Age 50.",
            evidence_citations=[EvidenceCitation(text_snippet="Age: 50", source_field="demographics")],
        )
        trial_eval = TrialEligibilityEvaluation(
            trial_id="TRIAL-1",
            status=TrialEligibilityStatus.ELIGIBLE,
            criterion_evaluations=[eval_record],
            total_criteria_evaluated=1,
            passed_count=5,  # Mismatch!
            failed_count=0,
            unknown_count=0,
            passed_criterion_ids=["c1"],
        )
        errors = EligibilityValidator.validate_trial_evaluation(trial_eval)
        assert any("Count mismatch" in err for err in errors)

    def test_duplicate_criterion_id_in_trial_caught(self):
        eval1 = CriterionEvaluationRecord(
            criterion_id="c1",
            trial_id="TRIAL-1",
            criterion_type=CriterionType.INCLUSION,
            criterion_text="Criterion 1",
            status=CriterionEvaluationStatus.PASS,
            reasoning="Satisfied.",
            evidence_citations=[EvidenceCitation(text_snippet="Snippet 1", source_field="notes")],
        )
        eval2 = CriterionEvaluationRecord(
            criterion_id="c1",  # Duplicate!
            trial_id="TRIAL-1",
            criterion_type=CriterionType.INCLUSION,
            criterion_text="Criterion 1 duplicate",
            status=CriterionEvaluationStatus.PASS,
            reasoning="Satisfied duplicate.",
            evidence_citations=[EvidenceCitation(text_snippet="Snippet 2", source_field="notes")],
        )
        trial_eval = TrialEligibilityEvaluation(
            trial_id="TRIAL-1",
            status=TrialEligibilityStatus.ELIGIBLE,
            criterion_evaluations=[eval1, eval2],
            total_criteria_evaluated=2,
            passed_count=2,
            failed_count=0,
            unknown_count=0,
            passed_criterion_ids=["c1"],
        )
        errors = EligibilityValidator.validate_trial_evaluation(trial_eval)
        assert any("Duplicate criterion_id" in err for err in errors)
