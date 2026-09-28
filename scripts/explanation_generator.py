"""
MedMatch Deterministic Explanation Generator.
Phase 10: Explainability & Evidence Graph Foundation.

Generates structured, traceable, graph-grounded clinical explanations
strictly from EvidenceGraph facts. Uses deterministic template synthesis;
strictly avoids LLM hallucination and external fact fabrication.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional

try:
    from scripts.evidence_graph_schema import (
        EdgeType,
        EvidenceGraph,
        EvidenceGraphNode,
        NodeType,
    )
    from scripts.explanation_schema import (
        ExplanationClaim,
        ExplanationType,
        StructuredExplanation,
    )
except ImportError:
    from evidence_graph_schema import (
        EdgeType,
        EvidenceGraph,
        EvidenceGraphNode,
        NodeType,
    )
    from explanation_schema import (
        ExplanationClaim,
        ExplanationType,
        StructuredExplanation,
    )


class DeterministicExplanationGenerator:
    """
    Deterministic rule-based explanation engine.
    Derives all text, claims, and citations strictly from an EvidenceGraph.
    """

    @classmethod
    def explain_criterion_evaluation(
        cls,
        graph: EvidenceGraph,
        eval_node_id: str,
        explanation_id: Optional[str] = None
    ) -> StructuredExplanation:
        """
        Synthesizes a structured explanation for an individual criterion evaluation.
        """
        eval_node = graph.get_node(eval_node_id)
        if not eval_node or eval_node.node_type != NodeType.CRITERION_EVALUATION:
            raise ValueError(f"Node '{eval_node_id}' is not a valid CRITERION_EVALUATION node.")

        status = eval_node.properties.get("status", "UNKNOWN")
        reasoning = eval_node.properties.get("reasoning", "")
        crit_id_prop = eval_node.properties.get("criterion_id", "")

        # Find linked TRIAL_CRITERION
        incoming_eval = [e for e in graph.get_incoming_edges(eval_node_id) if e.edge_type == EdgeType.EVALUATED_BY]
        crit_node: Optional[EvidenceGraphNode] = None
        if incoming_eval:
            crit_node = graph.get_node(incoming_eval[0].source_id)

        crit_text = crit_node.properties.get("criterion_text", crit_node.label) if crit_node else crit_id_prop
        crit_type = crit_node.properties.get("criterion_type", "criterion") if crit_node else "criterion"

        # Find evidence nodes
        supporting_edges = [e for e in graph.get_incoming_edges(eval_node_id) if e.edge_type == EdgeType.SUPPORTS]
        contradicting_edges = [e for e in graph.get_incoming_edges(eval_node_id) if e.edge_type == EdgeType.CONTRADICTS]
        context_edges = [e for e in graph.get_incoming_edges(eval_node_id) if e.edge_type == EdgeType.CONTEXTUALIZES]

        supporting_nodes = [graph.get_node(e.source_id) for e in supporting_edges if graph.get_node(e.source_id)]
        contradicting_nodes = [graph.get_node(e.source_id) for e in contradicting_edges if graph.get_node(e.source_id)]

        # Find uncertainties
        unc_edges = [e for e in graph.get_outgoing_edges(eval_node_id) if e.edge_type == EdgeType.HAS_UNCERTAINTY]
        unc_nodes = [graph.get_node(e.target_id) for e in unc_edges if graph.get_node(e.target_id)]

        claims: List[ExplanationClaim] = []
        claim_counter = 1

        # Claim 1: Requirement
        crit_refs = [crit_node.node_id] if crit_node else []
        claims.append(
            ExplanationClaim(
                claim_id=f"CLM-{eval_node_id}-{claim_counter}",
                claim_text=f"Trial requires {crit_type}: '{crit_text}'.",
                claim_type="CRITERION_REQUIREMENT",
                referenced_node_ids=crit_refs,
            )
        )
        claim_counter += 1

        # Claim 2: Supporting evidence
        supp_refs: List[str] = []
        for sn in supporting_nodes:
            if sn:
                supp_refs.append(sn.node_id)
                fact_desc = sn.properties.get("concept", sn.label)
                val = sn.properties.get("value", "")
                text_frag = sn.properties.get("text", "")
                if val:
                    evidence_desc = f"{fact_desc} is recorded as {val}"
                elif text_frag:
                    evidence_desc = f"source documentation confirms '{text_frag}'"
                else:
                    evidence_desc = sn.label

                claims.append(
                    ExplanationClaim(
                        claim_id=f"CLM-{eval_node_id}-{claim_counter}",
                        claim_text=f"Patient evidence indicates that {evidence_desc}.",
                        claim_type="FACT_ASSERTION",
                        referenced_node_ids=[sn.node_id],
                    )
                )
                claim_counter += 1

        # Claim 3: Contradicting evidence
        contra_refs: List[str] = []
        for cn in contradicting_nodes:
            if cn:
                contra_refs.append(cn.node_id)
                claims.append(
                    ExplanationClaim(
                        claim_id=f"CLM-{eval_node_id}-{claim_counter}",
                        claim_text=f"Conflicting or disqualifying evidence observed in {cn.node_id}: {cn.label}.",
                        claim_type="FACT_ASSERTION",
                        referenced_node_ids=[cn.node_id],
                    )
                )
                claim_counter += 1

        # Claim 4: Uncertainty if applicable
        unc_refs: List[str] = []
        for un in unc_nodes:
            if un:
                unc_refs.append(un.node_id)
                u_type = un.properties.get("uncertainty_type", "UNCERTAINTY")
                u_desc = un.properties.get("description", un.label)
                claims.append(
                    ExplanationClaim(
                        claim_id=f"CLM-{eval_node_id}-{claim_counter}",
                        claim_text=f"Clinical uncertainty identified ({u_type}): {u_desc}.",
                        claim_type="UNCERTAINTY_STATEMENT",
                        referenced_node_ids=[un.node_id],
                    )
                )
                claim_counter += 1

        # Claim 5: Evaluation conclusion
        claims.append(
            ExplanationClaim(
                claim_id=f"CLM-{eval_node_id}-{claim_counter}",
                claim_text=f"Based on available graph evidence, criterion {crit_id_prop} is evaluated as {status}.",
                claim_type="EVALUATION_RESULT",
                referenced_node_ids=[eval_node.node_id],
            )
        )

        # Assemble full text
        text_parts = [
            f"Evaluation for {crit_type.upper()} criterion '{crit_text}': Status is {status}."
        ]
        if supp_refs:
            supp_labels = [n.label for n in supporting_nodes if n]
            text_parts.append(f"Supporting patient evidence: {'; '.join(supp_labels)}.")
        if contra_refs:
            contra_labels = [n.label for n in contradicting_nodes if n]
            text_parts.append(f"Contradicting / disqualifying evidence: {'; '.join(contra_labels)}.")
        if unc_refs:
            unc_labels = [n.properties.get('description', n.label) for n in unc_nodes if n]
            text_parts.append(f"Uncertainty notes: {'; '.join(unc_labels)}.")
        if reasoning:
            text_parts.append(f"Reasoning summary: {reasoning}")

        exp_id = explanation_id or f"EXP-{eval_node_id}"

        return StructuredExplanation(
            explanation_id=exp_id,
            explanation_type=ExplanationType.CRITERION_EXPLANATION,
            target_node_id=eval_node_id,
            decision_reference=status,
            criterion_references=crit_refs,
            supporting_evidence_references=supp_refs,
            contradictory_evidence_references=contra_refs,
            uncertainty_references=unc_refs,
            claims=claims,
            explanation_text=" ".join(text_parts),
            generation_method="deterministic_rule_based",
            is_graph_grounded=True,
        )

    @classmethod
    def explain_eligibility_decision(
        cls,
        graph: EvidenceGraph,
        decision_node_id: str,
        explanation_id: Optional[str] = None
    ) -> StructuredExplanation:
        """
        Synthesizes a structured explanation for an aggregated trial eligibility decision.
        Strictly reflects Phase 6 deterministic aggregation (ANY FAIL -> INELIGIBLE;
        NO FAIL + ANY UNKNOWN -> NEEDS_REVIEW; ALL PASS -> ELIGIBLE).
        """
        decision_node = graph.get_node(decision_node_id)
        if not decision_node or decision_node.node_type != NodeType.ELIGIBILITY_DECISION:
            raise ValueError(f"Node '{decision_node_id}' is not a valid ELIGIBILITY_DECISION node.")

        status = decision_node.properties.get("status", "UNKNOWN")
        summary = decision_node.properties.get("clinical_summary", "")

        # Find contributing evaluation nodes
        incoming_contrib = [e for e in graph.get_incoming_edges(decision_node_id) if e.edge_type == EdgeType.CONTRIBUTES_TO]
        eval_nodes = [graph.get_node(e.source_id) for e in incoming_contrib if graph.get_node(e.source_id)]

        pass_evals = [n for n in eval_nodes if n and n.properties.get("status") == "PASS"]
        fail_evals = [n for n in eval_nodes if n and n.properties.get("status") == "FAIL"]
        unknown_evals = [n for n in eval_nodes if n and n.properties.get("status") == "UNKNOWN"]

        claims: List[ExplanationClaim] = []
        claim_counter = 1

        claims.append(
            ExplanationClaim(
                claim_id=f"CLM-{decision_node_id}-{claim_counter}",
                claim_text=f"Evaluated {len(eval_nodes)} trial criteria: {len(pass_evals)} PASS, {len(fail_evals)} FAIL, {len(unknown_evals)} UNKNOWN.",
                claim_type="DECISION_SYNTHESIS",
                referenced_node_ids=[n.node_id for n in eval_nodes if n],
            )
        )
        claim_counter += 1

        if status == "INELIGIBLE":
            fail_ids = [n.properties.get("criterion_id", n.node_id) for n in fail_evals if n]
            claims.append(
                ExplanationClaim(
                    claim_id=f"CLM-{decision_node_id}-{claim_counter}",
                    claim_text=f"Patient is INELIGIBLE due to failure of criterion/criteria: {', '.join(fail_ids)}.",
                    claim_type="DECISION_SYNTHESIS",
                    referenced_node_ids=[n.node_id for n in fail_evals if n],
                )
            )
        elif status == "NEEDS_REVIEW":
            unk_ids = [n.properties.get("criterion_id", n.node_id) for n in unknown_evals if n]
            claims.append(
                ExplanationClaim(
                    claim_id=f"CLM-{decision_node_id}-{claim_counter}",
                    claim_text=f"Decision is NEEDS_REVIEW because zero criteria failed, but {len(unknown_evals)} criteria remain UNKNOWN: {', '.join(unk_ids)}.",
                    claim_type="DECISION_SYNTHESIS",
                    referenced_node_ids=[n.node_id for n in unknown_evals if n],
                )
            )
        elif status == "ELIGIBLE":
            claims.append(
                ExplanationClaim(
                    claim_id=f"CLM-{decision_node_id}-{claim_counter}",
                    claim_text="Patient is ELIGIBLE because all evaluated criteria deterministically satisfied PASS.",
                    claim_type="DECISION_SYNTHESIS",
                    referenced_node_ids=[n.node_id for n in pass_evals if n],
                )
            )

        # Assemble full text
        text_lines = [
            f"Trial Eligibility Decision: {status}.",
            f"Summary: Evaluated {len(eval_nodes)} criteria ({len(pass_evals)} PASS, {len(fail_evals)} FAIL, {len(unknown_evals)} UNKNOWN)."
        ]
        if fail_evals:
            fail_descs = [f"{n.properties.get('criterion_id', n.node_id)}: {n.properties.get('reasoning', '')}" for n in fail_evals if n]
            text_lines.append(f"Disqualifying criteria: {'; '.join(fail_descs)}.")
        if unknown_evals:
            unk_descs = [f"{n.properties.get('criterion_id', n.node_id)}: {n.properties.get('reasoning', '')}" for n in unknown_evals if n]
            text_lines.append(f"Unresolved criteria requiring review: {'; '.join(unk_descs)}.")
        if summary:
            text_lines.append(f"Clinical synthesis: {summary}")

        exp_id = explanation_id or f"EXP-{decision_node_id}"

        return StructuredExplanation(
            explanation_id=exp_id,
            explanation_type=ExplanationType.TRIAL_DECISION_EXPLANATION,
            target_node_id=decision_node_id,
            decision_reference=status,
            criterion_references=[n.node_id for n in eval_nodes if n],
            claims=claims,
            explanation_text=" ".join(text_lines),
            generation_method="deterministic_rule_based",
            is_graph_grounded=True,
        )

    @classmethod
    def explain_review_resolution(
        cls,
        graph: EvidenceGraph,
        resolution_node_id: str,
        explanation_id: Optional[str] = None
    ) -> StructuredExplanation:
        """
        Synthesizes an explanation for a human review adjudication, contrasting
        the reviewer's resolution with the preserved original machine decision.
        """
        res_node = graph.get_node(resolution_node_id)
        if not res_node or res_node.node_type != NodeType.REVIEW_RESOLUTION:
            raise ValueError(f"Node '{resolution_node_id}' is not a valid REVIEW_RESOLUTION node.")

        decision = res_node.properties.get("decision", "")
        reviewer_id = res_node.properties.get("reviewer_id", "")
        rationale = res_node.properties.get("rationale", "")
        orig_machine = res_node.properties.get("original_machine_output", {})

        # Supporting evidence for resolution
        supp_edges = [e for e in graph.get_outgoing_edges(resolution_node_id) if e.edge_type == EdgeType.SUPPORTED_BY]
        supp_nodes = [graph.get_node(e.target_id) for e in supp_edges if graph.get_node(e.target_id)]

        claims: List[ExplanationClaim] = []
        claim_counter = 1

        claims.append(
            ExplanationClaim(
                claim_id=f"CLM-{resolution_node_id}-{claim_counter}",
                claim_text=f"Reviewer {reviewer_id} rendered decision: {decision}.",
                claim_type="REVIEW_OVERRIDE",
                referenced_node_ids=[res_node.node_id],
            )
        )
        claim_counter += 1

        if rationale:
            claims.append(
                ExplanationClaim(
                    claim_id=f"CLM-{resolution_node_id}-{claim_counter}",
                    claim_text=f"Reviewer rationale: {rationale}",
                    claim_type="REVIEW_OVERRIDE",
                    referenced_node_ids=[res_node.node_id],
                )
            )
            claim_counter += 1

        if orig_machine:
            orig_status = orig_machine.get("overall_status") or orig_machine.get("status", "UNKNOWN")
            claims.append(
                ExplanationClaim(
                    claim_id=f"CLM-{resolution_node_id}-{claim_counter}",
                    claim_text=f"Original machine reasoning output '{orig_status}' was preserved immutably.",
                    claim_type="DECISION_SYNTHESIS",
                    referenced_node_ids=[res_node.node_id],
                )
            )
            claim_counter += 1

        text_lines = [
            f"Human Review Adjudication: Decision is {decision} by reviewer {reviewer_id}.",
            f"Clinical rationale: {rationale}.",
            f"Original machine decision ({orig_machine.get('overall_status', 'UNKNOWN')}) remains preserved in audit trail."
        ]
        if supp_nodes:
            supp_labels = [n.label for n in supp_nodes if n]
            text_lines.append(f"Citing external/clinical evidence: {'; '.join(supp_labels)}.")

        exp_id = explanation_id or f"EXP-{resolution_node_id}"

        return StructuredExplanation(
            explanation_id=exp_id,
            explanation_type=ExplanationType.REVIEW_EXPLANATION,
            target_node_id=resolution_node_id,
            decision_reference=decision,
            supporting_evidence_references=[n.node_id for n in supp_nodes if n],
            claims=claims,
            explanation_text=" ".join(text_lines),
            generation_method="deterministic_rule_based",
            is_graph_grounded=True,
        )
