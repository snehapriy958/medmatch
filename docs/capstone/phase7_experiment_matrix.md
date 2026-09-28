# MedMatch Capstone — Phase 7: Experiment Matrix & Ablation Design

**Document Version:** `1.0.0`  
**Phase:** 7 — RAG vs. Non-RAG Experimental Evaluation  
**Date:** September 2026  
**Status:** Canonical Experiment Matrix  

---

## 1. Experimental Roadmap & Architecture Alignment

The Phase 7 experimental matrix builds directly on the retrieval baselines established in Phase 5 (E0–E4) and the reasoning models established in Phase 6. It investigates the progressive contribution of retrieval evidence and hybrid fusion to eligibility reasoning accuracy.

```text
+------------------------------------------------------------------------------------------------------------------------------------+
|                                                  PHASE 7 REASONING EXPERIMENT MATRIX                                               |
+----+----------------------+--------------------+--------------------+-----------------------+---------------------+----------------+
| ID | Experiment Name      | Retrieval Engine   | Candidate Pool     | Reasoning Input       | Aggregation         | Status         |
+----+----------------------+--------------------+--------------------+-----------------------+---------------------+----------------+
| E5 | Non-RAG Baseline     | NONE               | Task Criteria Only | Patient Facts + Note  | Deterministic Pure  | IMPLEMENTED    |
|    |                      | (No Retrieval)     | (No Passages)      | (No Retrieved Text)   | Programmatic (P6)   | (RUN PENDING)  |
+----+----------------------+--------------------+--------------------+-----------------------+---------------------+----------------+
| E6 | Dense-RAG            | Phase 5 Dense      | Top-5 Trials       | Patient Facts +       | Deterministic Pure  | IMPLEMENTED    |
|    |                      | (all-MiniLM-L6-v2) | pgvector Cosine    | Dense Retrieved Text  | Programmatic (P6)   | (RUN PENDING)  |
+----+----------------------+--------------------+--------------------+-----------------------+---------------------+----------------+
| E7 | Hybrid-RAG           | Phase 5 Hybrid     | Top-5 Trials       | Patient Facts +       | Deterministic Pure  | IMPLEMENTED    |
|    |                      | (BM25 + Dense RRF) | RRF Score Fusion   | Hybrid Retrieved Text | Programmatic (P6)   | (RUN PENDING)  |
+----+----------------------+--------------------+--------------------+-----------------------+---------------------+----------------+
| E8 | RAG + Reranking      | Phase 5 Hybrid +   | Top-5 Trials from  | Patient Facts +       | Deterministic Pure  | IMPLEMENTED    |
|    |                      | Clinical Reranker  | Top-20 Pool        | Reranked Evidence     | Programmatic (P6)   | (RUN PENDING)  |
+----+----------------------+--------------------+--------------------+-----------------------+---------------------+----------------+
```

> [!IMPORTANT]
> **EMPIRICAL EXECUTION STATUS:**  
> Phase 7 now invokes the actual Phase 5 retrieval engine for RAG conditions (`DenseRetriever`, `HybridRRFRetriever`, `RerankingRetriever`). All four configurations (E5, E6, E7, E8) are architecturally implemented and verified via automated unit and contract tests in `scripts/` and `tests/rag_evaluation/`. The experiment remains unexecuted empirically because the validated research benchmark has not yet been ingested into the repository. The 6-patient Phase 2 synthetic fixture is NOT used as empirical benchmark evidence.

---

## 2. Detailed Configuration Specifications

### Experiment E5: Non-RAG Baseline
- **Independent Variable:** Complete absence of retrieval-augmented context passages.
- **Fixed Variables:** Model (`gemini-2.5-flash` / `rule_reasoner_v1`), temperature (`0.0`), patient facts ($D_P, E_P$), canonical criteria list ($C_T$), Phase 6 deterministic aggregator ($\Lambda$), Phase 6 validator.
- **Input:** Patient demographics, structured clinical facts, verbatim criteria descriptions to be judged.
- **Withheld Input:** All candidate trial brief summaries, retrieval rankings, similarity scores, and pre-selected evidence spans.
- **Expected Failure Mode:** Elevated `UNKNOWN` rate on criteria requiring protocol context; potential hallucination if ungrounded reasoning is permitted.

### Experiment E6: Dense-RAG
- **Independent Variable:** Inclusion of candidate trial passages retrieved via Phase 5 dense vector search (`DenseRetriever`, `sentence-transformers/all-MiniLM-L6-v2`, top-$k=5$).
- **Fixed Variables:** Identical to E5.
- **Input:** E5 input + dense retrieved trial summary text, section descriptions, and cosine similarity metadata.
- **Expected Contribution:** Improved resolution of domain concepts captured well by semantic embeddings.

### Experiment E7: Hybrid-RAG (Dense + Lexical BM25)
- **Independent Variable:** Candidate passages retrieved via Phase 5 Reciprocal Rank Fusion (`HybridRRFRetriever`, $k_{rrf}=60$) combining Okapi BM25 and dense cosine search.
- **Fixed Variables:** Identical to E5 and E6.
- **Input:** E5 input + hybrid retrieved passages, lexical token overlap metadata, and RRF rank metadata.
- **Expected Contribution:** Reduced retrieval blindness on exact clinical terms (e.g. `EGFR L858R`, `ECOG 1`, `creatinine < 1.5 mg/dL`).

### Experiment E8: RAG + Clinical Cross-Encoder Reranking
- **Independent Variable:** Top-5 passages re-ranked from an initial pool of 20 candidate trials via `ClinicalOverlapReranker`.
- **Fixed Variables:** Identical to E5, E6, and E7.
- **Input:** E5 input + reranked evidence passages prioritized by clinical concept alignment.
- **Expected Contribution:** Highest evidence precision and lowest false-positive criterion retrieval rate.

---

## 3. Systematic Ablation Dimensions

When benchmark evaluation is executed, five orthogonal ablation dimensions will isolate component effects:

1. **Ablation 1 (Retrieval Presence):** E5 (None) vs. E6 (Dense). Isolates the core value of RAG.
2. **Ablation 2 (Retrieval Strategy):** E6 (Dense) vs. E7 (Hybrid). Isolates the marginal value of sparse lexical search.
3. **Ablation 3 (Two-Stage Ranking):** E7 (Hybrid) vs. E8 (Hybrid + Reranking). Isolates second-stage candidate filtering.
4. **Ablation 4 (Evidence Grounding Policy):** Strict citation requirement vs. unconstrained model output. Evaluates hallucination reduction.
5. **Ablation 5 (Aggregation Mechanism):** Pure deterministic aggregation code vs. LLM end-to-end trial decision. Evaluates consistency and safety.

---

## 4. Controlled Variable Summary Table

| Experimental Factor | E5 (Non-RAG) | E6 (Dense-RAG) | E7 (Hybrid-RAG) | E8 (RAG + Rerank) |
| :--- | :---: | :---: | :---: | :---: |
| **Patient Profile** | Fixed | Fixed | Fixed | Fixed |
| **Criteria List** | Fixed | Fixed | Fixed | Fixed |
| **Reasoner Model** | Fixed | Fixed | Fixed | Fixed |
| **Temperature** | 0.0 | 0.0 | 0.0 | 0.0 |
| **Seed** | 42 | 42 | 42 | 42 |
| **Retrieval Engine** | None | Dense (MiniLM) | Hybrid (BM25+Dense) | Hybrid + Reranker |
| **Retrieval Top-K** | N/A | 5 | 5 | 5 (from 20) |
| **Aggregation Engine** | Deterministic | Deterministic | Deterministic | Deterministic |
| **Validation Rules** | Identical | Identical | Identical | Identical |
