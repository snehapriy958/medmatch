# MedMatch Capstone — Retrieval Experiment Matrix (E0 to E4)

## 1. Overview & Research Hypothesis

### Primary Research Question
> **"Does evidence-aware hybrid retrieval improve candidate retrieval quality over the current dense-vector retrieval baseline for clinical-trial eligibility matching?"**

To empirically evaluate this question without compromising production operations, Phase 5 establishes an experiment matrix spanning five standardized retrieval configurations:
- **E0:** Baseline Dense Vector Retrieval (Current Production)
- **E1:** Structured Profile Dense Retrieval
- **E2:** Lexical BM25 Retrieval
- **E3:** Hybrid Dense + Lexical Fusion (RRF)
- **E4:** Hybrid Fusion + Second-Stage Reranking

> [!WARNING]
> **RESEARCH INTEGRITY DIRECTIVE:**
> No configuration is claimed to be superior prior to empirical evaluation against an accredited clinical benchmark corpus. Hyperparameters must not be tuned on the test split.

---

## 2. Standardized Experiment Matrix

| Experiment ID | Strategy Name | Independent Variable | Fixed Architecture | Candidate Pool Size | Primary Evaluation Metrics |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **E0 (Baseline)** | **Current Dense Baseline** | Raw unstructured note string directly embedded. | `all-MiniLM-L6-v2` (384-d), pgvector cosine `<=>`, CPU inference. | Top $K \in \{1, 5, 10, 20\}$ | Recall@K, Precision@K, MRR |
| **E1** | **Structured Profile Dense** | Query vector generated from normalized `PatientClinicalProfile` concepts (diagnoses, stage, biomarkers). | Same model (`all-MiniLM-L6-v2`), same vector space (384-d), same DB index. | Top $K \in \{1, 5, 10, 20\}$ | Recall@K, Precision@K, MRR |
| **E2** | **Lexical BM25 Retrieval** | Exact keyword matching via Okapi BM25 ($k_1=1.2, b=0.75$) with clinical tokenization. | Inverted index over trial title, condition, summary, and criteria text. | Top $K \in \{1, 5, 10, 20\}$ | Recall@K, Precision@K, MRR |
| **E3** | **Hybrid Dense + Lexical (RRF)** | Rank-based score fusion combining E0 dense and E2 lexical rankings via Reciprocal Rank Fusion ($k_{rrf}=60$). | E0 dense retriever + E2 lexical retriever; deterministic tie-breaking. | Pool: $3K$, Truncated: $K$ | Recall@K, Precision@K, MRR, nDCG@K |
| **E4** | **Hybrid + Reranking** | Two-stage pipeline: E3 hybrid retrieval followed by second-stage clinical concept alignment reranking. | E3 candidate generator (pool $2K$) + deterministic reranker. | Pool: $2K$, Output: $K$ | Recall@K, Precision@K, MRR, nDCG@K |

---

## 3. Detailed Experiment Specifications

### Experiment E0: Baseline Dense Retrieval
- **Description:** Directly reproduces existing production behavior in `MatchingService._retrieve_matching_criteria`.
- **Query Input:** Raw `patient_note` string.
- **Model:** `sentence-transformers/all-MiniLM-L6-v2` (384-d).
- **Metric:** Cosine distance `<=>` in pgvector.
- **Candidate Pool:** Top $K$ trials filtered by `hospital_id`.

### Experiment E1: Structured Profile Dense Retrieval
- **Description:** Isolates the effect of structured patient extraction on dense vector representation.
- **Query Input:** Concatenation of normalized clinical facts extracted by Phase 4 `PatientClinicalProfile` (e.g., `"Primary: Stage IV lung adenocarcinoma. Biomarkers: EGFR exon 19 deletion. ECOG: 1"`).
- **Hypothesis to Test:** Extracting structured clinical facts filters conversational noise, producing a higher-density representation in semantic vector space.

### Experiment E2: Lexical BM25 Retrieval
- **Description:** Evaluates pure exact-match keyword retrieval using Okapi BM25.
- **Query Input:** Clinical keywords extracted from patient note.
- **Corpus:** Trial protocol fields (title, condition, brief_summary, and criteria text).
- **Hypothesis to Test:** Lexical matching guarantees exact hit for rare genomic acronyms (e.g., `T790M`, `KRAS G12C`) where dense vectors experience semantic drift.

### Experiment E3: Hybrid Dense + Lexical Fusion (RRF)
- **Description:** Evaluates whether combining dense semantic breadth with lexical precision improves recall and MRR over either method alone.
- **Fusion Formula:**
  $$\text{RRF}(d) = \frac{1}{60 + r_{\text{dense}}(d)} + \frac{1}{60 + r_{\text{lexical}}(d)}$$
- **Deterministic Ordering:** `ORDER BY rrf_score DESC, trial_id ASC`.

### Experiment E4: Hybrid Retrieval + Reranking
- **Description:** Evaluates two-stage candidate retrieval where an initial high-recall pool from E3 is scored and reordered by a fine-grained clinical alignment reranker.
- **Candidate Pool:** Top $2K$ candidates from E3.
- **Output:** Top $K$ reranked trials.

---

## 4. Evaluation & Reproducibility Protocol

1. **Benchmark Datasets:** When external clinical trial benchmark datasets (e.g., TREC Precision Medicine / Clinical Trials track) are ingested, all 5 experiments must be evaluated on the **exact same query set and qrels**.
2. **Deterministic Seed:** All experiments must execute with fixed random seeds (`seed=42`) and deterministic tie-breaking.
3. **No Test-Set Tuning:** Hyperparameters ($k_1=1.2, b=0.75, k_{rrf}=60$) remain fixed across evaluation runs.
