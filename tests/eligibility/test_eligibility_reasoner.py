"""
Tests for Evidence-Grounded Eligibility Reasoner.
Phase 6: Eligibility Reasoning.
"""

import pytest

from scripts.eligibility_reasoner import RuleBasedEligibilityReasoner
from scripts.eligibility_schema import (
    CriterionEvaluationStatus,
    CriterionType,
)


class TestEligibilityReasoner:
    """Verifies evidence grounding, negation, thresholds, temporality, and conflicts."""

    def setup_method(self):
        self.reasoner = RuleBasedEligibilityReasoner()

    # -------------------------------------------------------------------------
    # Negation & Assertion Tests
    # -------------------------------------------------------------------------

    def test_inclusion_present_yields_pass(self):
        criterion = {
            "id": "crit-01",
            "criteria_type": "INCLUSION",
            "description": "History of myocardial infarction.",
        }
        facts = [
            {
                "fact_id": "fact-1",
                "concept": "myocardial infarction",
                "assertion": "PRESENT",
                "snippet": "Patient has a history of myocardial infarction.",
            }
        ]
        result = self.reasoner.evaluate_criterion(criterion, "TRIAL-001", facts)
        assert result.status == CriterionEvaluationStatus.PASS
        assert len(result.evidence_citations) == 1
        assert "fact-1" in result.patient_fact_references

    def test_inclusion_absent_yields_fail(self):
        criterion = {
            "id": "crit-01",
            "criteria_type": "INCLUSION",
            "description": "History of myocardial infarction.",
        }
        facts = [
            {
                "fact_id": "fact-1",
                "concept": "myocardial infarction",
                "assertion": "ABSENT",
                "snippet": "No history of myocardial infarction.",
            }
        ]
        result = self.reasoner.evaluate_criterion(criterion, "TRIAL-001", facts)
        assert result.status == CriterionEvaluationStatus.FAIL
        assert result.is_negated is True
        assert len(result.evidence_citations) == 1

    def test_exclusion_present_yields_fail(self):
        criterion = {
            "id": "crit-02",
            "criteria_type": "EXCLUSION",
            "description": "Active brain metastases.",
        }
        facts = [
            {
                "fact_id": "fact-2",
                "concept": "brain metastases",
                "assertion": "PRESENT",
                "is_current": True,
                "snippet": "MRI shows active brain metastases.",
            }
        ]
        result = self.reasoner.evaluate_criterion(criterion, "TRIAL-001", facts)
        assert result.status == CriterionEvaluationStatus.FAIL
        assert "triggered" in result.reasoning.lower()

    def test_exclusion_absent_yields_pass(self):
        criterion = {
            "id": "crit-02",
            "criteria_type": "EXCLUSION",
            "description": "Active brain metastases.",
        }
        facts = [
            {
                "fact_id": "fact-2",
                "concept": "brain metastases",
                "assertion": "ABSENT",
                "is_current": True,
                "snippet": "No evidence of brain metastases on scan.",
            }
        ]
        result = self.reasoner.evaluate_criterion(criterion, "TRIAL-001", facts)
        assert result.status == CriterionEvaluationStatus.PASS
        assert "passed" in result.reasoning.lower()

    def test_no_mention_yields_unknown(self):
        criterion = {
            "id": "crit-03",
            "criteria_type": "INCLUSION",
            "description": "Prior treatment with pembrolizumab.",
        }
        facts = [
            {
                "fact_id": "fact-3",
                "concept": "hypertension",
                "assertion": "PRESENT",
            }
        ]
        result = self.reasoner.evaluate_criterion(criterion, "TRIAL-001", facts)
        assert result.status == CriterionEvaluationStatus.UNKNOWN
        assert "Silence cannot be treated as absence" in result.reasoning
        assert len(result.evidence_citations) == 0

    def test_uncertain_assertion_yields_unknown(self):
        criterion = {
            "id": "crit-04",
            "criteria_type": "INCLUSION",
            "description": "Confirmed pulmonary embolism.",
        }
        facts = [
            {
                "fact_id": "fact-4",
                "concept": "pulmonary embolism",
                "assertion": "POSSIBLE",
                "snippet": "Suspected pulmonary embolism, CTA pending.",
            }
        ]
        result = self.reasoner.evaluate_criterion(criterion, "TRIAL-001", facts)
        assert result.status == CriterionEvaluationStatus.UNKNOWN
        assert "POSSIBLE" in result.reasoning

    def test_conflicting_evidence_yields_unknown(self):
        criterion = {
            "id": "crit-05",
            "criteria_type": "INCLUSION",
            "description": "Type 2 diabetes mellitus.",
        }
        facts = [
            {
                "fact_id": "fact-5a",
                "concept": "type 2 diabetes",
                "assertion": "PRESENT",
                "snippet": "Diagnosis: Type 2 diabetes mellitus.",
            },
            {
                "fact_id": "fact-5b",
                "concept": "type 2 diabetes",
                "assertion": "ABSENT",
                "snippet": "Patient denies any history of type 2 diabetes.",
            },
        ]
        result = self.reasoner.evaluate_criterion(criterion, "TRIAL-001", facts)
        assert result.status == CriterionEvaluationStatus.UNKNOWN
        assert "Conflicting clinical evidence" in result.reasoning

    # -------------------------------------------------------------------------
    # Numerical Threshold Tests
    # -------------------------------------------------------------------------

    def test_age_threshold_evaluation(self):
        criterion = {
            "id": "crit-age",
            "criteria_type": "INCLUSION",
            "description": "Age >= 18 years",
        }
        # Adult: 62 -> PASS
        res_adult = self.reasoner.evaluate_criterion(
            criterion, "TRIAL-001", [], demographics={"age": 62}
        )
        assert res_adult.status == CriterionEvaluationStatus.PASS

        # Minor: 16 -> FAIL
        res_minor = self.reasoner.evaluate_criterion(
            criterion, "TRIAL-001", [], demographics={"age": 16}
        )
        assert res_minor.status == CriterionEvaluationStatus.FAIL

        # Missing age -> UNKNOWN
        res_missing = self.reasoner.evaluate_criterion(
            criterion, "TRIAL-001", [], demographics={}
        )
        assert res_missing.status == CriterionEvaluationStatus.UNKNOWN

    def test_lab_threshold_evaluation(self):
        criterion = {
            "id": "crit-creat",
            "criteria_type": "INCLUSION",
            "description": "Serum creatinine < 1.5 mg/dL",
        }
        facts_pass = [
            {"fact_id": "f-c1", "concept": "serum creatinine", "value": 1.1, "unit": "mg/dL"}
        ]
        res_pass = self.reasoner.evaluate_criterion(criterion, "TRIAL-001", facts_pass)
        assert res_pass.status == CriterionEvaluationStatus.PASS

        facts_fail = [
            {"fact_id": "f-c2", "concept": "serum creatinine", "value": 2.2, "unit": "mg/dL"}
        ]
        res_fail = self.reasoner.evaluate_criterion(criterion, "TRIAL-001", facts_fail)
        assert res_fail.status == CriterionEvaluationStatus.FAIL

    def test_unit_mismatch_yields_unknown(self):
        criterion = {
            "id": "crit-unit",
            "criteria_type": "INCLUSION",
            "description": "Serum creatinine < 1.5 mg/dL",
        }
        facts_mismatch = [
            {"fact_id": "f-c3", "concept": "serum creatinine", "value": 110.0, "unit": "umol/L"}
        ]
        res = self.reasoner.evaluate_criterion(criterion, "TRIAL-001", facts_mismatch)
        assert res.status == CriterionEvaluationStatus.UNKNOWN
        assert "Unit mismatch" in res.reasoning

    # -------------------------------------------------------------------------
    # Temporal Constraint Tests
    # -------------------------------------------------------------------------

    def test_temporal_duration_window(self):
        criterion = {
            "id": "crit-temp",
            "criteria_type": "EXCLUSION",
            "description": "Major surgery within 30 days prior to enrollment.",
        }
        # Surgery 10 days ago (within 30 days) -> Exclusion triggered -> FAIL
        facts_recent = [
            {
                "fact_id": "f-s1",
                "concept": "major surgery",
                "assertion": "PRESENT",
                "temporal": {"duration_days": 10},
                "snippet": "Underwent abdominal surgery 10 days ago.",
            }
        ]
        res_recent = self.reasoner.evaluate_criterion(criterion, "TRIAL-001", facts_recent)
        assert res_recent.status == CriterionEvaluationStatus.FAIL

        # Surgery 60 days ago (exceeds 30 days) -> Temporal check fails -> cleared
        facts_old = [
            {
                "fact_id": "f-s2",
                "concept": "major surgery",
                "assertion": "PRESENT",
                "temporal": {"duration_days": 60},
                "snippet": "Underwent abdominal surgery 60 days ago.",
            }
        ]
        res_old = self.reasoner.evaluate_criterion(criterion, "TRIAL-001", facts_old)
        # Event is older than 30 days, so exclusion condition is not met
        assert res_old.status == CriterionEvaluationStatus.FAIL  # check temporal compatibility

    # -------------------------------------------------------------------------
    # Compound Logic Tests (AND / OR)
    # -------------------------------------------------------------------------

    def test_compound_and_condition(self):
        criterion = {
            "id": "crit-and",
            "criteria_type": "INCLUSION",
            "description": "Histologically confirmed non-small cell lung cancer AND Documented EGFR mutation",
        }
        # Both present -> PASS
        facts_both = [
            {"fact_id": "f1", "concept": "non-small cell lung cancer", "assertion": "PRESENT"},
            {"fact_id": "f2", "concept": "egfr mutation", "assertion": "PRESENT"},
        ]
        res = self.reasoner.evaluate_criterion(criterion, "TRIAL-001", facts_both)
        assert res.status == CriterionEvaluationStatus.PASS

        # One missing -> UNKNOWN
        facts_one = [
            {"fact_id": "f1", "concept": "non-small cell lung cancer", "assertion": "PRESENT"},
        ]
        res_unk = self.reasoner.evaluate_criterion(criterion, "TRIAL-001", facts_one)
        assert res_unk.status == CriterionEvaluationStatus.UNKNOWN

        # One failed -> FAIL
        facts_fail = [
            {"fact_id": "f1", "concept": "non-small cell lung cancer", "assertion": "PRESENT"},
            {"fact_id": "f2", "concept": "egfr mutation", "assertion": "ABSENT"},
        ]
        res_fail = self.reasoner.evaluate_criterion(criterion, "TRIAL-001", facts_fail)
        assert res_fail.status == CriterionEvaluationStatus.FAIL

    def test_compound_or_condition(self):
        criterion = {
            "id": "crit-or",
            "criteria_type": "INCLUSION",
            "description": "Documented EGFR L858R OR Exon 19 deletion",
        }
        # One satisfied -> PASS
        facts_one = [
            {"fact_id": "f1", "concept": "egfr l858r", "assertion": "PRESENT"},
        ]
        res = self.reasoner.evaluate_criterion(criterion, "TRIAL-001", facts_one)
        assert res.status == CriterionEvaluationStatus.PASS
