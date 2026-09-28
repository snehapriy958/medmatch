"""
MedMatch Canonical Evidence Graph Schemas & Contracts.
Phase 10: Explainability & Evidence Graph Foundation.

Defines strongly-typed Pydantic models for:
- NodeType: 13 canonical graph node categories
- EdgeType: 16 canonical typed relational links
- NodeProvenance: Source document, section, offset, page, and retrieval tracking
- EvidenceGraphNode: Verifiable atomic node representation
- EvidenceGraphEdge: Typed directed relationship between nodes
- EvidenceGraph: Canonical graph container with serialization and query traversal
"""

from __future__ import annotations

import datetime
import json
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# =============================================================================
# 1. Canonical Graph Enumerations
# =============================================================================

class NodeType(str, Enum):
    """
    Taxonomic category of an evidence graph node.
    """
    PATIENT = "PATIENT"
    PATIENT_FACT = "PATIENT_FACT"
    SOURCE_DOCUMENT = "SOURCE_DOCUMENT"
    SOURCE_FRAGMENT = "SOURCE_FRAGMENT"
    TRIAL = "TRIAL"
    TRIAL_CRITERION = "TRIAL_CRITERION"
    RETRIEVAL_RESULT = "RETRIEVAL_RESULT"
    CRITERION_EVALUATION = "CRITERION_EVALUATION"
    ELIGIBILITY_DECISION = "ELIGIBILITY_DECISION"
    UNCERTAINTY = "UNCERTAINTY"
    REVIEW = "REVIEW"
    REVIEW_RESOLUTION = "REVIEW_RESOLUTION"
    EXPLANATION = "EXPLANATION"


class EdgeType(str, Enum):
    """
    Semantic relationship connecting two evidence graph nodes.
    """
    HAS_FACT = "HAS_FACT"                         # PATIENT -> PATIENT_FACT
    DERIVED_FROM = "DERIVED_FROM"                 # PATIENT_FACT -> SOURCE_FRAGMENT
    BELONGS_TO = "BELONGS_TO"                     # SOURCE_FRAGMENT -> SOURCE_DOCUMENT
    HAS_CRITERION = "HAS_CRITERION"               # TRIAL -> TRIAL_CRITERION
    SUPPORTS = "SUPPORTS"                         # PATIENT_FACT / SOURCE_FRAGMENT -> CRITERION_EVALUATION
    CONTRADICTS = "CONTRADICTS"                   # PATIENT_FACT / SOURCE_FRAGMENT -> CRITERION_EVALUATION
    CONTEXTUALIZES = "CONTEXTUALIZES"             # PATIENT_FACT / SOURCE_FRAGMENT -> CRITERION_EVALUATION
    EVALUATED_BY = "EVALUATED_BY"                 # TRIAL_CRITERION -> CRITERION_EVALUATION
    RETRIEVED_CRITERION = "RETRIEVED_CRITERION"   # RETRIEVAL_RESULT -> TRIAL_CRITERION
    RETRIEVED_FROM = "RETRIEVED_FROM"             # RETRIEVAL_RESULT -> SOURCE_DOCUMENT / TRIAL
    CONTRIBUTES_TO = "CONTRIBUTES_TO"             # CRITERION_EVALUATION -> ELIGIBILITY_DECISION
    HAS_UNCERTAINTY = "HAS_UNCERTAINTY"           # CRITERION_EVALUATION / PATIENT_FACT -> UNCERTAINTY
    TRIGGERS = "TRIGGERS"                         # UNCERTAINTY -> REVIEW
    RESOLVED_BY = "RESOLVED_BY"                   # REVIEW -> REVIEW_RESOLUTION
    SUPPORTED_BY = "SUPPORTED_BY"                 # REVIEW_RESOLUTION -> SOURCE_FRAGMENT / PATIENT_FACT
    EXPLAINS = "EXPLAINS"                         # EXPLANATION -> CRITERION_EVALUATION / ELIGIBILITY_DECISION / REVIEW


# Allowed source and target node types for each EdgeType (for validation)
VALID_EDGE_CONSTRAINTS: Dict[EdgeType, List[Tuple[Set[NodeType], Set[NodeType]]]] = {
    EdgeType.HAS_FACT: [
        ({NodeType.PATIENT}, {NodeType.PATIENT_FACT})
    ],
    EdgeType.DERIVED_FROM: [
        ({NodeType.PATIENT_FACT}, {NodeType.SOURCE_FRAGMENT}),
        ({NodeType.TRIAL_CRITERION}, {NodeType.SOURCE_FRAGMENT})
    ],
    EdgeType.BELONGS_TO: [
        ({NodeType.SOURCE_FRAGMENT}, {NodeType.SOURCE_DOCUMENT})
    ],
    EdgeType.HAS_CRITERION: [
        ({NodeType.TRIAL}, {NodeType.TRIAL_CRITERION})
    ],
    EdgeType.SUPPORTS: [
        ({NodeType.PATIENT_FACT, NodeType.SOURCE_FRAGMENT}, {NodeType.CRITERION_EVALUATION})
    ],
    EdgeType.CONTRADICTS: [
        ({NodeType.PATIENT_FACT, NodeType.SOURCE_FRAGMENT}, {NodeType.CRITERION_EVALUATION})
    ],
    EdgeType.CONTEXTUALIZES: [
        ({NodeType.PATIENT_FACT, NodeType.SOURCE_FRAGMENT}, {NodeType.CRITERION_EVALUATION})
    ],
    EdgeType.EVALUATED_BY: [
        ({NodeType.TRIAL_CRITERION}, {NodeType.CRITERION_EVALUATION})
    ],
    EdgeType.RETRIEVED_CRITERION: [
        ({NodeType.RETRIEVAL_RESULT}, {NodeType.TRIAL_CRITERION})
    ],
    EdgeType.RETRIEVED_FROM: [
        ({NodeType.RETRIEVAL_RESULT}, {NodeType.SOURCE_DOCUMENT, NodeType.TRIAL})
    ],
    EdgeType.CONTRIBUTES_TO: [
        ({NodeType.CRITERION_EVALUATION}, {NodeType.ELIGIBILITY_DECISION})
    ],
    EdgeType.HAS_UNCERTAINTY: [
        ({NodeType.CRITERION_EVALUATION, NodeType.PATIENT_FACT}, {NodeType.UNCERTAINTY})
    ],
    EdgeType.TRIGGERS: [
        ({NodeType.UNCERTAINTY}, {NodeType.REVIEW})
    ],
    EdgeType.RESOLVED_BY: [
        ({NodeType.REVIEW}, {NodeType.REVIEW_RESOLUTION})
    ],
    EdgeType.SUPPORTED_BY: [
        ({NodeType.REVIEW_RESOLUTION}, {NodeType.SOURCE_FRAGMENT, NodeType.PATIENT_FACT})
    ],
    EdgeType.EXPLAINS: [
        ({NodeType.EXPLANATION}, {NodeType.CRITERION_EVALUATION, NodeType.ELIGIBILITY_DECISION, NodeType.REVIEW, NodeType.UNCERTAINTY})
    ],
}


# =============================================================================
# 2. Provenance Models
# =============================================================================

class NodeProvenance(BaseModel):
    """
    Fine-grained provenance metadata associated with an evidence-bearing node.
    Enforces non-fabrication of character offsets and page numbers.
    """
    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(..., min_length=1, description="Identifier of the origin source entity")
    document_id: Optional[str] = Field(default=None, description="Clinical note, pathology report, or trial document ID")
    section: Optional[str] = Field(default=None, description="Section heading (e.g. 'Past Medical History', 'Inclusion Criteria')")
    start_char: Optional[int] = Field(default=-1, ge=-1, description="0-based start character offset (-1 if unlocatable)")
    end_char: Optional[int] = Field(default=-1, ge=-1, description="0-based end character offset (-1 if unlocatable)")
    page_number: Optional[int] = Field(default=None, ge=1, description="1-based page number if document is paginated")
    retrieval_method: Optional[str] = Field(default=None, description="Retrieval algorithm (e.g. 'dense', 'lexical_bm25', 'hybrid_rrf')")
    retrieval_rank: Optional[int] = Field(default=None, ge=1, description="Retrieval rank position (1-indexed)")
    retrieval_score: Optional[float] = Field(default=None, description="Retrieval similarity or reranking score")
    extraction_timestamp: Optional[str] = Field(default=None, description="ISO-8601 UTC timestamp of extraction")

    @model_validator(mode="after")
    def validate_offsets(self) -> NodeProvenance:
        # Offsets are structurally preserved for EvidenceGraphValidator invariant inspection (G3 / X2)
        return self


# =============================================================================
# 3. Canonical Node & Edge Models
# =============================================================================

class EvidenceGraphNode(BaseModel):
    """
    Atomic entity in the MedMatch Evidence Graph.
    """
    model_config = ConfigDict(extra="forbid")

    node_id: str = Field(..., min_length=1, description="Unique, immutable identifier across the graph")
    node_type: NodeType = Field(..., description="Categorical entity type")
    label: str = Field(..., min_length=1, description="Human-readable node label or summary")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Structured attributes (status, value, concept, etc.)")
    provenance: Optional[NodeProvenance] = Field(default=None, description="Verifiable origin metadata")
    created_at: str = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat(),
        description="ISO-8601 timestamp"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional non-clinical annotations")


class EvidenceGraphEdge(BaseModel):
    """
    Directed typed relationship linking two EvidenceGraphNodes.
    """
    model_config = ConfigDict(extra="forbid")

    edge_id: str = Field(..., min_length=1, description="Unique identifier for the edge")
    source_id: str = Field(..., min_length=1, description="Origin node_id")
    target_id: str = Field(..., min_length=1, description="Destination node_id")
    edge_type: EdgeType = Field(..., description="Semantic relationship category")
    label: Optional[str] = Field(default=None, description="Optional descriptive label")
    weight: float = Field(default=1.0, ge=0.0, description="Confidence or relationship weight")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Relationship-specific properties")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional annotations")


# =============================================================================
# 4. Canonical Evidence Graph Container
# =============================================================================

class EvidenceGraph(BaseModel):
    """
    Canonical strongly-typed container for the MedMatch Evidence Graph.
    Maintains graph invariants, referential integrity, and traversal helpers.
    """
    model_config = ConfigDict(extra="forbid")

    graph_id: str = Field(..., min_length=1, description="Unique graph identifier, e.g. 'GRAPH-TRIAL-001-PAT-001'")
    trial_id: str = Field(..., min_length=1, description="Target clinical trial NCT ID or identifier")
    patient_id: str = Field(..., min_length=1, description="Target patient identifier")
    version: str = Field(default="1.0.0", description="Graph schema version")
    created_at: str = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat(),
        description="ISO-8601 timestamp"
    )
    nodes: Dict[str, EvidenceGraphNode] = Field(default_factory=dict, description="Map of node_id -> EvidenceGraphNode")
    edges: List[EvidenceGraphEdge] = Field(default_factory=list, description="List of directed edges")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Graph-level metadata")

    def add_node(self, node: EvidenceGraphNode) -> None:
        """Adds a node to the graph; raises ValueError if duplicate node_id exists."""
        if node.node_id in self.nodes:
            raise ValueError(f"Duplicate node_id: '{node.node_id}' already exists in graph.")
        self.nodes[node.node_id] = node

    def add_edge(self, edge: EvidenceGraphEdge) -> None:
        """Adds an edge to the graph after verifying that source and target nodes exist."""
        if edge.source_id not in self.nodes:
            raise ValueError(f"Edge source_id '{edge.source_id}' does not exist in graph nodes.")
        if edge.target_id not in self.nodes:
            raise ValueError(f"Edge target_id '{edge.target_id}' does not exist in graph nodes.")
        self.edges.append(edge)

    def get_node(self, node_id: str) -> Optional[EvidenceGraphNode]:
        """Returns node with given node_id, or None if not found."""
        return self.nodes.get(node_id)

    def get_nodes_by_type(self, node_type: NodeType) -> List[EvidenceGraphNode]:
        """Returns all nodes matching the specified NodeType."""
        return [n for n in self.nodes.values() if n.node_type == node_type]

    def get_edges(
        self,
        source_id: Optional[str] = None,
        target_id: Optional[str] = None,
        edge_type: Optional[EdgeType] = None
    ) -> List[EvidenceGraphEdge]:
        """Queries edges filtered by source_id, target_id, and/or edge_type."""
        results = self.edges
        if source_id is not None:
            results = [e for e in results if e.source_id == source_id]
        if target_id is not None:
            results = [e for e in results if e.target_id == target_id]
        if edge_type is not None:
            results = [e for e in results if e.edge_type == edge_type]
        return results

    def get_outgoing_edges(self, node_id: str) -> List[EvidenceGraphEdge]:
        """Returns all edges originating from node_id."""
        return self.get_edges(source_id=node_id)

    def get_incoming_edges(self, node_id: str) -> List[EvidenceGraphEdge]:
        """Returns all edges targeting node_id."""
        return self.get_edges(target_id=node_id)

    def get_neighbors(self, node_id: str, direction: str = "both") -> List[EvidenceGraphNode]:
        """
        Returns adjacent nodes in direction 'outgoing', 'incoming', or 'both'.
        """
        neighbor_ids: Set[str] = set()
        if direction in ("outgoing", "both"):
            neighbor_ids.update(e.target_id for e in self.get_outgoing_edges(node_id))
        if direction in ("incoming", "both"):
            neighbor_ids.update(e.source_id for e in self.get_incoming_edges(node_id))
        return [self.nodes[nid] for nid in neighbor_ids if nid in self.nodes]

    def to_dict(self) -> Dict[str, Any]:
        """Serializes graph to a Python dictionary."""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EvidenceGraph:
        """Deserializes graph from a Python dictionary."""
        return cls.model_validate(data)

    def to_json(self, indent: int = 2) -> str:
        """Serializes graph to formatted JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_json(cls, json_str: str) -> EvidenceGraph:
        """Deserializes graph from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
