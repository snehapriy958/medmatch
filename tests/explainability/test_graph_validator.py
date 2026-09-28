"""
Tests for Phase 10 Evidence Graph Validator (Invariants G1–G12).
"""

from scripts.evidence_graph_schema import (
    EdgeType,
    EvidenceGraph,
    EvidenceGraphEdge,
    EvidenceGraphNode,
    NodeProvenance,
    NodeType,
)
from scripts.evidence_graph_validator import EvidenceGraphValidator, GraphErrorCode


def test_validator_clean_graph_passes():
    """Verify that a compliant graph passes all G1-G12 invariants."""
    graph = EvidenceGraph(graph_id="VAL-G1", trial_id="T1", patient_id="P1")
    graph.add_node(EvidenceGraphNode(node_id="PAT-1", node_type=NodeType.PATIENT, label="Patient"))
    graph.add_node(EvidenceGraphNode(node_id="FACT-1", node_type=NodeType.PATIENT_FACT, label="Age 25", properties={"concept": "age", "value": 25}))
    graph.add_node(EvidenceGraphNode(node_id="TRIAL-1", node_type=NodeType.TRIAL, label="Trial 1"))
    graph.add_node(EvidenceGraphNode(node_id="CRIT-1", node_type=NodeType.TRIAL_CRITERION, label="Age >= 18", properties={"criterion_id": "CRIT-1"}))
    graph.add_node(EvidenceGraphNode(node_id="EVAL-1", node_type=NodeType.CRITERION_EVALUATION, label="PASS", properties={"criterion_id": "CRIT-1", "status": "PASS"}))
    graph.add_node(EvidenceGraphNode(node_id="DEC-1", node_type=NodeType.ELIGIBILITY_DECISION, label="ELIGIBLE", properties={"status": "ELIGIBLE"}))

    graph.add_edge(EvidenceGraphEdge(edge_id="e1", source_id="PAT-1", target_id="FACT-1", edge_type=EdgeType.HAS_FACT))
    graph.add_edge(EvidenceGraphEdge(edge_id="e2", source_id="TRIAL-1", target_id="CRIT-1", edge_type=EdgeType.HAS_CRITERION))
    graph.add_edge(EvidenceGraphEdge(edge_id="e3", source_id="CRIT-1", target_id="EVAL-1", edge_type=EdgeType.EVALUATED_BY))
    graph.add_edge(EvidenceGraphEdge(edge_id="e4", source_id="FACT-1", target_id="EVAL-1", edge_type=EdgeType.SUPPORTS))
    graph.add_edge(EvidenceGraphEdge(edge_id="e5", source_id="EVAL-1", target_id="DEC-1", edge_type=EdgeType.CONTRIBUTES_TO))

    res = EvidenceGraphValidator.validate_graph(graph)
    assert res.is_valid is True
    assert len(res.errors) == 0


def test_validator_flags_missing_evidence_link_on_pass():
    """G2: PASS evaluation lacking supporting evidence edge must be flagged (X1)."""
    graph = EvidenceGraph(graph_id="VAL-G2", trial_id="T1", patient_id="P1")
    graph.add_node(EvidenceGraphNode(node_id="TRIAL-1", node_type=NodeType.TRIAL, label="Trial"))
    graph.add_node(EvidenceGraphNode(node_id="CRIT-1", node_type=NodeType.TRIAL_CRITERION, label="Inclusion", properties={"criterion_id": "C1"}))
    graph.add_node(EvidenceGraphNode(node_id="EVAL-1", node_type=NodeType.CRITERION_EVALUATION, label="Eval", properties={"criterion_id": "C1", "status": "PASS"}))
    graph.add_node(EvidenceGraphNode(node_id="DEC-1", node_type=NodeType.ELIGIBILITY_DECISION, label="Dec", properties={"status": "ELIGIBLE"}))

    graph.add_edge(EvidenceGraphEdge(edge_id="e1", source_id="TRIAL-1", target_id="CRIT-1", edge_type=EdgeType.HAS_CRITERION))
    graph.add_edge(EvidenceGraphEdge(edge_id="e2", source_id="CRIT-1", target_id="EVAL-1", edge_type=EdgeType.EVALUATED_BY))
    graph.add_edge(EvidenceGraphEdge(edge_id="e3", source_id="EVAL-1", target_id="DEC-1", edge_type=EdgeType.CONTRIBUTES_TO))

    res = EvidenceGraphValidator.validate_graph(graph)
    assert res.is_valid is False
    assert any(e.error_code == GraphErrorCode.X1_MISSING_EVIDENCE_LINK for e in res.errors)


def test_validator_flags_dangling_edge_reference():
    """G9: Edge pointing to non-existent node must trigger X3_DANGLING_GRAPH_REFERENCE."""
    graph = EvidenceGraph(graph_id="VAL-G3", trial_id="T1", patient_id="P1")
    graph.add_node(EvidenceGraphNode(node_id="PAT-1", node_type=NodeType.PATIENT, label="Patient"))
    
    # Non-existent target node
    graph.edges.append(
        EvidenceGraphEdge(edge_id="e_dangling", source_id="PAT-1", target_id="GHOST_NODE", edge_type=EdgeType.HAS_FACT)
    )

    res = EvidenceGraphValidator.validate_graph(graph)
    assert res.is_valid is False
    assert any(e.error_code == GraphErrorCode.X3_DANGLING_GRAPH_REFERENCE for e in res.errors)


def test_validator_flags_invalid_offsets():
    """G3: start_char > end_char must trigger X2_INVALID_PROVENANCE."""
    graph = EvidenceGraph(graph_id="VAL-G4", trial_id="T1", patient_id="P1")
    prov = NodeProvenance(source_id="S1", document_id="D1", start_char=100, end_char=50)
    frag = EvidenceGraphNode(node_id="FRAG-1", node_type=NodeType.SOURCE_FRAGMENT, label="Frag", provenance=prov)
    graph.add_node(frag)

    res = EvidenceGraphValidator.validate_graph(graph)
    assert res.is_valid is False
    assert any(e.error_code == GraphErrorCode.X2_INVALID_PROVENANCE for e in res.errors)


def test_validator_flags_decision_without_contributing_evals():
    """G4: ELIGIBILITY_DECISION without CONTRIBUTES_TO edges must trigger X6."""
    graph = EvidenceGraph(graph_id="VAL-G5", trial_id="T1", patient_id="P1")
    graph.add_node(EvidenceGraphNode(node_id="DEC-1", node_type=NodeType.ELIGIBILITY_DECISION, label="Decision", properties={"status": "ELIGIBLE"}))

    res = EvidenceGraphValidator.validate_graph(graph)
    assert res.is_valid is False
    assert any(e.error_code == GraphErrorCode.X6_INCORRECT_DECISION_LINKAGE for e in res.errors)
