"""
Tests for Phase 10 Deterministic Explanation Generator.
"""

from scripts.evidence_graph_builder import EvidenceGraphBuilder
from scripts.explanation_generator import DeterministicExplanationGenerator
from scripts.explanation_schema import ExplanationType


def test_explain_criterion_evaluation_deterministic():
    """Verify deterministic explanation generation for a criterion evaluation."""
    builder = EvidenceGraphBuilder(graph_id="EXP-GEN-01", trial_id="NCT01", patient_id="PT-01")
    builder.add_trial_criterion("INC-1", "inclusion", "Age >= 18")
    frag_id = builder.add_source_fragment("FRAG-1", "DOC-1", "Age 42 documented in intake.", start_char=0, end_char=28)
    builder.add_patient_fact("FACT-1", concept="age", value=42, source_fragment_id=frag_id)
    eval_id = builder.add_criterion_evaluation(
        eval_id="EVAL-1",
        criterion_id="INC-1",
        status="PASS",
        reasoning="Age 42 >= 18",
        supporting_fact_ids=["FACT-1"],
    )
    graph = builder.build()

    exp = DeterministicExplanationGenerator.explain_criterion_evaluation(graph, eval_id)

    assert exp.explanation_type == ExplanationType.CRITERION_EXPLANATION
    assert exp.target_node_id == eval_id
    assert exp.decision_reference == "PASS"
    assert len(exp.claims) >= 3
    assert "Age >= 18" in exp.explanation_text
    assert "42" in exp.explanation_text


def test_explain_trial_decision_deterministic():
    """Verify explanation generation for aggregated trial decision."""
    builder = EvidenceGraphBuilder(graph_id="EXP-GEN-02", trial_id="NCT02", patient_id="PT-02")
    builder.add_trial_criterion("INC-1", "inclusion", "Age >= 18")
    builder.add_patient_fact("FACT-1", concept="age", value=15)
    eval_id = builder.add_criterion_evaluation(
        eval_id="EVAL-1",
        criterion_id="INC-1",
        status="FAIL",
        reasoning="Pediatric patient",
        contradicting_fact_ids=["FACT-1"],
    )
    dec_id = builder.add_eligibility_decision(
        decision_id="DEC-1",
        status="INELIGIBLE",
        clinical_summary="Disqualified by age",
        contributing_eval_ids=[eval_id],
    )
    graph = builder.build()

    exp = DeterministicExplanationGenerator.explain_eligibility_decision(graph, dec_id)

    assert exp.explanation_type == ExplanationType.TRIAL_DECISION_EXPLANATION
    assert exp.decision_reference == "INELIGIBLE"
    assert "INELIGIBLE" in exp.explanation_text
    assert any("INELIGIBLE" in c.claim_text for c in exp.claims)


def test_explain_review_resolution_preserves_machine_output():
    """Verify explanation of human review explicitly references original machine output."""
    builder = EvidenceGraphBuilder(graph_id="EXP-GEN-03", trial_id="NCT03", patient_id="PT-03")
    builder.add_trial_criterion("INC-1", "inclusion", "Lab check")
    eval_id = builder.add_criterion_evaluation("EVAL-1", "INC-1", "UNKNOWN", "Lab missing")
    unc_id = builder.add_uncertainty("UNC-1", "MISSING_PATIENT_FACT", "HIGH", "Missing lab", affected_eval_id=eval_id)
    rev_id = builder.add_review("REV-1", "RESOLVED", "PRIORITY", uncertainty_id=unc_id)
    res_id = builder.add_review_resolution(
        resolution_id="RES-1",
        review_id=rev_id,
        reviewer_id="REV-EXPERT",
        decision="RESOLVE_PASS",
        rationale="Lab report received via email",
        original_machine_output={"overall_status": "NEEDS_REVIEW"},
    )
    graph = builder.build()

    exp = DeterministicExplanationGenerator.explain_review_resolution(graph, res_id)

    assert exp.explanation_type == ExplanationType.REVIEW_EXPLANATION
    assert exp.decision_reference == "RESOLVE_PASS"
    assert "REV-EXPERT" in exp.explanation_text
    assert "NEEDS_REVIEW" in exp.explanation_text
