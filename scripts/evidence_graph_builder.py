"""
MedMatch Canonical Evidence Graph Builder.
Phase 10: Explainability & Evidence Graph Foundation.

Constructs strongly-typed, verifiable EvidenceGraph instances from upstream
Phase 3 (Document Intelligence), Phase 4 (Patient Profile), Phase 5 (Retrieval),
Phase 6 (Eligibility Reasoning), and Phase 9 (Uncertainty & Review) contracts.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional

try:
    from scripts.evidence_graph_schema import (
        EdgeType,
        EvidenceGraph,
        EvidenceGraphEdge,
        EvidenceGraphNode,
        NodeProvenance,
        NodeType,
    )
except ImportError:
    from evidence_graph_schema import (
        EdgeType,
        EvidenceGraph,
        EvidenceGraphEdge,
        EvidenceGraphNode,
        NodeProvenance,
        NodeType,
    )


class EvidenceGraphBuilder:
    """
    Deterministic builder assembling end-to-end evidence graphs.
    """

    def __init__(self, graph_id: str, trial_id: str, patient_id: str):
        self.graph_id = graph_id
        self.trial_id = trial_id
        self.patient_id = patient_id
        self.graph = EvidenceGraph(
            graph_id=graph_id,
            trial_id=trial_id,
            patient_id=patient_id,
        )
        self._edge_counter = 0

        # Ensure patient and trial root nodes are initialized
        self._init_patient_node()
        self._init_trial_node()

    def _next_edge_id(self, prefix: str = "edge") -> str:
        self._edge_counter += 1
        return f"{self.graph_id}-{prefix}-{self._edge_counter:04d}"

    def _init_patient_node(self) -> None:
        patient_node = EvidenceGraphNode(
            node_id=f"PAT-{self.patient_id}",
            node_type=NodeType.PATIENT,
            label=f"Patient {self.patient_id}",
            properties={"patient_id": self.patient_id},
        )
        self.graph.add_node(patient_node)

    def _init_trial_node(self) -> None:
        trial_node = EvidenceGraphNode(
            node_id=f"TRIAL-{self.trial_id}",
            node_type=NodeType.TRIAL,
            label=f"Trial {self.trial_id}",
            properties={"trial_id": self.trial_id},
        )
        self.graph.add_node(trial_node)

    def add_source_document(
        self,
        document_id: str,
        title: str,
        doc_type: str = "clinical_note",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Adds a SOURCE_DOCUMENT node."""
        node_id = f"DOC-{document_id}" if not document_id.startswith("DOC-") else document_id
        if node_id not in self.graph.nodes:
            self.graph.add_node(
                EvidenceGraphNode(
                    node_id=node_id,
                    node_type=NodeType.SOURCE_DOCUMENT,
                    label=title,
                    properties={
                        "document_id": document_id,
                        "document_type": doc_type,
                    },
                    metadata=metadata or {},
                )
            )
        return node_id

    def add_source_fragment(
        self,
        fragment_id: str,
        document_id: str,
        text: str,
        section: Optional[str] = None,
        start_char: int = -1,
        end_char: int = -1,
        page_number: Optional[int] = None
    ) -> str:
        """Adds a SOURCE_FRAGMENT node and links BELONGS_TO to its SOURCE_DOCUMENT."""
        doc_node_id = self.add_source_document(document_id, title=f"Document {document_id}")
        node_id = f"FRAG-{fragment_id}" if not fragment_id.startswith("FRAG-") else fragment_id
        if node_id not in self.graph.nodes:
            prov = NodeProvenance(
                source_id=fragment_id,
                document_id=document_id,
                section=section,
                start_char=start_char,
                end_char=end_char,
                page_number=page_number,
            )
            self.graph.add_node(
                EvidenceGraphNode(
                    node_id=node_id,
                    node_type=NodeType.SOURCE_FRAGMENT,
                    label=text[:60] + ("..." if len(text) > 60 else ""),
                    properties={"text": text},
                    provenance=prov,
                )
            )
            # Edge: FRAG -> BELONGS_TO -> DOC
            self.graph.add_edge(
                EvidenceGraphEdge(
                    edge_id=self._next_edge_id("belongs_to"),
                    source_id=node_id,
                    target_id=doc_node_id,
                    edge_type=EdgeType.BELONGS_TO,
                )
            )
        return node_id

    def add_patient_fact(
        self,
        fact_id: str,
        concept: str,
        value: Any,
        assertion: str = "PRESENT",
        source_fragment_id: Optional[str] = None,
        temporality: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Adds a PATIENT_FACT node, links from PATIENT via HAS_FACT, and to SOURCE_FRAGMENT."""
        node_id = f"FACT-{fact_id}" if not fact_id.startswith("FACT-") else fact_id
        if node_id not in self.graph.nodes:
            self.graph.add_node(
                EvidenceGraphNode(
                    node_id=node_id,
                    node_type=NodeType.PATIENT_FACT,
                    label=f"{concept}: {value}",
                    properties={
                        "fact_id": fact_id,
                        "concept": concept,
                        "value": value,
                        "assertion": assertion,
                        "temporality": temporality,
                    },
                    metadata=metadata or {},
                )
            )
            # Edge: PATIENT -> HAS_FACT -> PATIENT_FACT
            self.graph.add_edge(
                EvidenceGraphEdge(
                    edge_id=self._next_edge_id("has_fact"),
                    source_id=f"PAT-{self.patient_id}",
                    target_id=node_id,
                    edge_type=EdgeType.HAS_FACT,
                )
            )
            # Link to source fragment if provided
            if source_fragment_id:
                frag_node_id = f"FRAG-{source_fragment_id}" if not source_fragment_id.startswith("FRAG-") else source_fragment_id
                if frag_node_id in self.graph.nodes:
                    self.graph.add_edge(
                        EvidenceGraphEdge(
                            edge_id=self._next_edge_id("derived_from"),
                            source_id=node_id,
                            target_id=frag_node_id,
                            edge_type=EdgeType.DERIVED_FROM,
                        )
                    )
        return node_id

    def add_trial_criterion(
        self,
        criterion_id: str,
        criterion_type: str,
        text: str,
        domain: str = "other",
        source_fragment_id: Optional[str] = None
    ) -> str:
        """Adds a TRIAL_CRITERION node and links from TRIAL via HAS_CRITERION."""
        node_id = f"CRIT-{criterion_id}" if not criterion_id.startswith("CRIT-") else criterion_id
        if node_id not in self.graph.nodes:
            self.graph.add_node(
                EvidenceGraphNode(
                    node_id=node_id,
                    node_type=NodeType.TRIAL_CRITERION,
                    label=f"[{criterion_type.upper()}] {text[:50]}...",
                    properties={
                        "criterion_id": criterion_id,
                        "criterion_type": criterion_type,
                        "criterion_text": text,
                        "domain": domain,
                    },
                )
            )
            # Edge: TRIAL -> HAS_CRITERION -> TRIAL_CRITERION
            self.graph.add_edge(
                EvidenceGraphEdge(
                    edge_id=self._next_edge_id("has_criterion"),
                    source_id=f"TRIAL-{self.trial_id}",
                    target_id=node_id,
                    edge_type=EdgeType.HAS_CRITERION,
                )
            )
            if source_fragment_id:
                frag_node_id = f"FRAG-{source_fragment_id}" if not source_fragment_id.startswith("FRAG-") else source_fragment_id
                if frag_node_id in self.graph.nodes:
                    self.graph.add_edge(
                        EvidenceGraphEdge(
                            edge_id=self._next_edge_id("crit_derived_from"),
                            source_id=node_id,
                            target_id=frag_node_id,
                            edge_type=EdgeType.DERIVED_FROM,
                        )
                    )
        return node_id

    def add_retrieval_result(
        self,
        retrieval_id: str,
        criterion_id: str,
        rank: int,
        score: float,
        method: str,
        source_doc_id: Optional[str] = None
    ) -> str:
        """Adds a RETRIEVAL_RESULT node and links to TRIAL_CRITERION and source."""
        node_id = f"RET-{retrieval_id}" if not retrieval_id.startswith("RET-") else retrieval_id
        crit_node_id = f"CRIT-{criterion_id}" if not criterion_id.startswith("CRIT-") else criterion_id
        if node_id not in self.graph.nodes:
            prov = NodeProvenance(
                source_id=retrieval_id,
                retrieval_method=method,
                retrieval_rank=rank,
                retrieval_score=score,
            )
            self.graph.add_node(
                EvidenceGraphNode(
                    node_id=node_id,
                    node_type=NodeType.RETRIEVAL_RESULT,
                    label=f"Rank {rank} ({method}, score: {score:.3f})",
                    properties={
                        "retrieval_id": retrieval_id,
                        "rank": rank,
                        "score": score,
                        "method": method,
                    },
                    provenance=prov,
                )
            )
            # Edge: RETRIEVAL_RESULT -> RETRIEVED_CRITERION -> TRIAL_CRITERION
            if crit_node_id in self.graph.nodes:
                self.graph.add_edge(
                    EvidenceGraphEdge(
                        edge_id=self._next_edge_id("retrieved_criterion"),
                        source_id=node_id,
                        target_id=crit_node_id,
                        edge_type=EdgeType.RETRIEVED_CRITERION,
                        weight=score,
                    )
                )
            # Edge: RETRIEVAL_RESULT -> RETRIEVED_FROM -> TRIAL / DOC
            target_source = f"DOC-{source_doc_id}" if (source_doc_id and f"DOC-{source_doc_id}" in self.graph.nodes) else f"TRIAL-{self.trial_id}"
            self.graph.add_edge(
                EvidenceGraphEdge(
                    edge_id=self._next_edge_id("retrieved_from"),
                    source_id=node_id,
                    target_id=target_source,
                    edge_type=EdgeType.RETRIEVED_FROM,
                )
            )
        return node_id

    def add_criterion_evaluation(
        self,
        eval_id: str,
        criterion_id: str,
        status: str,
        reasoning: str,
        supporting_fact_ids: Optional[List[str]] = None,
        contradicting_fact_ids: Optional[List[str]] = None,
        supporting_fragment_ids: Optional[List[str]] = None,
        contradicting_fragment_ids: Optional[List[str]] = None,
        contextualizing_fact_ids: Optional[List[str]] = None,
    ) -> str:
        """
        Adds CRITERION_EVALUATION node, links from TRIAL_CRITERION via EVALUATED_BY,
        and links evidence via SUPPORTS, CONTRADICTS, or CONTEXTUALIZES.
        """
        node_id = f"EVAL-{eval_id}" if not eval_id.startswith("EVAL-") else eval_id
        crit_node_id = f"CRIT-{criterion_id}" if not criterion_id.startswith("CRIT-") else criterion_id
        if node_id not in self.graph.nodes:
            self.graph.add_node(
                EvidenceGraphNode(
                    node_id=node_id,
                    node_type=NodeType.CRITERION_EVALUATION,
                    label=f"Eval {criterion_id}: {status}",
                    properties={
                        "evaluation_id": eval_id,
                        "criterion_id": criterion_id,
                        "status": status,
                        "reasoning": reasoning,
                    },
                )
            )
            # Edge: TRIAL_CRITERION -> EVALUATED_BY -> CRITERION_EVALUATION
            if crit_node_id in self.graph.nodes:
                self.graph.add_edge(
                    EvidenceGraphEdge(
                        edge_id=self._next_edge_id("evaluated_by"),
                        source_id=crit_node_id,
                        target_id=node_id,
                        edge_type=EdgeType.EVALUATED_BY,
                    )
                )

            # Supporting facts
            for fid in (supporting_fact_ids or []):
                fnid = f"FACT-{fid}" if not fid.startswith("FACT-") else fid
                if fnid in self.graph.nodes:
                    self.graph.add_edge(
                        EvidenceGraphEdge(
                            edge_id=self._next_edge_id("supports"),
                            source_id=fnid,
                            target_id=node_id,
                            edge_type=EdgeType.SUPPORTS,
                        )
                    )

            # Contradicting facts
            for fid in (contradicting_fact_ids or []):
                fnid = f"FACT-{fid}" if not fid.startswith("FACT-") else fid
                if fnid in self.graph.nodes:
                    self.graph.add_edge(
                        EvidenceGraphEdge(
                            edge_id=self._next_edge_id("contradicts"),
                            source_id=fnid,
                            target_id=node_id,
                            edge_type=EdgeType.CONTRADICTS,
                        )
                    )

            # Supporting fragments
            for frid in (supporting_fragment_ids or []):
                frnid = f"FRAG-{frid}" if not frid.startswith("FRAG-") else frid
                if frnid in self.graph.nodes:
                    self.graph.add_edge(
                        EvidenceGraphEdge(
                            edge_id=self._next_edge_id("frag_supports"),
                            source_id=frnid,
                            target_id=node_id,
                            edge_type=EdgeType.SUPPORTS,
                        )
                    )

            # Contradicting fragments
            for frid in (contradicting_fragment_ids or []):
                frnid = f"FRAG-{frid}" if not frid.startswith("FRAG-") else frid
                if frnid in self.graph.nodes:
                    self.graph.add_edge(
                        EvidenceGraphEdge(
                            edge_id=self._next_edge_id("frag_contradicts"),
                            source_id=frnid,
                            target_id=node_id,
                            edge_type=EdgeType.CONTRADICTS,
                        )
                    )

            # Contextualizing facts
            for fid in (contextualizing_fact_ids or []):
                fnid = f"FACT-{fid}" if not fid.startswith("FACT-") else fid
                if fnid in self.graph.nodes:
                    self.graph.add_edge(
                        EvidenceGraphEdge(
                            edge_id=self._next_edge_id("contextualizes"),
                            source_id=fnid,
                            target_id=node_id,
                            edge_type=EdgeType.CONTEXTUALIZES,
                        )
                    )
        return node_id

    def add_eligibility_decision(
        self,
        decision_id: str,
        status: str,
        clinical_summary: str,
        contributing_eval_ids: List[str]
    ) -> str:
        """Adds ELIGIBILITY_DECISION node and links CONTRIBUTES_TO from evaluations."""
        node_id = f"DEC-{decision_id}" if not decision_id.startswith("DEC-") else decision_id
        if node_id not in self.graph.nodes:
            self.graph.add_node(
                EvidenceGraphNode(
                    node_id=node_id,
                    node_type=NodeType.ELIGIBILITY_DECISION,
                    label=f"Decision: {status}",
                    properties={
                        "decision_id": decision_id,
                        "status": status,
                        "clinical_summary": clinical_summary,
                    },
                )
            )
            for evid in contributing_eval_ids:
                evnid = f"EVAL-{evid}" if not evid.startswith("EVAL-") else evid
                if evnid in self.graph.nodes:
                    self.graph.add_edge(
                        EvidenceGraphEdge(
                            edge_id=self._next_edge_id("contributes_to"),
                            source_id=evnid,
                            target_id=node_id,
                            edge_type=EdgeType.CONTRIBUTES_TO,
                        )
                    )
        return node_id

    def add_uncertainty(
        self,
        uncertainty_id: str,
        uncertainty_type: str,
        severity: str,
        description: str,
        affected_eval_id: Optional[str] = None,
        affected_fact_id: Optional[str] = None
    ) -> str:
        """Adds UNCERTAINTY node and links from evaluation or fact via HAS_UNCERTAINTY."""
        node_id = f"UNC-{uncertainty_id}" if not uncertainty_id.startswith("UNC-") else uncertainty_id
        if node_id not in self.graph.nodes:
            self.graph.add_node(
                EvidenceGraphNode(
                    node_id=node_id,
                    node_type=NodeType.UNCERTAINTY,
                    label=f"Uncertainty: {uncertainty_type} ({severity})",
                    properties={
                        "uncertainty_id": uncertainty_id,
                        "uncertainty_type": uncertainty_type,
                        "severity": severity,
                        "description": description,
                    },
                )
            )
            if affected_eval_id:
                enid = f"EVAL-{affected_eval_id}" if not affected_eval_id.startswith("EVAL-") else affected_eval_id
                if enid in self.graph.nodes:
                    self.graph.add_edge(
                        EvidenceGraphEdge(
                            edge_id=self._next_edge_id("has_uncertainty"),
                            source_id=enid,
                            target_id=node_id,
                            edge_type=EdgeType.HAS_UNCERTAINTY,
                        )
                    )
            if affected_fact_id:
                fnid = f"FACT-{affected_fact_id}" if not affected_fact_id.startswith("FACT-") else affected_fact_id
                if fnid in self.graph.nodes:
                    self.graph.add_edge(
                        EvidenceGraphEdge(
                            edge_id=self._next_edge_id("fact_has_uncertainty"),
                            source_id=fnid,
                            target_id=node_id,
                            edge_type=EdgeType.HAS_UNCERTAINTY,
                        )
                    )
        return node_id

    def add_review(
        self,
        review_id: str,
        status: str,
        priority: str,
        uncertainty_id: str
    ) -> str:
        """Adds REVIEW node and links from UNCERTAINTY via TRIGGERS."""
        node_id = f"REV-{review_id}" if not review_id.startswith("REV-") else review_id
        unc_node_id = f"UNC-{uncertainty_id}" if not uncertainty_id.startswith("UNC-") else uncertainty_id
        if node_id not in self.graph.nodes:
            self.graph.add_node(
                EvidenceGraphNode(
                    node_id=node_id,
                    node_type=NodeType.REVIEW,
                    label=f"Review ({status}, Priority: {priority})",
                    properties={
                        "review_id": review_id,
                        "status": status,
                        "priority": priority,
                    },
                )
            )
            if unc_node_id in self.graph.nodes:
                self.graph.add_edge(
                    EvidenceGraphEdge(
                        edge_id=self._next_edge_id("triggers_review"),
                        source_id=unc_node_id,
                        target_id=node_id,
                        edge_type=EdgeType.TRIGGERS,
                    )
                )
        return node_id

    def add_review_resolution(
        self,
        resolution_id: str,
        review_id: str,
        reviewer_id: str,
        decision: str,
        rationale: str,
        original_machine_output: Dict[str, Any],
        evidence_fragment_ids: Optional[List[str]] = None
    ) -> str:
        """
        Adds REVIEW_RESOLUTION node, links from REVIEW via RESOLVED_BY,
        preserves original_machine_output immutably, and links supporting evidence.
        """
        node_id = f"RES-{resolution_id}" if not resolution_id.startswith("RES-") else resolution_id
        rev_node_id = f"REV-{review_id}" if not review_id.startswith("REV-") else review_id
        if node_id not in self.graph.nodes:
            self.graph.add_node(
                EvidenceGraphNode(
                    node_id=node_id,
                    node_type=NodeType.REVIEW_RESOLUTION,
                    label=f"Resolution: {decision} by {reviewer_id}",
                    properties={
                        "resolution_id": resolution_id,
                        "reviewer_id": reviewer_id,
                        "decision": decision,
                        "rationale": rationale,
                        "original_machine_output": original_machine_output,
                    },
                )
            )
            if rev_node_id in self.graph.nodes:
                self.graph.add_edge(
                    EvidenceGraphEdge(
                        edge_id=self._next_edge_id("resolved_by"),
                        source_id=rev_node_id,
                        target_id=node_id,
                        edge_type=EdgeType.RESOLVED_BY,
                    )
                )

            for frid in (evidence_fragment_ids or []):
                frnid = f"FRAG-{frid}" if not frid.startswith("FRAG-") else frid
                if frnid in self.graph.nodes:
                    self.graph.add_edge(
                        EvidenceGraphEdge(
                            edge_id=self._next_edge_id("resolution_evidence"),
                            source_id=node_id,
                            target_id=frnid,
                            edge_type=EdgeType.SUPPORTED_BY,
                        )
                    )
        return node_id

    def build(self) -> EvidenceGraph:
        """Returns the completed EvidenceGraph."""
        return self.graph
