"""
Tests for Phase 10 Explanation Validator.
"""

from scripts.evidence_graph_builder import EvidenceGraphBuilder
from scripts.evidence_graph_validator import GraphErrorCode
from scripts.explanation_generator import DeterministicExplanationGenerator
from scripts.explanation_schema import (
    ExplanationClaim,
    ExplanationType,
    StructuredExplanation,
)
from scripts.explanation_validator import ExplanationValidator


def test_validator_accepts_clean_generated_explanation():
    """Verify that a deterministically generated explanation passes validation."""
    builder = EvidenceGraphBuilder(graph_id="VAL-EXP-01", trial_id="T1", patient_id="P1")
    builder.add_trial_criterion("INC-1", "inclusion", "Age >= 18")
    builder.add_patient_fact("FACT-1", concept="age", value=25)
    eval_id = builder.add_criterion_evaluation("EVAL-1", "INC-1", "PASS", "Valid", supporting_fact_ids=["FACT-1"])
    graph = builder.build()

    exp = DeterministicExplanationGenerator.explain_criterion_evaluation(graph, eval_id)
    res = ExplanationValidator.validate_explanation(exp, graph)

    assert res.is_valid is True
    assert len(res.errors) == 0
    assert res.unsupported_claims == 0


def test_validator_rejects_unsupported_hallucinated_claim():
    """Verify that claims citing non-existent graph nodes trigger X9."""
    builder = EvidenceGraphBuilder(graph_id="VAL-EXP-02", trial_id="T2", patient_id="P2")
    builder.add_trial_criterion("INC-1", "inclusion", "Age >= 18")
    builder.add_patient_fact("FACT-1", concept="age", value=25)
    eval_id = builder.add_criterion_evaluation("EVAL-1", "INC-1", "PASS", "Valid", supporting_fact_ids=["FACT-1"])
    graph = builder.build()

    # Create explanation with hallucinated claim referencing GHOST_NODE
    exp = StructuredExplanation(
        explanation_id="EXP-BAD",
        explanation_type=ExplanationType.CRITERION_EXPLANATION,
        target_node_id=eval_id,
        decision_reference="PASS",
        claims=[
            ExplanationClaim(
                claim_id="CLM-HALLUCINATED",
                claim_text="Patient has history of liver transplant.",
                referenced_node_ids=["GHOST_TRANSPLANT_NODE"],
            )
        ],
        explanation_text="Fabricated liver transplant history.",
    )

    res = ExplanationValidator.validate_explanation(exp, graph)
    assert res.is_valid is False
    assert any(e.error_code == GraphErrorCode.X9_UNSUPPORTED_EXPLANATION_CLAIM for e in res.errors)
    assert res.unsupported_claims == 1


def test_validator_enforces_contradiction_disclosure():
    """Verify that omitting contradictory evidence present in graph triggers X10."""
    builder = EvidenceGraphBuilder(graph_id="VAL-EXP-03", trial_id="T3", patient_id="P3")
    builder.add_trial_criterion("INC-1", "inclusion", "Penicillin tolerance")
    builder.add_patient_fact("FACT-1", concept="allergy", value="None")
    builder.add_patient_fact("FACT-2", concept="allergy", value="Anaphylaxis")
    eval_id = builder.add_criterion_evaluation(
        "EVAL-1", "INC-1", "UNKNOWN", "Conflicting allergy notes",
        supporting_fact_ids=["FACT-1"],
        contradicting_fact_ids=["FACT-2"],
    )
    graph = builder.build()

    # Explanation that omits the contradiction
    exp = StructuredExplanation(
        explanation_id="EXP-OMISSION",
        explanation_type=ExplanationType.CRITERION_EXPLANATION,
        target_node_id=eval_id,
        decision_reference="UNKNOWN",
        supporting_evidence_references=["FACT-1"],
        contradictory_evidence_references=[],  # Deliberately empty
        claims=[
            ExplanationClaim(
                claim_id="CLM-1",
                claim_text="Patient chart mentions no allergy.",
                referenced_node_ids=["FACT-1"],
            )
        ],
        explanation_text="Patient reported no allergies.",
    )

    res = ExplanationValidator.validate_explanation(exp, graph)
    assert res.is_valid is False
    assert any(e.error_code == GraphErrorCode.X10_CONTRADICTORY_EVIDENCE_OMITTED for e in res.errors)
    assert res.contradictions_disclosed is False
