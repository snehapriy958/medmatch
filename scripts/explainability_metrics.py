"""
MedMatch Canonical Explainability & Evidence Graph Metrics Engine.
Phase 10: Explainability & Evidence Graph Foundation.

Defines deterministic mathematical metrics for:
- Evidence Coverage (EC)
- Decision Traceability Rate (DTR)
- Criterion Traceability Rate (CTR)
- Provenance Validity Rate (PVR)
- Explanation Support Rate (ESR)
- Unsupported Explanation Claim Rate (UECR)
- Contradiction Disclosure Rate (CDR)
- Graph Integrity Rate (GIR)

Implements strict zero-denominator safeguards and guardrails.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

try:
    from scripts.evidence_graph_schema import (
        EdgeType,
        EvidenceGraph,
        EvidenceGraphNode,
        NodeType,
    )
    from scripts.evidence_graph_validator import EvidenceGraphValidator, GraphValidationResult
    from scripts.explanation_schema import StructuredExplanation
    from scripts.explanation_validator import ExplanationValidationResult, ExplanationValidator
except ImportError:
    from evidence_graph_schema import (
        EdgeType,
        EvidenceGraph,
        EvidenceGraphNode,
        NodeType,
    )
    from evidence_graph_validator import EvidenceGraphValidator, GraphValidationResult
    from explanation_schema import StructuredExplanation
    from explanation_validator import ExplanationValidationResult, ExplanationValidator


class ExplainabilityMetricsReport(BaseModel):
    """
    Container for Phase 10 explainability and evidence graph metrics.
    """
    model_config = ConfigDict(extra="forbid")

    total_graphs: int = Field(default=0, ge=0)
    total_criteria_evaluations: int = Field(default=0, ge=0)
    total_decisions: int = Field(default=0, ge=0)
    total_evidence_nodes: int = Field(default=0, ge=0)
    total_explanation_claims: int = Field(default=0, ge=0)
    total_contradictory_cases: int = Field(default=0, ge=0)

    evidence_coverage: float = Field(default=0.0, ge=0.0, le=1.0)
    decision_traceability_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    criterion_traceability_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    provenance_validity_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    explanation_support_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    unsupported_explanation_claim_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    contradiction_disclosure_rate: float = Field(default=1.0, ge=0.0, le=1.0)
    graph_integrity_rate: float = Field(default=0.0, ge=0.0, le=1.0)


class ExplainabilityMetricsCalculator:
    """
    Deterministic calculation engine for Phase 10 metrics.
    """

    @staticmethod
    def calculate_metrics(
        graphs: List[EvidenceGraph],
        explanations: Optional[List[StructuredExplanation]] = None
    ) -> ExplainabilityMetricsReport:
        """
        Computes all Phase 10 metrics across a batch of graphs and explanations.
        """
        explanations = explanations or []
        total_graphs = len(graphs)

        if total_graphs == 0:
            return ExplainabilityMetricsReport(
                total_graphs=0,
                evidence_coverage=0.0,
                decision_traceability_rate=0.0,
                criterion_traceability_rate=0.0,
                provenance_validity_rate=0.0,
                explanation_support_rate=0.0,
                unsupported_explanation_claim_rate=0.0,
                contradiction_disclosure_rate=1.0,
                graph_integrity_rate=0.0,
            )

        # 1. Graph Integrity Rate (GIR)
        valid_graphs_count = 0
        for g in graphs:
            val_res = EvidenceGraphValidator.validate_graph(g)
            if val_res.is_valid:
                valid_graphs_count += 1
        gir = valid_graphs_count / total_graphs

        # Aggregated counters across all graphs
        total_evals = 0
        covered_evals = 0
        traceable_evals = 0

        total_decisions = 0
        traceable_decisions = 0

        total_evidence_nodes = 0
        valid_provenance_nodes = 0

        total_contra_cases = 0
        disclosed_contra_cases = 0

        for g in graphs:
            eval_nodes = g.get_nodes_by_type(NodeType.CRITERION_EVALUATION)
            total_evals += len(eval_nodes)

            for en in eval_nodes:
                # Evidence coverage: has incoming SUPPORTS or CONTRADICTS
                ev_edges = [
                    e for e in g.get_incoming_edges(en.node_id)
                    if e.edge_type in (EdgeType.SUPPORTS, EdgeType.CONTRADICTS)
                ]
                if ev_edges:
                    covered_evals += 1

                # Criterion traceability: has incoming EVALUATED_BY from TRIAL_CRITERION
                crit_edges = [
                    e for e in g.get_incoming_edges(en.node_id)
                    if e.edge_type == EdgeType.EVALUATED_BY
                ]
                if crit_edges:
                    traceable_evals += 1

                # Contradiction tracking
                has_contra = any(e.edge_type == EdgeType.CONTRADICTS for e in ev_edges)
                if has_contra:
                    total_contra_cases += 1
                    # Check if any explanation discloses it
                    matching_exps = [exp for exp in explanations if exp.target_node_id == en.node_id]
                    if matching_exps and all(exp.contradictory_evidence_references for exp in matching_exps):
                        disclosed_contra_cases += 1
                    elif not matching_exps:
                        # If no explanation generated yet for this node, count as disclosed if graph has it
                        disclosed_contra_cases += 1

            # Decisions
            dec_nodes = g.get_nodes_by_type(NodeType.ELIGIBILITY_DECISION)
            total_decisions += len(dec_nodes)
            for dn in dec_nodes:
                contrib_edges = [
                    e for e in g.get_incoming_edges(dn.node_id)
                    if e.edge_type == EdgeType.CONTRIBUTES_TO
                ]
                if contrib_edges:
                    traceable_decisions += 1

            # Evidence nodes provenance
            ev_nodes = g.get_nodes_by_type(NodeType.SOURCE_FRAGMENT) + g.get_nodes_by_type(NodeType.PATIENT_FACT)
            total_evidence_nodes += len(ev_nodes)
            for evn in ev_nodes:
                if evn.provenance:
                    prov = evn.provenance
                    if prov.start_char is not None and prov.end_char is not None:
                        if prov.start_char != -1 and prov.end_char != -1:
                            if prov.start_char <= prov.end_char and prov.start_char >= 0:
                                valid_provenance_nodes += 1
                        elif prov.start_char == -1 and prov.end_char == -1:
                            valid_provenance_nodes += 1
                    else:
                        valid_provenance_nodes += 1
                else:
                    # Patient facts may have fact_id without detailed text offsets
                    if evn.node_type == NodeType.PATIENT_FACT and "fact_id" in evn.properties:
                        valid_provenance_nodes += 1

        # 5. Explanation claims metrics
        total_claims = 0
        supported_claims = 0

        for exp in explanations:
            # Match explanation to its graph
            target_graph = next((g for g in graphs if exp.target_node_id in g.nodes), None)
            if target_graph:
                res = ExplanationValidator.validate_explanation(exp, target_graph)
                total_claims += res.total_claims
                supported_claims += res.supported_claims
            else:
                total_claims += len(exp.claims)

        ec = (covered_evals / total_evals) if total_evals > 0 else 1.0
        ctr = (traceable_evals / total_evals) if total_evals > 0 else 1.0
        dtr = (traceable_decisions / total_decisions) if total_decisions > 0 else 1.0
        pvr = (valid_provenance_nodes / total_evidence_nodes) if total_evidence_nodes > 0 else 1.0
        esr = (supported_claims / total_claims) if total_claims > 0 else 1.0
        uecr = (1.0 - esr) if total_claims > 0 else 0.0
        cdr = (disclosed_contra_cases / total_contra_cases) if total_contra_cases > 0 else 1.0

        return ExplainabilityMetricsReport(
            total_graphs=total_graphs,
            total_criteria_evaluations=total_evals,
            total_decisions=total_decisions,
            total_evidence_nodes=total_evidence_nodes,
            total_explanation_claims=total_claims,
            total_contradictory_cases=total_contra_cases,
            evidence_coverage=ec,
            decision_traceability_rate=dtr,
            criterion_traceability_rate=ctr,
            provenance_validity_rate=pvr,
            explanation_support_rate=esr,
            unsupported_explanation_claim_rate=uecr,
            contradiction_disclosure_rate=cdr,
            graph_integrity_rate=gir,
        )
