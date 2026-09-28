# Phase 11 Experiment Specification: Controlled Evaluation Matrix (E0–E4)

**Document ID:** EVAL-SPEC-P11  
**Phase:** Phase 11 — Evaluation & Ablation  
**Scope:** Canonical Configurations, Pipelines, Controlled Parameters, and Anti-Leakage Boundaries

---

## 1. Objective

This specification formalizes the five experimental conditions evaluated in Phase 11 to test the central research question:
*Does evidence-grounded RAG improve clinical-trial eligibility matching accuracy, retrieval quality, grounding, uncertainty handling, and explainability compared with the existing baseline?*

---

## 2. Canonical Experiment Matrix (E0–E4)

```mermaid
flowchart TD
    subgraph E0_Pipeline["E0: Baseline System"]
        E0_In["Raw Clinical Note (Text)"] --> E0_Ret["Dense Vector Retrieval"]
        E0_Ret --> E0_Candidates["Top-K Candidate Trials"]
        E0_Candidates --> E0_Reason["Unstructured Reasoning (Raw Text Only)"]
        E0_Reason --> E0_Out["Baseline Eligibility Decisions"]
    end

    subgraph E1_Pipeline["E1: Structured Profile (Non-RAG)"]
        E1_In["Structured Patient Profile (Phase 4)"] --> E1_Ret["Dense Vector Retrieval"]
        E1_Ret --> E1_Candidates["Top-K Candidate Trials"]
        E1_Candidates --> E1_Reason["Structured Non-RAG Reasoning (No Passages)"]
        E1_Reason --> E1_Out["Non-RAG Eligibility Decisions"]
    end

    subgraph E2_Pipeline["E2: Dense RAG"]
        E2_In["Structured Patient Profile"] --> E2_Ret["Phase 5 DenseRetriever"]
        E2_Ret --> E2_Evidence["Retrieved Protocol Evidence"]
        E2_Evidence --> E2_Reason["Phase 6 Grounded Reasoning"]
        E2_Reason --> E2_Out["Dense RAG Decisions"]
    end

    subgraph E3_Pipeline["E3: Hybrid RAG"]
        E3_In["Structured Patient Profile"] --> E3_Ret["Phase 5 HybridRRFRetriever (Dense + BM25)"]
        E3_Ret --> E3_Evidence["Fused RRF Protocol Evidence"]
        E3_Evidence --> E3_Reason["Phase 6 Grounded Reasoning"]
        E3_Reason --> E3_Out["Hybrid RAG Decisions"]
    end

    subgraph E4_Pipeline["E4: RAG + Reranking"]
        E4_In["Structured Patient Profile"] --> E4_Ret["Phase 5 RerankingRetriever"]
        E4_Ret --> E4_Evidence["Reranked Evidence (Clinical Overlap)"]
        E4_Evidence --> E4_Reason["Phase 6 Grounded Reasoning"]
        E4_Reason --> E4_Out["Reranked RAG Decisions"]
    end
```

---

## 3. Detailed Experiment Configurations

### 3.1. E0 — Existing Baseline
- **Description:** Mirrors the Phase 0 baseline architecture faithfully without silent improvements.
- **Input Representation:** Unstructured patient clinical narrative string (`note`). Demographics and structured clinical concepts are omitted.
- **Candidate Discovery:** Dense cosine vector retrieval over trial text embeddings.
- **Reasoning Component:** RuleBasedEligibilityReasoner operating strictly on keyword scan of raw text string. Missing clinical facts are not synthesized.
- **Evidence Augmentation:** None (raw criteria requirements only).
- **Configuration Contract:**
  ```json
  {
    "experiment_id": "E0_BASELINE",
    "patient_representation": "raw_clinical_note",
    "retrieval_strategy": "dense",
    "top_k": 5,
    "random_seed": 42
  }
  ```

### 3.2. E1 — Structured Patient Profile (Non-RAG)
- **Description:** Evaluates the isolated contribution of the Phase 4 structured `PatientClinicalProfile` while holding retrieval and reasoning non-augmented.
- **Input Representation:** Structured patient entity (`demographics`, `clinical_facts`, temporal offsets, assertion states).
- **Candidate Discovery:** Dense vector retrieval (identical candidate pool to E0).
- **Reasoning Component:** Non-RAG eligibility reasoner ([`NonRAGExperimentRunner`](file:///C:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/nonrag_experiment.py)).
- **Evidence Augmentation:** Prohibited (strict anti-leakage checks reject any retrieved passages or ranking scores).
- **Configuration Contract:**
  ```json
  {
    "experiment_id": "E1_STRUCTURED_PROFILE",
    "patient_representation": "structured_profile",
    "retrieval_strategy": "dense",
    "top_k": 5,
    "random_seed": 42
  }
  ```

### 3.3. E2 — Dense RAG
- **Description:** RAG pipeline pairing structured profiles with the actual Phase 5 [`DenseRetriever`](file:///C:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/retrieval_engine.py#L177).
- **Input Representation:** Structured patient profile.
- **Candidate Discovery:** Dense vector similarity (`cosine_similarity`).
- **Reasoning Component:** Phase 6 evidence-grounded reasoner ([`RAGExperimentRunner.create_dense_rag()`](file:///C:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/rag_experiment.py#L107)).
- **Evidence Augmentation:** Retrieved trial protocol summary, rank, score, and source URI passed into criterion reasoning context to resolve ambiguous requirements.
- **Configuration Contract:**
  ```json
  {
    "experiment_id": "E2_DENSE_RAG",
    "patient_representation": "structured_profile",
    "retrieval_strategy": "dense",
    "top_k": 5,
    "random_seed": 42
  }
  ```

### 3.4. E3 — Hybrid RAG
- **Description:** Hybrid RAG pipeline pairing structured profiles with the actual Phase 5 [`HybridRRFRetriever`](file:///C:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/retrieval_engine.py#L319).
- **Input Representation:** Structured patient profile.
- **Candidate Discovery:** Reciprocal Rank Fusion of dense embeddings and Okapi BM25 scores ($k_{\text{rrf}} = 60$).
- **Reasoning Component:** Phase 6 evidence-grounded reasoner.
- **Evidence Augmentation:** Hybrid retrieved evidence context with dense and lexical component ranks.
- **Configuration Contract:**
  ```json
  {
    "experiment_id": "E3_HYBRID_RAG",
    "patient_representation": "structured_profile",
    "retrieval_strategy": "hybrid_rrf",
    "top_k": 5,
    "bm25_k1": 1.2,
    "bm25_b": 0.75,
    "rrf_constant": 60,
    "random_seed": 42
  }
  ```

### 3.5. E4 — RAG + Reranking
- **Description:** Two-stage retrieval-augmented pipeline using the actual Phase 5 [`RerankingRetriever`](file:///C:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/retrieval_engine.py#L481).
- **Input Representation:** Structured patient profile.
- **Candidate Discovery:** Hybrid candidate generation with pool multiplier $=2$ ($2 \times \text{top\_k}$ candidates retrieved) followed by [`ClinicalOverlapReranker`](file:///C:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/retrieval_engine.py#L424) concept scoring.
- **Reasoning Component:** Phase 6 evidence-grounded reasoner.
- **Evidence Augmentation:** Top reranked trial evidence with rerank scores and original ranks.
- **Configuration Contract:**
  ```json
  {
    "experiment_id": "E4_RERANKED_RAG",
    "patient_representation": "structured_profile",
    "retrieval_strategy": "hybrid_reranked",
    "top_k": 5,
    "reranker_multiplier": 2,
    "random_seed": 42
  }
  ```

---

## 4. Controlled Variables & Invariant Safeguards

To prevent confounding between experiments, all variables are held strictly invariant across E0–E4:

| Parameter | Value | Scope of Control |
|:---|:---|:---|
| **Random Seed** | `42` | Controls all tie-breaking and deterministic orderings. |
| **Candidate Trial Pool** | Frozen from `trials.json` | All systems retrieve from the exact same candidate pool. |
| **Candidate Truncation ($K$)** | `top_k = 5` | Consistent candidate depth evaluated across all pipelines. |
| **BM25 Index Hyperparameters** | $k_1 = 1.2, b = 0.75$ | Okapi BM25 constants identical across E3 and E4. |
| **RRF Fusion Constant** | $k_{\text{rrf}} = 60$ | Reciprocal rank constant identical across E3 and E4. |
| **Eligibility Decision Logic** | Three-valued logic | `PASS`, `FAIL`, `UNKNOWN` semantics held identical. |
| **Aggregation Rules** | Deterministic Phase 6 | `ANY FAIL -> INELIGIBLE`, `NO FAIL + ANY UNKNOWN -> NEEDS_REVIEW`, `ALL PASS -> ELIGIBLE`. |
| **Reasoning Temperature** | `0.0` (Deterministic) | Rule-based execution; zero stochastic LLM variance. |

---

## 5. Anti-Leakage Isolation & Defensive Boundaries

1. **Non-RAG Boundary (E0, E1):**
   - The [`NonRAGExperimentRunner.assert_no_retrieval_leakage()`](file:///C:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/nonrag_experiment.py#L52) guardrail actively inspects all inputs. If any forbidden retrieval key (`retrieved_evidence`, `retrieval_rank`, `retrieval_score`, `retrieval_method`, `bm25_score`) is detected, execution aborts with `InformationLeakageError`.
2. **Ground Truth Boundary (All Systems):**
   - Gold trial-level labels and criterion ground-truth labels are never passed into any retrieval or reasoning function.
   - Ground truth is strictly restricted to [`EvaluationMetricsEngine`](file:///C:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/evaluation_metrics.py#L32) evaluation routines after predictions are fully generated.
