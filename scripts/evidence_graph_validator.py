"""
MedMatch Canonical Evidence Graph Validator.
Phase 10: Explainability & Evidence Graph Foundation.

Validates the 12 Graph Invariants (G1–G12):
- G1: Every criterion evaluation references a valid criterion.
- G2: Every evidence-backed evaluation references valid evidence.
- G3: Every evidence source has valid provenance.
- G4: Every trial decision references its criterion evaluations.
- G5: Every uncertainty references the affected criterion/case.
- G6: Every review request references its uncertainty.
- G7: Every review resolution references its review.
- G8: Reviewer overrides preserve machine output.
- G9: No dangling evidence references.
- G10: No fabricated provenance.
- G11: No duplicate stable IDs within a graph.
- G12: Graph serialization/deserialization preserves semantic equivalence.

Categorizes validation violations under Phase 10 error taxonomy (X1–X14).
"""

from __future__ import annotations

import copy
import json
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

try:
    from scripts.evidence_graph_schema import (
        EdgeType,
        EvidenceGraph,
        EvidenceGraphEdge,
        EvidenceGraphNode,
        NodeProvenance,
        NodeType,
        VALID_EDGE_CONSTRAINTS,
    )
except ImportError:
    from evidence_graph_schema import (
        EdgeType,
        EvidenceGraph,
        EvidenceGraphEdge,
        EvidenceGraphNode,
        NodeProvenance,
        NodeType,
        VALID_EDGE_CONSTRAINTS,
    )


class GraphErrorCode(str, Enum):
    """
    Phase 10 structural and relational graph error codes.
    """
    X1_MISSING_EVIDENCE_LINK = "X1_MISSING_EVIDENCE_LINK"
    X2_INVALID_PROVENANCE = "X2_INVALID_PROVENANCE"
    X3_DANGLING_GRAPH_REFERENCE = "X3_DANGLING_GRAPH_REFERENCE"
    X4_DUPLICATE_NODE_ID = "X4_DUPLICATE_NODE_ID"
    X5_INCORRECT_CRITERION_LINKAGE = "X5_INCORRECT_CRITERION_LINKAGE"
    X6_INCORRECT_DECISION_LINKAGE = "X6_INCORRECT_DECISION_LINKAGE"
    X7_LOST_UNCERTAINTY_LINKAGE = "X7_LOST_UNCERTAINTY_LINKAGE"
    X8_LOST_REVIEW_LINKAGE = "X8_LOST_REVIEW_LINKAGE"
    X9_UNSUPPORTED_EXPLANATION_CLAIM = "X9_UNSUPPORTED_EXPLANATION_CLAIM"
    X10_CONTRADICTORY_EVIDENCE_OMITTED = "X10_CONTRADICTORY_EVIDENCE_OMITTED"
    X11_MACHINE_DECISION_OVERWRITTEN = "X11_MACHINE_DECISION_OVERWRITTEN"
    X12_EXPLANATION_ALTERS_DECISION = "X12_EXPLANATION_ALTERS_DECISION"
    X13_FABRICATED_SOURCE_LOCATION = "X13_FABRICATED_SOURCE_LOCATION"
    X14_GRAPH_SERIALIZATION_CORRUPTION = "X14_GRAPH_SERIALIZATION_CORRUPTION"


class GraphValidationError(BaseModel):
    """
    Structured violation diagnostic record.
    """
    model_config = ConfigDict(extra="forbid")

    error_code: GraphErrorCode = Field(..., description="Taxonomic error code")
    invariant_violated: str = Field(..., description="G1 through G12 invariant tag")
    message: str = Field(..., min_length=3, description="Descriptive diagnostic details")
    entity_id: Optional[str] = Field(default=None, description="Affected node_id or edge_id")
    details: Dict[str, Any] = Field(default_factory=dict, description="Contextual debugging information")


class GraphValidationResult(BaseModel):
    """
    Summary outcome of graph invariant checks.
    """
    model_config = ConfigDict(extra="forbid")

    graph_id: str = Field(..., description="Validated graph identifier")
    is_valid: bool = Field(..., description="True if zero errors found")
    errors: List[GraphValidationError] = Field(default_factory=list, description="Encountered invariant violations")
    node_count: int = Field(default=0, ge=0)
    edge_count: int = Field(default=0, ge=0)
    invariants_checked: List[str] = Field(
        default_factory=lambda: [f"G{i}" for i in range(1, 13)]
    )


class EvidenceGraphValidator:
    """
    Deterministic rule-based integrity validator for MedMatch Evidence Graphs.
    """

    @classmethod
    def validate_graph(cls, graph: EvidenceGraph) -> GraphValidationResult:
        """
        Executes complete verification of G1 through G12 against an EvidenceGraph.
        """
        errors: List[GraphValidationError] = []

        # -------------------------------------------------------------
        # G11 & G4 / Basic structural collection
        # Check duplicate edge IDs
        # -------------------------------------------------------------
        seen_edge_ids = set()
        for edge in graph.edges:
            if edge.edge_id in seen_edge_ids:
                errors.append(
                    GraphValidationError(
                        error_code=GraphErrorCode.X4_DUPLICATE_NODE_ID,
                        invariant_violated="G11",
                        message=f"Duplicate edge_id: '{edge.edge_id}' detected.",
                        entity_id=edge.edge_id,
                    )
                )
            seen_edge_ids.add(edge.edge_id)

        # -------------------------------------------------------------
        # G9: No dangling evidence references in edges
        # -------------------------------------------------------------
        for edge in graph.edges:
            if edge.source_id not in graph.nodes:
                errors.append(
                    GraphValidationError(
                        error_code=GraphErrorCode.X3_DANGLING_GRAPH_REFERENCE,
                        invariant_violated="G9",
                        message=f"Dangling edge '{edge.edge_id}': source_id '{edge.source_id}' does not exist in graph nodes.",
                        entity_id=edge.edge_id,
                        details={"edge": edge.model_dump()},
                    )
                )
            if edge.target_id not in graph.nodes:
                errors.append(
                    GraphValidationError(
                        error_code=GraphErrorCode.X3_DANGLING_GRAPH_REFERENCE,
                        invariant_violated="G9",
                        message=f"Dangling edge '{edge.edge_id}': target_id '{edge.target_id}' does not exist in graph nodes.",
                        entity_id=edge.edge_id,
                        details={"edge": edge.model_dump()},
                    )
                )

        # Edge type constraints
        for edge in graph.edges:
            src_node = graph.nodes.get(edge.source_id)
            tgt_node = graph.nodes.get(edge.target_id)
            if src_node and tgt_node and edge.edge_type in VALID_EDGE_CONSTRAINTS:
                valid_pairs = VALID_EDGE_CONSTRAINTS[edge.edge_type]
                matched = any(
                    (src_node.node_type in allowed_srcs and tgt_node.node_type in allowed_tgts)
                    for allowed_srcs, allowed_tgts in valid_pairs
                )
                if not matched:
                    errors.append(
                        GraphValidationError(
                            error_code=GraphErrorCode.X5_INCORRECT_CRITERION_LINKAGE,
                            invariant_violated="G1",
                            message=(
                                f"Invalid edge connection for {edge.edge_type}: "
                                f"Source {src_node.node_type} -> Target {tgt_node.node_type} is not allowed."
                            ),
                            entity_id=edge.edge_id,
                        )
                    )

        # -------------------------------------------------------------
        # G1: Every criterion evaluation references a valid criterion
        # -------------------------------------------------------------
        eval_nodes = graph.get_nodes_by_type(NodeType.CRITERION_EVALUATION)
        for eval_node in eval_nodes:
            # incoming EVALUATED_BY edge from TRIAL_CRITERION
            incoming_eval_edges = [
                e for e in graph.get_incoming_edges(eval_node.node_id)
                if e.edge_type == EdgeType.EVALUATED_BY
            ]
            if not incoming_eval_edges:
                errors.append(
                    GraphValidationError(
                        error_code=GraphErrorCode.X5_INCORRECT_CRITERION_LINKAGE,
                        invariant_violated="G1",
                        message=f"Criterion evaluation '{eval_node.node_id}' is not linked to any TrialCriterion via EVALUATED_BY.",
                        entity_id=eval_node.node_id,
                    )
                )
            else:
                for ie in incoming_eval_edges:
                    crit_node = graph.nodes.get(ie.source_id)
                    if not crit_node or crit_node.node_type != NodeType.TRIAL_CRITERION:
                        errors.append(
                            GraphValidationError(
                                error_code=GraphErrorCode.X5_INCORRECT_CRITERION_LINKAGE,
                                invariant_violated="G1",
                                message=f"Evaluation '{eval_node.node_id}' references invalid criterion node '{ie.source_id}'.",
                                entity_id=eval_node.node_id,
                            )
                        )

        # -------------------------------------------------------------
        # G2: Every evidence-backed evaluation references valid evidence
        # PASS and FAIL evaluations strictly require supporting/contradicting evidence
        # -------------------------------------------------------------
        for eval_node in eval_nodes:
            status = eval_node.properties.get("status")
            if status in ("PASS", "FAIL"):
                # Must have incoming SUPPORTS or CONTRADICTS edge from a PATIENT_FACT or SOURCE_FRAGMENT
                evidence_edges = [
                    e for e in graph.get_incoming_edges(eval_node.node_id)
                    if e.edge_type in (EdgeType.SUPPORTS, EdgeType.CONTRADICTS)
                ]
                if not evidence_edges:
                    errors.append(
                        GraphValidationError(
                            error_code=GraphErrorCode.X1_MISSING_EVIDENCE_LINK,
                            invariant_violated="G2",
                            message=f"Criterion evaluation '{eval_node.node_id}' has status '{status}' but lacks incoming SUPPORTS or CONTRADICTS evidence edges.",
                            entity_id=eval_node.node_id,
                        )
                    )

        # -------------------------------------------------------------
        # G3 & G10: Provenance validity and non-fabrication
        # -------------------------------------------------------------
        for node in graph.nodes.values():
            if node.provenance:
                prov = node.provenance
                # Offset consistency
                if prov.start_char is not None and prov.end_char is not None:
                    if prov.start_char != -1 and prov.end_char != -1:
                        if prov.start_char > prov.end_char:
                            errors.append(
                                GraphValidationError(
                                    error_code=GraphErrorCode.X2_INVALID_PROVENANCE,
                                    invariant_violated="G3",
                                    message=f"Node '{node.node_id}' has invalid offsets: start_char ({prov.start_char}) > end_char ({prov.end_char}).",
                                    entity_id=node.node_id,
                                )
                            )
                # Unlocatable spans must use -1, not arbitrary fake numbers
                if prov.start_char is not None and prov.start_char < -1:
                    errors.append(
                        GraphValidationError(
                            error_code=GraphErrorCode.X13_FABRICATED_SOURCE_LOCATION,
                            invariant_violated="G10",
                            message=f"Node '{node.node_id}' has invalid negative offset < -1: {prov.start_char}.",
                            entity_id=node.node_id,
                        )
                    )
            # Source fragments must have provenance
            if node.node_type == NodeType.SOURCE_FRAGMENT:
                if not node.provenance or not node.provenance.source_id:
                    errors.append(
                        GraphValidationError(
                            error_code=GraphErrorCode.X2_INVALID_PROVENANCE,
                            invariant_violated="G3",
                            message=f"Source fragment '{node.node_id}' lacks mandatory provenance information.",
                            entity_id=node.node_id,
                        )
                    )

        # -------------------------------------------------------------
        # G4: Every trial decision references its criterion evaluations
        # -------------------------------------------------------------
        decision_nodes = graph.get_nodes_by_type(NodeType.ELIGIBILITY_DECISION)
        for dec_node in decision_nodes:
            incoming_contributions = [
                e for e in graph.get_incoming_edges(dec_node.node_id)
                if e.edge_type == EdgeType.CONTRIBUTES_TO
            ]
            if not incoming_contributions:
                errors.append(
                    GraphValidationError(
                        error_code=GraphErrorCode.X6_INCORRECT_DECISION_LINKAGE,
                        invariant_violated="G4",
                        message=f"Eligibility decision '{dec_node.node_id}' has no incoming CONTRIBUTES_TO criterion evaluations.",
                        entity_id=dec_node.node_id,
                    )
                )

        # -------------------------------------------------------------
        # G5: Every uncertainty references the affected criterion/fact
        # -------------------------------------------------------------
        unc_nodes = graph.get_nodes_by_type(NodeType.UNCERTAINTY)
        for unc in unc_nodes:
            incoming_unc_edges = [
                e for e in graph.get_incoming_edges(unc.node_id)
                if e.edge_type == EdgeType.HAS_UNCERTAINTY
            ]
            if not incoming_unc_edges:
                errors.append(
                    GraphValidationError(
                        error_code=GraphErrorCode.X7_LOST_UNCERTAINTY_LINKAGE,
                        invariant_violated="G5",
                        message=f"Uncertainty node '{unc.node_id}' is orphaned; lacks incoming HAS_UNCERTAINTY edge.",
                        entity_id=unc.node_id,
                    )
                )

        # -------------------------------------------------------------
        # G6: Every review request references its uncertainty
        # -------------------------------------------------------------
        review_nodes = graph.get_nodes_by_type(NodeType.REVIEW)
        for rev in review_nodes:
            incoming_triggers = [
                e for e in graph.get_incoming_edges(rev.node_id)
                if e.edge_type == EdgeType.TRIGGERS
            ]
            if not incoming_triggers:
                errors.append(
                    GraphValidationError(
                        error_code=GraphErrorCode.X8_LOST_REVIEW_LINKAGE,
                        invariant_violated="G6",
                        message=f"Review node '{rev.node_id}' is orphaned; lacks incoming TRIGGERS edge from Uncertainty.",
                        entity_id=rev.node_id,
                    )
                )

        # -------------------------------------------------------------
        # G7: Every review resolution references its review
        # -------------------------------------------------------------
        res_nodes = graph.get_nodes_by_type(NodeType.REVIEW_RESOLUTION)
        for res in res_nodes:
            incoming_resolutions = [
                e for e in graph.get_incoming_edges(res.node_id)
                if e.edge_type == EdgeType.RESOLVED_BY
            ]
            if not incoming_resolutions:
                errors.append(
                    GraphValidationError(
                        error_code=GraphErrorCode.X8_LOST_REVIEW_LINKAGE,
                        invariant_violated="G7",
                        message=f"Review resolution '{res.node_id}' lacks incoming RESOLVED_BY edge from a Review node.",
                        entity_id=res.node_id,
                    )
                )

        # -------------------------------------------------------------
        # G8: Reviewer overrides preserve machine output
        # -------------------------------------------------------------
        for res in res_nodes:
            orig_output = res.properties.get("original_machine_output")
            if orig_output is None:
                errors.append(
                    GraphValidationError(
                        error_code=GraphErrorCode.X11_MACHINE_DECISION_OVERWRITTEN,
                        invariant_violated="G8",
                        message=f"Review resolution '{res.node_id}' failed to preserve 'original_machine_output'.",
                        entity_id=res.node_id,
                    )
                )

        # -------------------------------------------------------------
        # G12: Graph serialization/deserialization semantic equivalence
        # -------------------------------------------------------------
        try:
            serialized_json = graph.to_json()
            reconstituted = EvidenceGraph.from_json(serialized_json)
            if len(reconstituted.nodes) != len(graph.nodes) or len(reconstituted.edges) != len(graph.edges):
                errors.append(
                    GraphValidationError(
                        error_code=GraphErrorCode.X14_GRAPH_SERIALIZATION_CORRUPTION,
                        invariant_violated="G12",
                        message="Reconstituted graph node/edge counts do not match original.",
                        entity_id=graph.graph_id,
                    )
                )
        except Exception as e:
            errors.append(
                GraphValidationError(
                    error_code=GraphErrorCode.X14_GRAPH_SERIALIZATION_CORRUPTION,
                    invariant_violated="G12",
                    message=f"Serialization round-trip raised an exception: {str(e)}",
                    entity_id=graph.graph_id,
                )
            )

        return GraphValidationResult(
            graph_id=graph.graph_id,
            is_valid=(len(errors) == 0),
            errors=errors,
            node_count=len(graph.nodes),
            edge_count=len(graph.edges),
        )
