# MedMatch Capstone — Phase 7: RAG vs. Non-RAG Experimental Evaluation Report

**Milestone:** Phase 7 — RAG vs. Non-RAG Experimental Evaluation  
**Status:** IMPLEMENTATION COMPLETE — AWAITING USER ACCEPTANCE  
**Date:** September 2026  
**Software Commit:** `120bd7e`  

---

## 1. Executive Summary

Phase 7 establishes the controlled experimental foundation to investigate the capstone research question:
> *"Does evidence-grounded retrieval-augmented reasoning improve eligibility reasoning compared with a non-RAG baseline?"*

To evaluate this question with scientific rigor, Phase 7 implemented the complete experimental harness, anti-leakage guards, paired metric calculators, and reproducibility tracking to compare **E5 (Non-RAG baseline)** against **E6 (RAG-grounded reasoning)**.

In strict adherence to capstone research integrity rules:
> **RAG vs non-RAG empirical performance comparison was not executed because a validated research benchmark with ground-truth labels was not yet available.**
>
> No empirical scores, bootstrap confidence intervals, McNemar significance figures, or ranking claims have been fabricated.

---

## 2. Experimental Architecture & Implementations

### 2.1 E5: Non-RAG Baseline (`scripts/nonrag_experiment.py`)
- **Implemented:** Clean adapter executing criterion-level reasoning strictly over patient clinical facts and criterion descriptions, **without** access to retrieved trial passages or vector search metadata.
- **Anti-Leakage Guardrail:** Defensively inspects input payloads and raises `InformationLeakageError` if any retrieval-derived keys (e.g. `retrieved_evidence`, `retrieval_rank`, `retrieval_score`) are detected.

### 2.2 E6 / E7 / E8: Actual Phase 5 Retrieval Integration (`scripts/rag_experiment.py`)
- **Direct Phase 5 Invocation:** Rather than accepting mock or manual evidence dictionaries, `RAGExperimentRunner` directly imports and invokes the actual Phase 5 retrieval engine classes:
  - **E6 (Dense-RAG):** Invokes Phase 5 `DenseRetriever` with canonical `RetrievalRequest`.
  - **E7 (Hybrid-RAG):** Invokes Phase 5 `HybridRRFRetriever` combining `DenseRetriever` + `LexicalBM25Retriever` via Reciprocal Rank Fusion.
  - **E8 (RAG + Reranking):** Invokes Phase 5 `RerankingRetriever` utilizing `ClinicalOverlapReranker`.
- **Evidence Provenance Preservation:** Links resolved criteria to both patient facts and retrieved evidence citations, preserving character spans, fact IDs, `retrieval_method`, `retrieval_rank`, `retrieval_score`, and source references (`source_field = "{retrieval_method}:{source_reference}"`).
- **Anti-Leakage Input Construction:** `run_case_comparison` constructs separate, immutable data dictionaries (`nonrag_criteria`, `nonrag_facts` vs. `rag_criteria`, `rag_facts`, `rag_evidence`) ensuring that retrieval results cannot inadvertently leak into Non-RAG evaluations.

### 2.3 Shared Deterministic Execution Framework
Both conditions are evaluated under strictly controlled variables:
- **Identical Inputs:** Identical patient facts, demographics, and verbatim criteria descriptions.
- **Identical Decision Logic:** Phase 6 canonical 3-valued schema (`PASS`, `FAIL`, `UNKNOWN`).
- **Identical Aggregation:** Deterministic pure code aggregator (`scripts/eligibility_aggregator.py`).
- **Identical Invariant Validation:** Rigorous validator (`scripts/validate_eligibility.py`) enforcing mandatory citations for `PASS` and `FAIL`.

---

## 3. Implementation vs. Evaluation Breakdown

### A. What Was Implemented
1. `NonRAGExperimentRunner` with anti-leakage verification.
2. `RAGExperimentRunner` integrating actual Phase 5 `DenseRetriever`, `HybridRRFRetriever`, and `RerankingRetriever`.
3. `Phase7ExperimentHarness` orchestrating paired comparisons and corpus candidate evaluations.
4. Comprehensive metric calculation utilities (Macro-F1, Precision, Recall, Accuracy, Unknown Rate, Evidence Grounding Rate).
5. 17-class comparative error taxonomy (`docs/capstone/phase7_rag_nonrag_error_taxonomy.md`).
6. Controlled experiment contract (`docs/capstone/phase7_rag_nonrag_contract.md`).
7. Ablation design matrix E5–E8 (`docs/capstone/phase7_experiment_matrix.md`).
8. Reproducibility & audit manifest specification (`docs/capstone/phase7_reproducibility.md`).

### B. What Was Tested
- **29 Phase 7 Unit, Contract, and Integration Tests (`tests/rag_evaluation/`):** All 29 passed.
  - Phase 5 `DenseRetriever` actual invocation by E6.
  - Phase 5 `HybridRRFRetriever` actual invocation by E7.
  - Phase 5 `RerankingRetriever` actual invocation by E8.
  - Zero retrieval invocation by E5.
  - Rejection of retrieval leakage by E5.
  - Receipt of actual `DenseRetriever` output by E6.
  - Receipt of actual `HybridRRFRetriever` output by E7.
  - Retrieval provenance preservation into RAG evidence citations and source fields.
  - Output conformity to Phase 6 schemas.
  - Identical deterministic aggregation behavior across conditions.
  - Strict rejection of ungrounded `PASS` and `FAIL` assertions.
  - Deterministic execution across repeated runs.
  - Explicit handling and detection of un-ingested research benchmarks.
  - Verification that production services do not import research modules and remain untouched.
- **Total Workspace Test Count:** **174 research tests** (Phases 2 through 7) and **45 production AI-service tests** passing with 0 regressions (219 total passing tests).

### C. What Was Empirically Evaluated
- Phase 7 now invokes the actual Phase 5 retrieval engine for RAG conditions.
- The experiment remains unexecuted empirically because the validated research benchmark has not yet been ingested.
- Only structural and toy benchmark verification was executed to mathematically validate metric functions and harness mechanics.

### D. What Was NOT Yet Evaluated
- Quantitative statistical comparison (Macro-$F_1$ deltas, bootstrap confidence intervals, McNemar tests, error distribution frequencies) between E5 and E6/E7/E8 on real-world patient cohorts.

### E. Benchmark Dependencies
- Quantitative evaluation is blocked pending ingestion of Layer B (`research_benchmark`), such as the 184-patient TrialGPT benchmark or TREC Clinical Trials corpora. The 6-patient Phase 2 synthetic fixture is NOT used as empirical evidence.

### F. Limitations
- Current evaluations are limited to offline synthetic test fixtures.
- Statistical significance cannot be asserted on sample sizes below power thresholds ($N < 30$).
- Generalization to external multi-center EHR formats remains unmeasured.

---

## 4. Production Isolation Verification

1. **Zero Modifications to Production Services:** `services/ai-service/`, `services/auth-service/`, and `frontend/` remain 100% untouched.
2. **Zero Imports from Experiment Modules:** Confirmed by automated test that no production file imports `nonrag_experiment`, `rag_experiment`, or `run_phase7_experiment`.
3. **Retrieval and Reasoning Integrity:** Phase 5 retrieval algorithms and Phase 6 eligibility reasoners are unchanged.

---

## 5. Non-Validation Statement & Phase Boundary

> [!CAUTION]
> **DISCLAIMER:**  
> MedMatch is an academic research decision-support prototype. It is **NOT** clinically validated and does not make autonomous clinical trial eligibility decisions. All matching recommendations require expert clinical evaluation.

- **Phase 8 (Human-in-the-Loop Clinician Study / Advanced Error Analysis) has NOT been started.**
- **STOPPED after Phase 7.**
