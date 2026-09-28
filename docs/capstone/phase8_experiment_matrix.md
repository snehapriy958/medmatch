# MedMatch Capstone — Phase 8: Grounding Experiment Matrix (G1–G4)

**Document Version:** `1.0.0`  
**Phase:** 8 — Grounding Evaluation & Faithfulness Auditing  
**Date:** September 2026  
**Status:** Canonical Experiment Matrix  

---

## 1. Experimental Overview & Architecture Alignment

Phase 8 extends the Phase 7 experimental matrix (E5–E8) by attaching the **Grounding & Faithfulness Evaluation Layer** to inspect the reasoning generated under each retrieval condition:

```text
+---------------------------------------------------------------------------------------------------------------------------------------+
|                                                  PHASE 8 GROUNDING EXPERIMENT MATRIX                                                  |
+----+----------------------+--------------------+--------------------+-----------------------+---------------------+-------------------+
| ID | Experiment Name      | Retrieval Engine   | Candidate Pool     | Reasoning Context     | Grounding Evaluator | Status            |
+----+----------------------+--------------------+--------------------+-----------------------+---------------------+-------------------+
| G1 | NON-RAG Grounding    | NONE               | Task Criteria Only | Patient Facts + Note  | Deterministic Pure  | IMPLEMENTED       |
|    | Evaluation           | (No Retrieval)     | (No Passages)      | (No Retrieved Text)   | Code Validator (P8) | (EMPIRICAL PEND.) |
+----+----------------------+--------------------+--------------------+-----------------------+---------------------+-------------------+
| G2 | Dense-RAG Grounding  | Phase 5 Dense      | Top-5 Trials       | Patient Facts +       | Deterministic Pure  | IMPLEMENTED       |
|    | Evaluation           | (all-MiniLM-L6-v2) | pgvector Cosine    | Dense Retrieved Text  | Code Validator (P8) | (EMPIRICAL PEND.) |
+----+----------------------+--------------------+--------------------+-----------------------+---------------------+-------------------+
| G3 | Hybrid-RAG Grounding | Phase 5 Hybrid     | Top-5 Trials       | Patient Facts +       | Deterministic Pure  | IMPLEMENTED       |
|    | Evaluation           | (BM25 + Dense RRF) | RRF Score Fusion   | Hybrid Retrieved Text | Code Validator (P8) | (EMPIRICAL PEND.) |
+----+----------------------+--------------------+--------------------+-----------------------+---------------------+-------------------+
| G4 | RAG + Reranking      | Phase 5 Hybrid +   | Top-5 Trials from  | Patient Facts +       | Deterministic Pure  | IMPLEMENTED       |
|    | Grounding Evaluation | Clinical Reranker  | Top-20 Pool        | Reranked Evidence     | Code Validator (P8) | (EMPIRICAL PEND.) |
+----+----------------------+--------------------+--------------------+-----------------------+---------------------+-------------------+
```

> [!IMPORTANT]
> **EMPIRICAL BENCHMARK STATUS:**  
> The evaluation harnesses and metric calculators for conditions G1, G2, G3, and G4 are fully implemented and verified via automated test suites. However, in strict accordance with capstone research integrity rules, **no comparative empirical scores or benchmark rankings are reported** because the external research benchmark (TrialGPT/TREC CT) has not yet been ingested into the repository. The 16-case synthetic development fixture is used solely for code and logic verification.

---

## 2. Experimental Condition Specifications

### Condition G1: NON-RAG Grounding Evaluation
- **Baseline Reasoning Source:** Phase 7 E5 baseline (`NonRAGExperimentRunner`).
- **Retrieval Engine:** `NONE`.
- **Information Boundary:** Receives patient clinical facts and criterion text; strictly isolated from all retrieval candidate summaries, ranks, and scores.
- **Grounding Evaluation Goal:** Measure baseline hallucination rate, unsupported assertion rate, and epistemic abstention rate when the reasoner lacks protocol context.
- **Expected Failure Mode:** Elevated `UNSUPPORTED` claim rate or epistemic abstention (`INSUFFICIENT_EVIDENCE`) when protocol-specific definitions are absent.

### Condition G2: Dense-RAG Grounding Evaluation
- **Reasoning Source:** Phase 7 E6 runner (`RAGExperimentRunner.create_dense_rag`).
- **Retrieval Engine:** Phase 5 `DenseRetriever` using cosine similarity over candidate trial embeddings.
- **Information Boundary:** Patient facts + dense retrieved candidate protocol summaries.
- **Grounding Evaluation Goal:** Measure whether dense semantic retrieval improves evidence coverage without introducing citation corruption or semantic hallucination.

### Condition G3: Hybrid-RAG Grounding Evaluation
- **Reasoning Source:** Phase 7 E7 runner (`RAGExperimentRunner.create_hybrid_rag`).
- **Retrieval Engine:** Phase 5 `HybridRRFRetriever` combining `DenseRetriever` and `LexicalBM25Retriever` ($k_{rrf}=60$).
- **Information Boundary:** Patient facts + hybrid retrieved candidate summaries.
- **Grounding Evaluation Goal:** Measure whether exact lexical matching (BM25) reduces numerical ($H3$) and biomarker ($H1$) hallucinations compared to dense-only retrieval.

### Condition G4: RAG + Clinical Cross-Encoder Reranking
- **Reasoning Source:** Phase 7 E8 runner (`RAGExperimentRunner.create_reranked_rag`).
- **Retrieval Engine:** Phase 5 `RerankingRetriever` utilizing `ClinicalOverlapReranker`.
- **Information Boundary:** Patient facts + reranked candidate protocol evidence.
- **Grounding Evaluation Goal:** Measure whether second-stage clinical concept alignment maximizes Citation Validity Rate ($\text{CVR}$) and minimizes Contradiction Rate ($\text{CR}$).

---

## 3. Strict Controlled Execution Parameters

To ensure experimental rigor and eliminate confounding variables, all non-retrieval parameters are held strictly constant across G1, G2, G3, and G4:

| Experimental Parameter | G1 (NON-RAG) | G2 (Dense-RAG) | G3 (Hybrid-RAG) | G4 (Reranked-RAG) | Control State |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Patient Profile** | Identical | Identical | Identical | Identical | Strictly Fixed |
| **Criteria List** | Identical | Identical | Identical | Identical | Strictly Fixed |
| **Reasoner Engine** | `RuleBasedEligibilityReasoner` | `RuleBasedEligibilityReasoner` | `RuleBasedEligibilityReasoner` | `RuleBasedEligibilityReasoner` | Strictly Fixed |
| **Aggregator** | `EligibilityAggregator` | `EligibilityAggregator` | `EligibilityAggregator` | `EligibilityAggregator` | Strictly Fixed |
| **Validator** | `EligibilityValidator` | `EligibilityValidator` | `EligibilityValidator` | `EligibilityValidator` | Strictly Fixed |
| **Claim Extractor** | `DeterministicClaimExtractor` | `DeterministicClaimExtractor` | `DeterministicClaimExtractor` | `DeterministicClaimExtractor` | Strictly Fixed |
| **Grounding Validator** | `GroundingValidator` | `GroundingValidator` | `GroundingValidator` | `GroundingValidator` | Strictly Fixed |
| **Metrics Engine** | `GroundingMetricsEngine` | `GroundingMetricsEngine` | `GroundingMetricsEngine` | `GroundingMetricsEngine` | Strictly Fixed |
| **Retrieval Engine** | `NONE` | Phase 5 Dense | Phase 5 Hybrid RRF | Phase 5 Reranking | **Independent Variable** |
