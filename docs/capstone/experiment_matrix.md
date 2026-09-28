# MedMatch Capstone — Experiment Matrix & Ablation Plan

> **Status:** Specification Document  
> **Phase:** 1 — Research Problem & Evaluation Design  
> **Author:** MedMatch Research Team  
> **Date:** September 2026  
> **Target System:** MedMatch Clinical Decision-Support Prototype

---

## 1. Controlled Experiment Matrix

The experimental roadmap defines five progressive system configurations (E0 through E4). In accordance with Phase 1 constraints, **no experimental runs are executed in this phase**, and **no results are claimed or fabricated**.

```text
+-------------------------------------------------------------------------------------------------------------------------+
|                                                   EXPERIMENT MATRIX                                                     |
+----+--------------------+----------------------+-------------------+-----------------------+----------------------------+
| ID | System Name        | Retrieval Mechanism  | Reasoning Engine  | Patient Input Format  | Primary Metric Targets     |
+----+--------------------+----------------------+-------------------+-----------------------+----------------------------+
| E0 | LLM Baseline       | None (Parametric)    | Monolithic Prompt | Raw Clinical Note     | Trial Macro-F1, UCR        |
| E1 | Current MedMatch   | Dense (MiniLM-L6-v2) | Monolithic Prompt | Raw Clinical Note     | Recall@5, Trial Macro-F1   |
| E2 | Hybrid Retrieval   | BM25 + Dense (RRF)   | Monolithic Prompt | Raw Clinical Note     | Recall@{5,10,20}, MRR, F1  |
| E3 | Structured Profile | Hybrid (BM25 + Dense)| Criterion-Level   | Structured Profile    | Criterion F1, Trial F1     |
| E4 | Full Grounded RAG  | Hybrid + Reranker    | Decomposed + Span | Dual (Profile + Note) | All (Retrieval, F1, Ground)|
+----+--------------------+----------------------+-------------------+-----------------------+----------------------------+
```

### 1.1 Detailed Experiment Specifications

#### Experiment E0: Non-Retrieval LLM Baseline
- **Purpose:** Measures the baseline performance of Google Gemini 2.5 Flash without access to a vector search index, establishing the performance floor and isolating the impact of information retrieval.
- **Retrieval:** None. Candidate trial descriptions are provided directly in the prompt or queried zero-shot.
- **Patient Input:** Unstructured clinical encounter text $N_P$.
- **Prompt:** Single monolithic zero-shot prompt.
- **Target Metrics:** Macro-$F_1$, Unsupported Claim Rate ($UCR$), Execution Latency.

#### Experiment E1: Current MedMatch Baseline (Phase 0 Implementation)
- **Purpose:** Rigorously benchmarks the exact production system audited in Phase 0.
- **Retrieval:** Sequential pgvector cosine distance over `sentence-transformers/all-MiniLM-L6-v2` embeddings (`top_k = 5`, distance threshold `0.75`).
- **Patient Input:** Raw `patient_note: str`.
- **Reasoning:** Production 966-line prompt `TRIAL_MATCHING_PROMPT` in `app/prompts/trial_matching_prompt.py`.
- **LLM:** Google Gemini 2.5 Flash (`temperature = 0.0`).
- **Target Metrics:** Recall@5, Trial-Level Macro-$F_1$, Precision for `ELIGIBLE`, Evidence Coverage.

#### Experiment E2: Hybrid Lexical + Semantic Retrieval
- **Purpose:** Evaluates whether adding BM25 sparse search addresses dense retrieval blindness on exact medical terms, gene mutations, and laboratory values (Hypothesis H2).
- **Retrieval:** Hybrid combination of sparse BM25 and dense `all-MiniLM-L6-v2` merged via Reciprocal Rank Fusion (RRF, $k=60$).
- **Patient Input:** Raw clinical note $N_P$.
- **Reasoning:** Identical monolithic prompt to E1.
- **Target Metrics:** Recall@1, Recall@3, Recall@5, Recall@10, MRR, nDCG@10.

#### Experiment E3: Structured Patient Representation + Criterion-Level Reasoning
- **Purpose:** Evaluates whether converting clinical text into structured clinical entities and decomposing reasoning into individual criteria reduces misclassification (Hypotheses H3, H5).
- **Retrieval:** Hybrid retrieval as validated in E2.
- **Patient Input:** Structured clinical profile $D_P, E_P$ (demographics, normalized conditions, biomarker status, lab values).
- **Reasoning:** Modular criterion evaluation function $g(P, c_i) \to \{\text{PASS}, \text{FAIL}, \text{UNKNOWN}\}$ followed by deterministic aggregation $\Lambda$.
- **Target Metrics:** Criterion-Level Macro-$F_1$, False Positive Rate ($FPR_{\text{elig}}$), Calibration Error (ECE).

#### Experiment E4: Full Evidence-Grounded Modular Architecture (Target System C)
- **Purpose:** Evaluates the complete proposed capstone framework incorporating hybrid retrieval, cross-encoder reranking, dual patient representation, character-span evidence extraction, and deterministic clinical aggregation.
- **Retrieval:** Two-stage retrieval: Stage 1 Hybrid (BM25 + Dense) candidate retrieval ($K_1 = 20$) followed by Stage 2 Cross-Encoder reranking ($K_2 = 5$).
- **Patient Input:** Dual representation (Structured clinical profile $D_P, E_P$ + verbatim narrative $N_P$).
- **Reasoning:** Decomposed criterion-level verification with explicit character-level text span citation.
- **Target Metrics:** Full evaluation suite: Recall@5, nDCG@5, Criterion Macro-$F_1$, Trial Macro-$F_1$, Grounded Decision Rate ($GDR$), Unsupported Claim Rate ($UCR$), 12-factor error distribution.

---

## 2. Systematic Ablation Study Plan

To determine the isolated marginal contribution of each architectural component, five ablation dimensions will be investigated:

```text
                               +----------------------------------+
                               |     ABLATION STUDY DIMENSIONS    |
                               +----------------------------------+
                                                |
          +-------------------+-----------------+-----------------+-------------------+
          |                   |                 |                 |                   |
          v                   v                 v                 v                   v
     [Dimension 1]       [Dimension 2]     [Dimension 3]     [Dimension 4]       [Dimension 5]
       Retrieval          Candidate           Patient          Reasoning           Evidence
      Architecture       Depth (Top-K)     Representation     Decomposition       Provenance
   - Dense only        - K = 3           - Raw note only    - Monolithic prompt - Without spans
   - Sparse (BM25)     - K = 5           - Structured only  - Domain-grouped    - With spans
   - Hybrid (RRF)      - K = 10          - Dual (Both)      - Atomic criterion  - Strict verified
   - Hybrid + Rerank   - K = 20
```

### 2.1 Dimension 1: Candidate Retrieval Mechanism
- **Variants:**
  - $A_{1.1}$: Dense Vector Only (`all-MiniLM-L6-v2`)
  - $A_{1.2}$: Sparse Lexical Only (BM25)
  - $A_{1.3}$: Hybrid (BM25 + Dense RRF)
  - $A_{1.4}$: Hybrid + Cross-Encoder Reranker (`bge-reranker-large` or `ms-marco-MiniLM-L-6-v2`)
- **Fixed Parameters:** Reasoning engine (E1 or E3), $K=5$, fixed test queries.
- **Evaluates:** Hypothesis H2 (retrieval recall, MRR, nDCG).

### 2.2 Dimension 2: Candidate Retrieval Depth ($K$)
- **Variants:** $K \in \{3, 5, 10, 20\}$
- **Fixed Parameters:** Retrieval algorithm (Hybrid), downstream reasoning engine.
- **Evaluates:** Tradeoff between retrieval recall (improving downstream eligibility ceiling) and context-window cognitive load / latency.

### 2.3 Dimension 3: Patient Information Representation
- **Variants:**
  - $A_{3.1}$: Raw clinical narrative text $N_P$ only (Current MedMatch baseline).
  - $A_{3.2}$: Structured clinical profile $D_P, E_P$ only (Normalized JSON).
  - $A_{3.3}$: Dual representation ($D_P, E_P + N_P$).
- **Fixed Parameters:** Retrieval and reasoning engine.
- **Evaluates:** Hypothesis H3 (false positive rate and normalization value).

### 2.4 Dimension 4: Reasoning Decomposition
- **Variants:**
  - $A_{4.1}$: Monolithic whole-trial prompt (evaluates all 20+ criteria in single LLM completion).
  - $A_{4.2}$: Domain-grouped criteria prompts (evaluates criteria grouped by clinical domain: Labs, Genomics, History).
  - $A_{4.3}$: Atomic criterion evaluation ($g(P, c_i)$ evaluated individually and aggregated via $\Lambda$).
- **Evaluates:** Reasoning granularity impact on accuracy and schema adherence.

### 2.5 Dimension 5: Evidence Grounding and Provenance Attribution
- **Variants:**
  - $A_{5.1}$: Unconstrained generation (LLM generates decision and rationale without text-span constraint).
  - $A_{5.2}$: Span-constrained generation (LLM must quote exact character-level text spans).
  - $A_{5.3}$: Span-verified generation (Automated post-hoc substring verification against original patient narrative).
- **Evaluates:** Hypothesis H4 (Unsupported Claim Rate, Grounded Decision Rate).
