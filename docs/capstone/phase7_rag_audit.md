# MedMatch Capstone — Phase 7: RAG vs. Non-RAG Pre-Implementation Audit

**Document Version:** `1.0.0`  
**Phase:** 7 — RAG vs. Non-RAG Experimental Evaluation  
**Date:** September 2026  
**Status:** Audit Specification  

---

## 1. Executive Summary

This audit establishes the experimental baseline for Phase 7 of the MedMatch capstone. It investigates how **Retrieval-Augmented Generation (RAG)** is presently structured across the repository, defines the exact boundary separating **RAG-grounded reasoning (E6)** from the **Non-RAG baseline (E5)**, audits production dependencies, and details the data limitations preventing premature empirical claims.

---

## 2. Current Production Architecture & Reasoning Path

### 2.1 The Production Reasoning Path
In `services/ai-service/app/services/matching_service.py`:
1. `MatchingService.evaluate_eligibility(patient_note, hospital_id, current_user, limit)` receives an unstructured clinical note and a tenant identifier.
2. Tenant access is verified via `_validate_user_hospital`.
3. `_retrieve_matching_criteria` embeds `patient_note` using `sentence-transformers/all-MiniLM-L6-v2` (384-d) on CPU and executes an exact kNN sequential scan in PostgreSQL (`SELECT trial_id, embedding <=> :patient_embedding AS distance FROM trial_embeddings WHERE hospital_id = :hospital_id ORDER BY distance ASC LIMIT :top_k`).
4. Unique trial IDs are extracted (`expected_trial_ids`).
5. For those candidate trials, all complete inclusion and exclusion criteria are fetched from `TrialCriteriaRepository.list_by_trial(trial_id)`.
6. `PromptBuilder.build_matching_prompt` groups all retrieved criteria by trial and formats them into `TRIAL_MATCHING_PROMPT`.
7. Google Gemini is invoked via `LLMService.evaluate_eligibility(prompt)` to generate a JSON array of `EligibilityResponse` objects.
8. `_validate_llm_trial_results` enforces that Gemini evaluated every retrieved trial ID exactly once without hallucinating or omitting trials.
9. Results are cached in Redis (`CacheKeys.llm`) and audited via `AuditService.log`.

### 2.3 What Constitutes RAG in Current MedMatch
In the current platform, RAG consists of:
- **Retrieval:** Using dense vector search over trial summary embeddings to filter a large trial catalog down to candidate trials, then loading their full criteria sets from SQL.
- **Augmentation:** Injecting these retrieved criteria descriptions, conditions, titles, and phases into the prompt context alongside the patient note.
- **Generation:** Direct LLM evaluation of eligibility based on that injected context.

---

## 3. Information Boundaries: E5 (Non-RAG) vs. E6 (RAG)

To rigorously answer the research question:
> *"Does evidence-grounded retrieval-augmented reasoning improve eligibility reasoning compared with a non-RAG baseline?"*

the two experimental conditions must be strictly controlled to isolate the exact causal effect of **retrieved trial evidence**:

```
+----------------------------------------------------------------------------------------------------+
|                                    CONTROLLED INFORMATION MATRIX                                   |
+------------------------------------+--------------------------------+------------------------------+
| Information Element                | E5: Non-RAG Baseline           | E6: RAG-Grounded Reasoner    |
+------------------------------------+--------------------------------+------------------------------+
| Patient Clinical Facts / Profile   | ALLOWED (Identical)            | ALLOWED (Identical)          |
| Patient Demographics               | ALLOWED (Identical)            | ALLOWED (Identical)          |
| Raw Patient Note Text              | ALLOWED (Identical where used) | ALLOWED (Identical)          |
| Trial Criterion Definitions (Task) | ALLOWED (Identical text)       | ALLOWED (Identical text)     |
| Retrieved Trial Summary Passages   | FORBIDDEN (Withheld)           | ALLOWED                      |
| Retrieved Criterion Passages       | FORBIDDEN (Withheld)           | ALLOWED                      |
| Retrieval Rankings & Scores        | FORBIDDEN (Withheld)           | ALLOWED (In metadata)        |
| Reranker Overlap Scores            | FORBIDDEN (Withheld)           | ALLOWED (In metadata)        |
| Pre-selected Retrieval Snippets    | FORBIDDEN (Withheld)           | ALLOWED                      |
| Criterion Evaluation Schema        | IDENTICAL (Phase 6 Schema)     | IDENTICAL (Phase 6 Schema)   |
| Trial Aggregation Logic            | IDENTICAL (Phase 6 Aggregator) | IDENTICAL (Phase 6 Aggregator)|
| Validation Harness                 | IDENTICAL (Phase 6 Validator)  | IDENTICAL (Phase 6 Validator) |
+------------------------------------+--------------------------------+------------------------------+
```

### 3.1 What Must Be Withheld from Non-RAG (E5)
1. Any candidate trial summary narrative retrieved from the vector store.
2. Any relevance rankings, cosine distances, BM25 scores, or RRF fusion weights.
3. Pre-computed evidence alignment spans retrieved by the search engine.
4. *Task definition exception:* The non-RAG reasoner receives the patient facts and the verbatim criterion text (e.g. "Age >= 18") so that it knows what question to evaluate, but it has zero access to external retrieved protocol context or retrieval-ranked evidence passages.

### 3.2 What RAG (E6) Receives
1. The exact same patient facts, demographics, and criterion text.
2. The retrieved trial protocol context, candidate criterion embeddings/matches, and retrieval source references generated by Phase 5 retrievers (`DenseRetriever`, `LexicalBM25Retriever`, `HybridRRFRetriever`).
3. Explicit character spans and provenance links connecting patient facts to candidate trial criteria.

---

## 4. Architectural Placement of Phase 7 Research Modules

To guarantee **zero disruption** to production operations, all experimental adapters and evaluation harnesses reside exclusively in the research layer:

- **`scripts/nonrag_experiment.py`**: Executes E5 Non-RAG baseline evaluation.
- **`scripts/rag_experiment.py`**: Executes E6 RAG-grounded evaluation.
- **`scripts/run_phase7_experiment.py`**: Orchestrates paired runs, leakage checks, metric computations, and report generation.
- **`tests/rag_evaluation/`**: Unit and integration test suite verifying contract compliance, isolation, and metrics.

**Zero production files under `services/` will be modified or imported into.**

---

## 5. Existing Benchmark & Dataset Limitations

1. **Development Fixture Status:**  
   The current repository contains only the **Phase 2 development fixture** (1 trial, 6 synthetic patients, 8 criteria). As established in Phase 2 (`data/README.md`), this is a tiny fixture designed solely for schema validation and unit testing. **It is NOT a research evaluation benchmark.**
2. **External Benchmark Status:**  
   Candidate benchmark datasets (TrialGPT 184-patient cohort, TREC Clinical Trials 2021/2022) were formally identified in Phase 2 but have **not yet been ingested** into the repository.
3. **Empirical Policy for Phase 7:**  
   The Phase 7 experimental harness, metrics calculation, error taxonomy, and leakage detection must be fully implemented and verified via automated tests. However, **no empirical superiority claims, fabricated metrics, or statistical significance tests will be reported** until a verified external benchmark is ingested.

---

## 6. Phase 5 Retrieval Engine Integration Status

Phase 7 now directly invokes the actual Phase 5 retrieval engine (`DenseRetriever`, `HybridRRFRetriever`, `RerankingRetriever`) for RAG conditions rather than relying on manual evidence dictionaries.

- **E6 (Dense-RAG):** Invokes Phase 5 `DenseRetriever` with canonical `RetrievalRequest`.
- **E7 (Hybrid-RAG):** Invokes Phase 5 `HybridRRFRetriever` combining `DenseRetriever` + `LexicalBM25Retriever` via Reciprocal Rank Fusion.
- **E8 (RAG + Reranking):** Invokes Phase 5 `RerankingRetriever` utilizing `ClinicalOverlapReranker`.
- **E5 (Non-RAG):** Withholds all retrieval components and executes strictly on patient facts and verbatim criterion definitions.

**Benchmark Notice:** The experiment remains unexecuted empirically because the validated research benchmark has not yet been ingested. All integration checkpoints are validated via automated unit and integration tests.

