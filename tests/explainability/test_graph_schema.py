"""
Tests for Phase 10 Evidence Graph Schema & Contracts.
"""

import pytest
from scripts.evidence_graph_schema import (
    EdgeType,
    EvidenceGraph,
    EvidenceGraphEdge,
    EvidenceGraphNode,
    NodeProvenance,
    NodeType,
)


def test_node_and_edge_enums():
    """Verify all 13 node types and 16 edge types are defined."""
    assert len(NodeType) == 13
    assert len(EdgeType) == 16
    assert NodeType.PATIENT == "PATIENT"
    assert NodeType.CRITERION_EVALUATION == "CRITERION_EVALUATION"
    assert EdgeType.SUPPORTS == "SUPPORTS"
    assert EdgeType.CONTRIBUTES_TO == "CONTRIBUTES_TO"


def test_valid_node_creation():
    """Verify valid node instantiation with provenance."""
    prov = NodeProvenance(
        source_id="FRAG-001",
        document_id="NOTE-001",
        section="Assessment",
        start_char=10,
        end_char=50,
        page_number=1,
    )
    node = EvidenceGraphNode(
        node_id="FRAG-001",
        node_type=NodeType.SOURCE_FRAGMENT,
        label="Biomarker snippet",
        properties={"text": "KRAS G12C positive"},
        provenance=prov,
    )
    assert node.node_id == "FRAG-001"
    assert node.provenance.start_char == 10
    assert node.provenance.end_char == 50


def test_graph_container_duplicate_node_rejection():
    """Verify EvidenceGraph rejects duplicate node IDs."""
    graph = EvidenceGraph(graph_id="G1", trial_id="T1", patient_id="P1")
    n1 = EvidenceGraphNode(node_id="N1", node_type=NodeType.PATIENT, label="P1")
    graph.add_node(n1)
    
    with pytest.raises(ValueError, match="Duplicate node_id"):
        graph.add_node(n1)


def test_graph_container_edge_addition_and_traversal():
    """Verify edge addition, traversal, and neighboring queries."""
    graph = EvidenceGraph(graph_id="G1", trial_id="T1", patient_id="P1")
    n1 = EvidenceGraphNode(node_id="PAT-1", node_type=NodeType.PATIENT, label="Patient 1")
    n2 = EvidenceGraphNode(node_id="FACT-1", node_type=NodeType.PATIENT_FACT, label="Fact 1")
    graph.add_node(n1)
    graph.add_node(n2)

    edge = EvidenceGraphEdge(
        edge_id="e1",
        source_id="PAT-1",
        target_id="FACT-1",
        edge_type=EdgeType.HAS_FACT,
    )
    graph.add_edge(edge)

    assert len(graph.edges) == 1
    assert len(graph.get_outgoing_edges("PAT-1")) == 1
    assert len(graph.get_incoming_edges("FACT-1")) == 1
    assert len(graph.get_incoming_edges("PAT-1")) == 0

    neighbors = graph.get_neighbors("PAT-1", direction="outgoing")
    assert len(neighbors) == 1
    assert neighbors[0].node_id == "FACT-1"


def test_graph_serialization_roundtrip():
    """Verify exact JSON round-trip equivalence."""
    graph = EvidenceGraph(graph_id="G-ROUNDTRIP", trial_id="T1", patient_id="P1")
    n1 = EvidenceGraphNode(node_id="PAT-1", node_type=NodeType.PATIENT, label="Patient 1")
    n2 = EvidenceGraphNode(node_id="FACT-1", node_type=NodeType.PATIENT_FACT, label="Fact 1")
    graph.add_node(n1)
    graph.add_node(n2)
    graph.add_edge(
        EvidenceGraphEdge(
            edge_id="e1",
            source_id="PAT-1",
            target_id="FACT-1",
            edge_type=EdgeType.HAS_FACT,
        )
    )

    json_str = graph.to_json()
    reconstituted = EvidenceGraph.from_json(json_str)

    assert reconstituted.graph_id == graph.graph_id
    assert len(reconstituted.nodes) == len(graph.nodes)
    assert len(reconstituted.edges) == len(graph.edges)
    assert reconstituted.nodes["FACT-1"].label == "Fact 1"
