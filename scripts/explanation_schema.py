"""
MedMatch Canonical Explanation Schemas & Contracts.
Phase 10: Explainability & Evidence Graph Foundation.

Defines strongly-typed Pydantic models for:
- ExplanationType: Taxonomic categories of clinical explanations
- ExplanationClaim: Fine-grained atomic proposition mapped to graph evidence
- StructuredExplanation: Canonical, graph-grounded explanation payload
"""

from __future__ import annotations

import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ExplanationType(str, Enum):
    """
    Taxonomic scope of a generated clinical decision explanation.
    """
    CRITERION_EXPLANATION = "CRITERION_EXPLANATION"         # Explains a single inclusion/exclusion evaluation
    TRIAL_DECISION_EXPLANATION = "TRIAL_DECISION_EXPLANATION" # Explains aggregated trial eligibility verdict
    UNCERTAINTY_EXPLANATION = "UNCERTAINTY_EXPLANATION"       # Explains epistemic or clinical uncertainty origin
    REVIEW_EXPLANATION = "REVIEW_EXPLANATION"                 # Explains human review routing, priority, or override


class ExplanationClaim(BaseModel):
    """
    Atomic factual or logical assertion within an explanation text.
    Must map to verifiable nodes or edges in the EvidenceGraph.
    """
    model_config = ConfigDict(extra="forbid")

    claim_id: str = Field(..., min_length=1, description="Unique claim identifier, e.g. 'CLM-001'")
    claim_text: str = Field(..., min_length=1, description="Verbatim text of the proposition")
    claim_type: str = Field(
        default="FACT_ASSERTION",
        description="FACT_ASSERTION, CRITERION_REQUIREMENT, EVALUATION_RESULT, DECISION_SYNTHESIS, UNCERTAINTY_STATEMENT, REVIEW_OVERRIDE"
    )
    referenced_node_ids: List[str] = Field(
        default_factory=list,
        description="IDs of EvidenceGraph nodes grounding this claim"
    )
    is_supported_by_graph: bool = Field(
        default=True,
        description="True if all referenced nodes and relations exist in the graph"
    )


class StructuredExplanation(BaseModel):
    """
    Canonical, graph-grounded explanation container.
    """
    model_config = ConfigDict(extra="forbid")

    explanation_id: str = Field(..., min_length=1, description="Unique explanation identifier")
    explanation_type: ExplanationType = Field(..., description="Scope of the explanation")
    target_node_id: str = Field(..., min_length=1, description="Graph node ID being explained (eval, decision, uncertainty, or review)")
    decision_reference: Optional[str] = Field(default=None, description="Target eligibility decision status if applicable")
    criterion_references: List[str] = Field(default_factory=list, description="Referenced TRIAL_CRITERION node IDs")
    supporting_evidence_references: List[str] = Field(
        default_factory=list,
        description="Referenced PATIENT_FACT or SOURCE_FRAGMENT node IDs providing support"
    )
    contradictory_evidence_references: List[str] = Field(
        default_factory=list,
        description="Referenced PATIENT_FACT or SOURCE_FRAGMENT node IDs indicating contradiction"
    )
    uncertainty_references: List[str] = Field(
        default_factory=list,
        description="Referenced UNCERTAINTY node IDs if explaining an uncertain/unknown state"
    )
    claims: List[ExplanationClaim] = Field(
        default_factory=list,
        description="Fine-grained atomic claims comprising the explanation"
    )
    explanation_text: str = Field(..., min_length=3, description="Human-readable synthesis text")
    generation_method: str = Field(
        default="deterministic_rule_based",
        description="Method identifier; must be deterministic for research baseline"
    )
    is_graph_grounded: bool = Field(
        default=True,
        description="True only if verified against the canonical EvidenceGraph"
    )
    created_at: str = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat(),
        description="ISO-8601 timestamp"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional provenance or audit annotations")
