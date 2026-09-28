"""
MedMatch Canonical Retrieval Engine Schemas & Contracts.
Phase 5: Retrieval Engine.

Defines Pydantic models for:
- RetrievalRequest (query representation, top-k, tenant_id, filters, experiment_id)
- RetrievalResult (trial_id, criterion_id, rank, score, method, provenance)
- RetrievalResponse (execution metadata, ranked results list)
- CandidateTrialRecord (internal trial representation for indexing/searching)
"""

from __future__ import annotations

import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class RetrievalStrategy(str, Enum):
    DENSE_BASELINE = "dense_baseline"          # E0: Current pgvector dense retrieval
    DENSE_STRUCTURED = "dense_structured"      # E1: Dense retrieval with structured query profile
    LEXICAL_BM25 = "lexical_bm25"              # E2: Full-text / BM25 lexical retrieval
    HYBRID_RRF = "hybrid_rrf"                  # E3: Reciprocal Rank Fusion of dense + lexical
    HYBRID_RERANKED = "hybrid_reranked"        # E4: Hybrid retrieval + cross-encoder reranking


class CandidateTrialRecord(BaseModel):
    """
    Representation of a clinical trial in the searchable candidate pool.
    """
    trial_id: str = Field(..., description="Unique trial accession or UUID")
    hospital_id: Optional[str] = Field(default=None, description="Owning hospital/tenant UUID")
    title: str = Field(..., description="Official clinical trial title")
    condition: Optional[str] = Field(default=None, description="Primary indication / disease")
    phase: Optional[str] = Field(default=None, description="Clinical trial phase (e.g., Phase 1/2)")
    status: Optional[str] = Field(default="RECRUITING", description="Recruiting status")
    brief_summary: Optional[str] = Field(default=None, description="Brief trial narrative summary")
    criteria: List[Dict[str, Any]] = Field(default_factory=list, description="Associated criteria records")
    embedding: Optional[List[float]] = Field(default=None, description="384-d dense embedding vector")


class RetrievalRequest(BaseModel):
    """
    Canonical retrieval query contract.
    """
    request_id: str = Field(..., description="Unique request identifier")
    tenant_id: Optional[str] = Field(default=None, description="Hospital or tenant UUID for multi-tenant isolation")
    query_text: str = Field(..., min_length=1, description="Raw patient clinical note or query narrative")
    structured_query: Optional[Dict[str, Any]] = Field(
        default=None, description="Extracted clinical concepts/facts (e.g. from PatientClinicalProfile)"
    )
    top_k: int = Field(default=10, ge=1, le=100, description="Number of candidate trials to retrieve")
    filters: Optional[Dict[str, Any]] = Field(
        default=None, description="Hard metadata filters (e.g. phase, active status, condition)"
    )
    retrieval_strategy: RetrievalStrategy = Field(
        default=RetrievalStrategy.DENSE_BASELINE, description="Configured retrieval strategy"
    )
    experiment_id: str = Field(default="E0", description="Experiment matrix identifier: E0, E1, E2, E3, E4")


class RetrievalResult(BaseModel):
    """
    Canonical single candidate result returned by any retrieval strategy.
    """
    trial_id: str = Field(..., description="Canonical clinical trial accession (NCT ID or UUID)")
    criterion_id: Optional[str] = Field(default=None, description="Specific matching criterion ID if applicable")
    rank: int = Field(..., ge=1, description="1-based ordinal rank in retrieved candidate list")
    score: float = Field(..., description="Strategy-specific relevance score")
    raw_distance: Optional[float] = Field(default=None, description="Original pgvector distance if dense retrieval")
    retrieval_method: str = Field(..., description="Method: 'dense', 'lexical', 'hybrid_rrf', 'reranked'")
    source_reference: Optional[str] = Field(default=None, description="Document or section provenance reference")
    criterion_text: Optional[str] = Field(default=None, description="Text snippet of matching criterion")
    trial_title: Optional[str] = Field(default=None, description="Official title of candidate clinical trial")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Component scores and diagnostic metadata")


class RetrievalResponse(BaseModel):
    """
    Canonical retrieval response contract.
    """
    request_id: str = Field(...)
    experiment_id: str = Field(...)
    retrieval_strategy: RetrievalStrategy = Field(...)
    total_candidates_evaluated: int = Field(..., ge=0)
    returned_count: int = Field(..., ge=0)
    results: List[RetrievalResult] = Field(default_factory=list)
    execution_time_ms: float = Field(..., ge=0.0)
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    @model_validator(mode="after")
    def validate_returned_count(self) -> RetrievalResponse:
        if len(self.results) != self.returned_count:
            self.returned_count = len(self.results)
        return self
