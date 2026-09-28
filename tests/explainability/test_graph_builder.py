"""
Tests for Phase 10 Evidence Graph Builder.
"""

from scripts.evidence_graph_builder import EvidenceGraphBuilder
from scripts.evidence_graph_schema import EdgeType, NodeType


def test_build_complete_evidence_graph():
    """Verify end-to-end evidence graph construction using builder."""
    builder = EvidenceGraphBuilder(
        graph_id="BUILD-TEST-01",
        trial_id="NCT01234567",
        patient_id="PT-999",
    )

    doc_id = builder.add_source_document("DOC-1", "Progress Note")
    frag_id = builder.add_source_fragment("FRAG-1", "DOC-1", "Patient has ECOG 1", start_char=0, end_char=18)
    fact_id = builder.add_patient_fact("FACT-1", concept="ecog", value=1, source_fragment_id=frag_id)

    crit_id = builder.add_trial_criterion("INC-1", criterion_type="inclusion", text="ECOG <= 1")
    ret_id = builder.add_retrieval_result("RET-1", "INC-1", rank=1, score=0.95, method="dense")

    eval_id = builder.add_criterion_evaluation(
        eval_id="EVAL-1",
        criterion_id="INC-1",
        status="PASS",
        reasoning="ECOG 1 <= 1",
        supporting_fact_ids=["FACT-1"],
    )

    dec_id = builder.add_eligibility_decision(
        decision_id="DEC-1",
        status="ELIGIBLE",
        clinical_summary="Met all criteria",
        contributing_eval_ids=["EVAL-1"],
    )

    graph = builder.build()

    assert graph.graph_id == "BUILD-TEST-01"
    assert len(graph.nodes) == 9  # PAT, TRIAL, DOC, FRAG, FACT, CRIT, RET, EVAL, DEC
    assert "PAT-PT-999" in graph.nodes
    assert "TRIAL-NCT01234567" in graph.nodes
    assert f"DOC-{doc_id}" in graph.nodes or doc_id in graph.nodes
    assert "FACT-1" in graph.nodes
    assert "CRIT-INC-1" in graph.nodes
    assert "EVAL-1" in graph.nodes
    assert "DEC-1" in graph.nodes

    # Check edges
    has_fact_edges = [e for e in graph.edges if e.edge_type == EdgeType.HAS_FACT]
    assert len(has_fact_edges) == 1
    eval_by_edges = [e for e in graph.edges if e.edge_type == EdgeType.EVALUATED_BY]
    assert len(eval_by_edges) == 1
    supports_edges = [e for e in graph.edges if e.edge_type == EdgeType.SUPPORTS]
    assert len(supports_edges) == 1
    contrib_edges = [e for e in graph.edges if e.edge_type == EdgeType.CONTRIBUTES_TO]
    assert len(contrib_edges) == 1


def test_build_uncertainty_and_review_resolution():
    """Verify builder properly connects uncertainty, review, and resolution."""
    builder = EvidenceGraphBuilder(
        graph_id="BUILD-TEST-02",
        trial_id="NCT01234567",
        patient_id="PT-998",
    )

    builder.add_trial_criterion("INC-1", "inclusion", "Platelets >= 100")
    builder.add_criterion_evaluation("EVAL-1", "INC-1", "UNKNOWN", "Platelet count missing")

    unc_id = builder.add_uncertainty("UNC-1", "MISSING_PATIENT_FACT", "HIGH", "Missing CBC", affected_eval_id="EVAL-1")
    rev_id = builder.add_review("REV-1", "RESOLVED", "PRIORITY", uncertainty_id=unc_id)

    frag_id = builder.add_source_fragment("FRAG-FAX", "DOC-FAX", "Platelet count 150 confirmed on outside fax", start_char=0, end_char=44)
    builder.add_review_resolution(
        resolution_id="RES-1",
        review_id=rev_id,
        reviewer_id="REV-CLINICIAN",
        decision="RESOLVE_PASS",
        rationale="Outside lab confirmed normal platelets",
        original_machine_output={"status": "NEEDS_REVIEW"},
        evidence_fragment_ids=[frag_id],
    )

    graph = builder.build()
    assert "UNC-1" in graph.nodes
    assert "REV-1" in graph.nodes
    assert "RES-1" in graph.nodes

    triggers_edges = [e for e in graph.edges if e.edge_type == EdgeType.TRIGGERS]
    assert len(triggers_edges) == 1
    resolved_edges = [e for e in graph.edges if e.edge_type == EdgeType.RESOLVED_BY]
    assert len(resolved_edges) == 1
    supp_edges = [e for e in graph.edges if e.edge_type == EdgeType.SUPPORTED_BY]
    assert len(supp_edges) == 1
