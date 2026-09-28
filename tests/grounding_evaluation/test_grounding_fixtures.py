"""
Tests verifying all 16 Phase 8 Development Test Fixtures.
Phase 8: Grounding Evaluation & Faithfulness Auditing.
"""

import json
import os
import pytest

from scripts.eligibility_schema import (
    CriterionEvaluationRecord,
    CriterionEvaluationStatus,
    CriterionType,
    EvidenceCitation,
)
from scripts.grounding_validator import GroundingValidator


class TestGroundingFixtures:
    """Runs GroundingValidator across all 16 canonical synthetic development cases."""

    @pytest.fixture
    def fixture_data(self):
        fixture_path = os.path.join("data", "fixtures", "phase8", "grounding_fixtures.json")
        with open(fixture_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def test_fixture_loads_16_cases(self, fixture_data):
        """Verifies exactly 16 cases are present in grounding_fixtures.json."""
        assert "cases" in fixture_data
        assert len(fixture_data["cases"]) == 16

    def test_all_16_cases_match_expected_faithfulness(self, fixture_data):
        """Verifies GroundingValidator evaluates each synthetic case according to its design."""
        validator = GroundingValidator()

        for case in fixture_data["cases"]:
            case_id = case["case_id"]
            expected_faithful = case["expected_faithful"]

            # Construct CriterionEvaluationRecord
            citations = [
                EvidenceCitation(
                    fact_id=c.get("fact_id"),
                    text_snippet=c.get("text_snippet", ""),
                    source_field=c.get("source_field", "patient_note"),
                    start_char=c.get("start_char", -1),
                    end_char=c.get("end_char", -1),
                    assertion_type=c.get("assertion_type", "PRESENT"),
                )
                for c in case.get("evidence_citations", [])
            ]

            status_str = case.get("status", "PASS")
            crit_status = (
                CriterionEvaluationStatus.PASS
                if status_str == "PASS"
                else (CriterionEvaluationStatus.FAIL if status_str == "FAIL" else CriterionEvaluationStatus.UNKNOWN)
            )

            record = CriterionEvaluationRecord(
                criterion_id=case["criterion"]["id"],
                trial_id=case["trial_id"],
                criterion_type=CriterionType(case["criterion"]["criteria_type"]),
                criterion_text=case["criterion"]["description"],
                status=crit_status,
                reasoning=case["reasoning_text"],
                evidence_citations=citations,
            )

            # Evaluate
            g_eval = validator.evaluate_criterion_record(
                record=record,
                patient_facts=case.get("patient_facts", []),
                criteria=[case["criterion"]],
                demographics=case.get("demographics"),
                retrieved_evidence=case.get("retrieved_evidence"),
                patient_note=case.get("patient_note"),
            )

            assert g_eval.is_faithful == expected_faithful, (
                f"Case '{case_id}' expected is_faithful={expected_faithful}, but got {g_eval.is_faithful}. "
                f"Metrics: CSR={g_eval.claim_support_rate}, UCR={g_eval.unsupported_claim_rate}, "
                f"CR={g_eval.contradiction_rate}, CVR={g_eval.citation_validity_rate}"
            )
