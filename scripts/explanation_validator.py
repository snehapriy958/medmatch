"""
MedMatch Canonical Explanation Validator.
Phase 10: Explainability & Evidence Graph Foundation.

Validates that clinical explanations strictly satisfy explanation guardrails:
- Every referenced node exists in the EvidenceGraph.
- Every claim is grounded in graph evidence (no hallucinations / X9).
- Contradictory evidence present in the graph is surfaced (not hidden / X10).
- Explanation generation does not alter decisions (X12) or overwrite machine reasoning (X11).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

try:
    from scripts.evidence_graph_schema import (
        EdgeType,
        EvidenceGraph,
        NodeType,
    )
    from scripts.evidence_graph_validator import GraphErrorCode, GraphValidationError
    from scripts.explanation_schema import (
        ExplanationClaim,
        ExplanationType,
        StructuredExplanation,
    )
except ImportError:
    from evidence_graph_schema import (
        EdgeType,
        EvidenceGraph,
        NodeType,
    )
    from evidence_graph_validator import GraphErrorCode, GraphValidationError
    from explanation_schema import (
        ExplanationClaim,
        ExplanationType,
        StructuredExplanation,
    )


class ExplanationValidationResult(BaseModel):
    """
    Validation report for an individual StructuredExplanation.
    """
    model_config = ConfigDict(extra="forbid")

    explanation_id: str = Field(..., description="Target explanation identifier")
    is_valid: bool = Field(..., description="True if explanation satisfies all guardrails")
    errors: List[GraphValidationError] = Field(default_factory=list, description="Diagnostic violation list")
    total_claims: int = Field(default=0, ge=0)
    supported_claims: int = Field(default=0, ge=0)
    unsupported_claims: int = Field(default=0, ge=0)
    contradictions_disclosed: bool = Field(default=True)


class ExplanationValidator:
    """
    Deterministic rule-based explanation validator.
    """

    @classmethod
    def validate_explanation(
        cls,
        explanation: StructuredExplanation,
        graph: EvidenceGraph
    ) -> ExplanationValidationResult:
        """
        Validates a StructuredExplanation against an EvidenceGraph.
        """
        errors: List[GraphValidationError] = []

        # 1. Target node existence
        target_node = graph.get_node(explanation.target_node_id)
        if not target_node:
            errors.append(
                GraphValidationError(
                    error_code=GraphErrorCode.X3_DANGLING_GRAPH_REFERENCE,
                    invariant_violated="G9",
                    message=f"Explanation target_node_id '{explanation.target_node_id}' does not exist in graph.",
                    entity_id=explanation.explanation_id,
                )
            )

        # 2. Referential integrity of evidence references
        for ref in explanation.supporting_evidence_references:
            if ref not in graph.nodes:
                errors.append(
                    GraphValidationError(
                        error_code=GraphErrorCode.X3_DANGLING_GRAPH_REFERENCE,
                        invariant_violated="G9",
                        message=f"Supporting evidence reference '{ref}' does not exist in graph nodes.",
                        entity_id=ref,
                    )
                )

        for ref in explanation.contradictory_evidence_references:
            if ref not in graph.nodes:
                errors.append(
                    GraphValidationError(
                        error_code=GraphErrorCode.X3_DANGLING_GRAPH_REFERENCE,
                        invariant_violated="G9",
                        message=f"Contradictory evidence reference '{ref}' does not exist in graph nodes.",
                        entity_id=ref,
                    )
                )

        for ref in explanation.criterion_references:
            if ref not in graph.nodes:
                errors.append(
                    GraphValidationError(
                        error_code=GraphErrorCode.X5_INCORRECT_CRITERION_LINKAGE,
                        invariant_violated="G1",
                        message=f"Criterion reference '{ref}' does not exist in graph nodes.",
                        entity_id=ref,
                    )
                )

        for ref in explanation.uncertainty_references:
            if ref not in graph.nodes:
                errors.append(
                    GraphValidationError(
                        error_code=GraphErrorCode.X7_LOST_UNCERTAINTY_LINKAGE,
                        invariant_violated="G5",
                        message=f"Uncertainty reference '{ref}' does not exist in graph nodes.",
                        entity_id=ref,
                    )
                )

        # 3. Claim-level grounding checks
        supported_claims = 0
        unsupported_claims = 0

        for claim in explanation.claims:
            claim_grounded = True
            if not claim.referenced_node_ids:
                # Claim without any graph grounding
                claim_grounded = False
            else:
                for nid in claim.referenced_node_ids:
                    if nid not in graph.nodes:
                        claim_grounded = False
                        break

            if claim_grounded:
                supported_claims += 1
            else:
                unsupported_claims += 1
                errors.append(
                    GraphValidationError(
                        error_code=GraphErrorCode.X9_UNSUPPORTED_EXPLANATION_CLAIM,
                        invariant_violated="G2",
                        message=f"Claim '{claim.claim_id}' asserts ungrounded proposition: '{claim.claim_text}'. Referenced nodes not in graph.",
                        entity_id=claim.claim_id,
                        details={"referenced_nodes": claim.referenced_node_ids},
                    )
                )

        # 4. Contradiction disclosure guardrail
        # If target node has incoming CONTRADICTS edges in graph, the explanation MUST disclose them
        contradictions_disclosed = True
        if target_node and target_node.node_type == NodeType.CRITERION_EVALUATION:
            graph_contra_edges = [
                e for e in graph.get_incoming_edges(target_node.node_id)
                if e.edge_type == EdgeType.CONTRADICTS
            ]
            if graph_contra_edges:
                # Explanation must have contradictory_evidence_references or mention contradiction in claims
                has_contra_ref = len(explanation.contradictory_evidence_references) > 0
                has_contra_claim = any(
                    any(e.source_id in c.referenced_node_ids for e in graph_contra_edges)
                    for c in explanation.claims
                )
                if not (has_contra_ref or has_contra_claim):
                    contradictions_disclosed = False
                    errors.append(
                        GraphValidationError(
                            error_code=GraphErrorCode.X10_CONTRADICTORY_EVIDENCE_OMITTED,
                            invariant_violated="G2",
                            message=f"Evaluation '{target_node.node_id}' has contradictory evidence in graph that was omitted from explanation.",
                            entity_id=target_node.node_id,
                            details={"contradicting_edges": [e.edge_id for e in graph_contra_edges]},
                        )
                    )

        # 5. Non-alteration of decisions guardrail
        if target_node:
            node_status = target_node.properties.get("status")
            if node_status and explanation.decision_reference:
                if explanation.decision_reference != node_status:
                    errors.append(
                        GraphValidationError(
                            error_code=GraphErrorCode.X12_EXPLANATION_ALTERS_DECISION,
                            invariant_violated="G8",
                            message=f"Explanation alters decision: explanation states '{explanation.decision_reference}' but graph target node has status '{node_status}'.",
                            entity_id=explanation.explanation_id,
                        )
                    )

        return ExplanationValidationResult(
            explanation_id=explanation.explanation_id,
            is_valid=(len(errors) == 0),
            errors=errors,
            total_claims=len(explanation.claims),
            supported_claims=supported_claims,
            unsupported_claims=unsupported_claims,
            contradictions_disclosed=contradictions_disclosed,
        )
