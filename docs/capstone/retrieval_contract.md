# MedMatch Capstone — Retrieval Contract Specification

## 1. Executive Summary & Core Principle

The retrieval contract defines a stable, decoupled boundary between patient representation and downstream clinical eligibility reasoning.

> [!IMPORTANT]
> **Core Architectural Principle:**
> The retrieval engine's sole responsibility is **evidence discovery**.
>
> The retrieval layer must return candidate clinical trials and representative criteria along with relevance scores and provenance references. **It does NOT evaluate eligibility, decide inclusion/exclusion verdicts, or make clinical enrollment determinations.**

---

## 2. Canonical Retrieval Request (`RetrievalRequest`)

The retrieval request encapsulates all parameters necessary for reproducible, tenant-isolated candidate discovery across all experimental modes (E0 to E4):

```python
class RetrievalRequest(BaseModel):
    request_id: str = Field(..., description="Unique request identifier")
    tenant_id: Optional[str] = Field(default=None, description="Hospital or tenant UUID for multi-tenant isolation")
    query_text: str = Field(..., min_length=1, description="Raw patient clinical note or query narrative")
    structured_query: Optional[Dict[str, Any]] = Field(
        default=None, description="Extracted clinical concepts/facts (e.g., from PatientClinicalProfile)"
    )
    top_k: int = Field(default=10, ge=1, le=100, description="Number of candidate trials to retrieve")
    filters: Optional[Dict[str, Any]] = Field(
        default=None, description="Hard metadata filters (e.g., phase, active status, trial condition)"
    )
    retrieval_strategy: str = Field(
        default="dense_baseline", description="'dense_baseline', 'lexical_bm25', 'hybrid_rrf', 'hybrid_reranked'"
    )
    experiment_id: str = Field(default="E0", description="Experiment matrix identifier: E0, E1, E2, E3, E4")
```

---

## 3. Canonical Retrieval Result (`RetrievalResult`)

Every item returned by the retrieval engine contains exact ranking, score provenance, and evidence pointers:

```python
class RetrievalResult(BaseModel):
    trial_id: str = Field(..., description="Canonical clinical trial accession (NCT ID or UUID)")
    criterion_id: Optional[str] = Field(default=None, description="Specific matching criterion ID if applicable")
    rank: int = Field(..., ge=1, description="1-based ordinal rank in retrieved candidate list")
    score: float = Field(..., description="Strategy-specific relevance score (cosine similarity, BM25, RRF score)")
    raw_distance: Optional[float] = Field(default=None, description="Original pgvector distance if dense retrieval")
    retrieval_method: str = Field(..., description="Method used: 'dense', 'lexical', 'hybrid_rrf', 'cross_encoder'")
    source_reference: Optional[str] = Field(default=None, description="Document or section provenance reference")
    criterion_text: Optional[str] = Field(default=None, description="Text snippet of matching criterion")
    trial_title: Optional[str] = Field(default=None, description="Official title of candidate clinical trial")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Component scores and diagnostic metadata")
```

---

## 4. Canonical Retrieval Response (`RetrievalResponse`)

```python
class RetrievalResponse(BaseModel):
    request_id: str = Field(...)
    experiment_id: str = Field(...)
    retrieval_strategy: str = Field(...)
    total_candidates_evaluated: int = Field(..., ge=0)
    returned_count: int = Field(..., ge=0)
    results: List[RetrievalResult] = Field(default_factory=list)
    execution_time_ms: float = Field(..., ge=0.0)
    timestamp: str = Field(..., description="ISO-8601 UTC timestamp")
```

---

## 5. Downstream Contract Guarantees

1. **Deterministic Tie-Breaking:** If two candidates produce identical retrieval scores, ordering is deterministically resolved using `trial_id ASC`, followed by `criterion_id ASC`.
2. **Tenant Boundary Invariance:** Under no circumstances will a candidate trial belonging to `hospital_A` be returned in a response for `hospital_B`.
3. **Evidence Traceability:** Every candidate references an existing `trial_id` and, where applicable, a `criterion_id`, enabling downstream verification against canonical protocol documents.
