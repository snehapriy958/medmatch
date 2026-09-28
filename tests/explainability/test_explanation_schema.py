"""
Tests for Phase 10 Explanation Schema & Claims.
"""

from scripts.explanation_schema import (
    ExplanationClaim,
    ExplanationType,
    StructuredExplanation,
)


def test_explanation_types_enum():
    """Verify all 4 explanation scopes exist."""
    assert len(ExplanationType) == 4
    assert ExplanationType.CRITERION_EXPLANATION == "CRITERION_EXPLANATION"
    assert ExplanationType.TRIAL_DECISION_EXPLANATION == "TRIAL_DECISION_EXPLANATION"
    assert ExplanationType.UNCERTAINTY_EXPLANATION == "UNCERTAINTY_EXPLANATION"
    assert ExplanationType.REVIEW_EXPLANATION == "REVIEW_EXPLANATION"


def test_valid_structured_explanation():
    """Verify instantiation of StructuredExplanation with fine-grained claims."""
    claim1 = ExplanationClaim(
        claim_id="CLM-01",
        claim_text="Trial requires Age >= 18.",
        claim_type="CRITERION_REQUIREMENT",
        referenced_node_ids=["CRIT-1"],
    )
    claim2 = ExplanationClaim(
        claim_id="CLM-02",
        claim_text="Patient age is 45.",
        claim_type="FACT_ASSERTION",
        referenced_node_ids=["FACT-1"],
    )

    exp = StructuredExplanation(
        explanation_id="EXP-01",
        explanation_type=ExplanationType.CRITERION_EXPLANATION,
        target_node_id="EVAL-1",
        decision_reference="PASS",
        criterion_references=["CRIT-1"],
        supporting_evidence_references=["FACT-1"],
        claims=[claim1, claim2],
        explanation_text="Age 45 satisfies requirement of Age >= 18.",
    )

    assert exp.explanation_id == "EXP-01"
    assert len(exp.claims) == 2
    assert exp.decision_reference == "PASS"
    assert exp.generation_method == "deterministic_rule_based"
