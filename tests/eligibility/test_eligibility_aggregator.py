"""
Tests for Deterministic Eligibility Aggregator.
Phase 6: Eligibility Reasoning.
"""

import pytest

from scripts.eligibility_aggregator import EligibilityAggregator
from scripts.eligibility_schema import (
    CriterionEvaluationRecord,
    CriterionEvaluationStatus,
    CriterionType,
    EvidenceCitation,
    TrialEligibilityStatus,
)


def _make_eval(
    cid: str,
    status: CriterionEvaluationStatus,
    trial_id: str = "TRIAL-001",
) -> CriterionEvaluationRecord:
    citations = []
    if status in (CriterionEvaluationStatus.PASS, CriterionEvaluationStatus.FAIL):
        citations.append(EvidenceCitation(text_snippet="Test evidence", source_field="patient_facts"))
    return CriterionEvaluationRecord(
        criterion_id=cid,
        trial_id=trial_id,
        criterion_type=CriterionType.INCLUSION,
        criterion_text=f"Criterion text for {cid}",
        status=status,
        reasoning=f"Reasoning for {cid}",
        evidence_citations=citations,
        uncertainty_notes="Missing info" if status == CriterionEvaluationStatus.UNKNOWN else None,
    )


class TestEligibilityAggregator:
    """Verifies deterministic aggregation rules and edge cases."""

    def test_all_pass_yields_eligible(self):
        evals = [
            _make_eval("c1", CriterionEvaluationStatus.PASS),
            _make_eval("c2", CriterionEvaluationStatus.PASS),
            _make_eval("c3", CriterionEvaluationStatus.PASS),
        ]
        result = EligibilityAggregator.aggregate_trial("TRIAL-001", evals)
        assert result.status == TrialEligibilityStatus.ELIGIBLE
        assert result.passed_count == 3
        assert result.failed_count == 0
        assert result.unknown_count == 0
        assert len(result.passed_criterion_ids) == 3

    def test_one_fail_yields_ineligible(self):
        evals = [
            _make_eval("c1", CriterionEvaluationStatus.PASS),
            _make_eval("c2", CriterionEvaluationStatus.FAIL),
            _make_eval("c3", CriterionEvaluationStatus.PASS),
        ]
        result = EligibilityAggregator.aggregate_trial("TRIAL-001", evals)
        assert result.status == TrialEligibilityStatus.INELIGIBLE
        assert result.failed_count == 1
        assert "c2" in result.failed_criterion_ids

    def test_multiple_fail_yields_ineligible(self):
        evals = [
            _make_eval("c1", CriterionEvaluationStatus.FAIL),
            _make_eval("c2", CriterionEvaluationStatus.FAIL),
            _make_eval("c3", CriterionEvaluationStatus.UNKNOWN),
        ]
        result = EligibilityAggregator.aggregate_trial("TRIAL-001", evals)
        assert result.status == TrialEligibilityStatus.INELIGIBLE
        assert result.failed_count == 2
        assert result.unknown_count == 1

    def test_pass_and_unknown_yields_needs_review(self):
        evals = [
            _make_eval("c1", CriterionEvaluationStatus.PASS),
            _make_eval("c2", CriterionEvaluationStatus.UNKNOWN),
            _make_eval("c3", CriterionEvaluationStatus.PASS),
        ]
        result = EligibilityAggregator.aggregate_trial("TRIAL-001", evals)
        assert result.status == TrialEligibilityStatus.NEEDS_REVIEW
        assert result.passed_count == 2
        assert result.unknown_count == 1
        assert "c2" in result.unknown_criterion_ids

    def test_unknown_only_yields_needs_review(self):
        evals = [
            _make_eval("c1", CriterionEvaluationStatus.UNKNOWN),
            _make_eval("c2", CriterionEvaluationStatus.UNKNOWN),
        ]
        result = EligibilityAggregator.aggregate_trial("TRIAL-001", evals)
        assert result.status == TrialEligibilityStatus.NEEDS_REVIEW
        assert result.passed_count == 0
        assert result.unknown_count == 2

    def test_empty_criteria_yields_needs_review(self):
        result = EligibilityAggregator.aggregate_trial("TRIAL-001", [])
        assert result.status == TrialEligibilityStatus.NEEDS_REVIEW
        assert result.total_criteria_evaluated == 0
        assert "Zero criteria evaluated" in result.clinical_summary

    def test_duplicate_criterion_id_raises_value_error(self):
        evals = [
            _make_eval("c1", CriterionEvaluationStatus.PASS),
            _make_eval("c1", CriterionEvaluationStatus.PASS),
        ]
        with pytest.raises(ValueError) as exc:
            EligibilityAggregator.aggregate_trial("TRIAL-001", evals, allow_duplicates=False)
        assert "Duplicate criterion_id 'c1'" in str(exc.value)

    def test_aggregate_batch_deterministic_ordering(self):
        batch = {
            "TRIAL-Z": [_make_eval("c1", CriterionEvaluationStatus.PASS, trial_id="TRIAL-Z")],
            "TRIAL-A": [_make_eval("c2", CriterionEvaluationStatus.FAIL, trial_id="TRIAL-A")],
        }
        results = EligibilityAggregator.aggregate_batch(batch)
        assert len(results) == 2
        # Deterministic sorting by trial_id ASC
        assert results[0].trial_id == "TRIAL-A"
        assert results[0].status == TrialEligibilityStatus.INELIGIBLE
        assert results[1].trial_id == "TRIAL-Z"
        assert results[1].status == TrialEligibilityStatus.ELIGIBLE
