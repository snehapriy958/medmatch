# Phase 11 Ablation Specification: Hypotheses & Component Isolation (A1–A5)

**Document ID:** ABL-SPEC-P11  
**Phase:** Phase 11 — Evaluation & Ablation  
**Scope:** Controlled Component Isolation, Phase 1 Hypothesis Mapping, and Empirical Safeguards

---

## 1. Overview & Research Hypotheses

The MedMatch Phase 1 evaluation design specified five primary architectural hypotheses ($H_1$ through $H_5$). Phase 11 operationalizes these hypotheses through five strictly controlled, paired ablation experiments ($A_1$ through $A_5$).

Every ablation isolates exactly one architectural component while holding all other system elements strictly invariant.

---

## 2. Canonical Ablation Matrix

```text
+---------------------------------------------------------------------------------------------------------------------+
|                                              PHASE 11 ABLATION MATRIX                                               |
+----+-----------------------------+---------------+-----------------+-------------------------+----------------------+
| ID | Ablation Name               | Baseline (A)  | Treatment (B)   | Isolated Component      | Hypothesis Tested    |
+----+-----------------------------+---------------+-----------------+-------------------------+----------------------+
| A1 | Dense vs Hybrid Retrieval   | E2_DENSE_RAG  | E3_HYBRID_RAG   | Retrieval Strategy      | H1: Lexical + Dense  |
|    |                             |               |                 | (Dense vs BM25+Dense)   | improves recall      |
| A2 | Hybrid vs Reranking         | E3_HYBRID_RAG | E4_RERANKED_RAG | Second-Stage Reranking  | H2: Concept overlap  |
|    |                             |               |                 | (None vs Cross-Encoder) | boosts precision@K   |
| A3 | Raw Note vs Structured Prof | E0_BASELINE   | E1_STRUCTURED   | Patient Representation  | H3: Structured facts |
|    |                             |               |                 | (Raw Text vs Profile)   | reduce unknowns      |
| A4 | Non-RAG vs RAG              | E1_STRUCTURED | E2_DENSE_RAG    | Evidence Augmentation   | H4: RAG grounds      |
|    |                             |               |                 | (Non-RAG vs Dense RAG)  | criteria resolution  |
| A5 | Grounding vs Non-Grounded   | E1_STRUCTURED | E2_DENSE_RAG    | Evidence Citations      | H5: Citations enable |
|    |                             |               |                 | (Absent vs Present)     | audit traceability   |
+----+-----------------------------+---------------+-----------------+-------------------------+----------------------+
```

---

## 3. Detailed Ablation Protocols

### 3.1. Ablation A1: Dense vs. Hybrid Retrieval
- **Hypothesis ($H_1$):** Hybrid retrieval combining dense semantic embeddings with BM25 lexical token matching improves candidate retrieval coverage by capturing exact biomarker codes (e.g., *EGFR L858R*) missed by dense bi-encoders.
- **Baseline System:** `E2_DENSE_RAG` (DenseRetriever).
- **Treatment System:** `E3_HYBRID_RAG` (HybridRRFRetriever, $k_{\text{rrf}} = 60$).
- **Changed Component:** Retrieval scoring function.
- **Unchanged Components:** Patient profile, candidate pool, reasoning engine, aggregation policy, top-$k=5$.
- **Primary Metrics:** Retrieval MRR, Recall@K, Eligibility Macro-$F_1$.
- **Sample Size:** $n=6$ patient encounters.
- **Interpretation Constraint:** *Development fixture observation only. Sample size is insufficient to statistically prove generalized hybrid superiority over dense embeddings.*

### 3.2. Ablation A2: Hybrid Retrieval vs. Hybrid + Reranking
- **Hypothesis ($H_2$):** A second-stage clinical concept overlap reranker over a broader candidate pool ($2 \times \text{top\_k}$) improves the ranking precision of candidate protocols.
- **Baseline System:** `E3_HYBRID_RAG` (Hybrid retrieval without reranking).
- **Treatment System:** `E4_RERANKED_RAG` (Hybrid retrieval + ClinicalOverlapReranker).
- **Changed Component:** Second-stage candidate reranker.
- **Unchanged Components:** Initial hybrid candidate generator, patient profile, reasoning logic, top-$k=5$.
- **Primary Metrics:** Precision@K, nDCG@K, Decision Accuracy.
- **Sample Size:** $n=6$ patient encounters.
- **Interpretation Constraint:** *Development fixture observation only. Re-ranking depth cannot demonstrate statistical significance on a single trial protocol.*

### 3.3. Ablation A3: Raw Patient Representation vs. Structured Profile
- **Hypothesis ($H_3$):** Transforming unstructured clinical narratives into structured patient profiles with explicit negation and temporal assertions resolves criteria more definitively and reduces unknown rates.
- **Baseline System:** `E0_BASELINE` (Unstructured raw clinical note).
- **Treatment System:** `E1_STRUCTURED_PROFILE` (Structured `PatientClinicalProfile`).
- **Changed Component:** Patient entity representation.
- **Unchanged Components:** Dense retrieval discovery, non-RAG reasoning rules, criteria definitions.
- **Primary Metrics:** Eligibility Macro-$F_1$, Accuracy, Criterion Accuracy, UNKNOWN rate.
- **Sample Size:** $n=6$ patient encounters.
- **Interpretation Constraint:** *Development fixture observation only. Reflects fixture rule coverage rather than broad NLP model generalizability.*

### 3.4. Ablation A4: Non-RAG vs. RAG
- **Hypothesis ($H_4$):** Augmenting eligibility reasoning with retrieved trial protocol context allows criteria that depend on trial specifications to be evaluated safely rather than defaulting to conservative `UNKNOWN`.
- **Baseline System:** `E1_STRUCTURED_PROFILE` (Non-RAG structured reasoning).
- **Treatment System:** `E2_DENSE_RAG` (Dense RAG with protocol evidence context).
- **Changed Component:** Presence of retrieved trial protocol passages during criterion reasoning.
- **Unchanged Components:** Patient facts, dense retrieval method, rule-based reasoning engine, aggregation logic.
- **Primary Metrics:** Eligibility Macro-$F_1$, Grounding Score, Claim Support Rate.
- **Sample Size:** $n=6$ patient encounters.
- **Interpretation Constraint:** *Development fixture observation only. True RAG superiority must be demonstrated on public multi-trial benchmarks (TrialGPT/TREC).*

### 3.5. Ablation A5: Evidence-Grounded Reasoning vs. Non-Retrieved Reasoning
- **Hypothesis ($H_5$):** Enforcing explicit character-level evidence citations and graph traceability eliminates ungrounded claims and enables auditability.
- **Baseline System:** `E1_STRUCTURED_PROFILE` (Reasoning without evidence citations).
- **Treatment System:** `E2_DENSE_RAG` (Reasoning with exact character span evidence citations).
- **Changed Component:** Evidence citation generation and verification.
- **Unchanged Components:** Patient facts, demographics, criteria definitions, deterministic aggregation.
- **Primary Metrics:** Evidence Coverage, Grounding Score, Citation Validity Rate, Decision Traceability Rate.
- **Sample Size:** $n=6$ patient encounters.
- **Interpretation Constraint:** *Development fixture observation only. Traceability metrics measure schema compliance, not empirical clinical safety.*

---

## 4. Empirical Safeguard Declaration

Every ablation result produced by [`scripts/ablation_runner.py`](file:///C:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/ablation_runner.py) embeds the following invariants:
- `is_development_fixture_observation_only = True`
- `empirical_superiority_claim_permitted = False`
- No p-values or significance claims are generated.
