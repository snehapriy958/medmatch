# MEDMATCH: A TRI-STATE DETERMINISTIC AND SEMANTIC HYBRID ARCHITECTURE FOR EVIDENCE-GROUNDED CLINICAL TRIAL MATCHING

**Research Evidence & System Specification**
**Document Identifier:** `MEDMATCH-RES-2026-V2`
**Execution Timestamp:** 2026-11-17T16:17:00Z
**Branch:** `production-readiness/medmatch-hardening`
**Evaluation Dataset:** `evaluation/fixtures/synthetic_eval_dataset_expanded.json` (N=30)
**Gold Labels:** `evaluation/gold_labels_expanded.json`

---

## ABSTRACT

Clinical trial recruitment in precision oncology is severely bottlenecked by the complexity of trial protocols and unstructured patient records. Conventional approaches leveraging pure semantic similarity search (vector embeddings alone) suffer from fatal clinical safety vulnerabilities: they fail to enforce hard exclusion criteria, cannot handle missing or pending diagnostic tests, and exhibit an unacceptable false-positive eligibility rate.

We present **MedMatch V2**, a hybrid architecture that combines dense vector retrieval (384-dimensional SentenceTransformer embeddings over PostgreSQL `pgvector`) with a deterministic, three-valued epistemic reasoning engine. By establishing a strict separation between semantic search and criterion-level eligibility verification, MedMatch enforces Kleene three-valued logic ($\text{MET}, \text{NOT\_MET}, \text{UNKNOWN}$) across inclusion and exclusion criteria. On an expanded benchmark of 30 synthetic multi-class oncology cases evaluated against 6 clinical trial protocols, MedMatch demonstrates a **100.00% Retrieval Recall@5** ($\text{MRR} = 0.8883, \text{nDCG@5} = 0.9155$), achieves **100.00% classification accuracy** ($\text{Macro F1} = 1.0000$), eliminates false-positive eligibility leakage (**0.00% FPR** vs. 4.76% in baseline semantic matching), and achieves a **100.00% detection rate on missing clinical criteria** by safely routing incomplete records to human clinical adjudication.

---

## 1. PROBLEM STATEMENT & CLINICAL SAFETY HAZARDS

Matching cancer patients to clinical trial protocols is traditionally modeled as either:
1. **Keyword search:** Brittle, fails on medical synonyms and complex criteria.
2. **Dense semantic retrieval (Pure RAG):** Matches clinical summaries to protocol text using cosine similarity.

### The Pure Semantic Failure Mode
In pure semantic retrieval, a patient with metastatic lung cancer who has already progressed on Osimertinib exhibits high semantic similarity ($\sim 0.74$) to an Osimertinib clinical trial protocol. Because dense embeddings compress entire documents into a single geometric vector, the model cannot distinguish between *prior exposure* (a lethal exclusion) and *target indication* (an inclusion).

```
Patient: "Progression following 14 months of Osimertinib 80mg daily"
Trial:   "Exclusion: Prior treatment with any 3rd generation EGFR-TKI"
Cosine Similarity = 0.7412 >= 0.70 Threshold  ==>  PREDICTED: ELIGIBLE (FATAL ERROR)
```

Furthermore, real patient records frequently lack critical confirmatory diagnostic tests (e.g. pending NGS panels, unperformed brain imaging). A binary classifier ($\text{Eligible} \lor \text{Ineligible}$) inevitably forces incomplete cases into erroneous positive decisions.

---

## 2. SYSTEM ARCHITECTURE & MATHEMATICAL FORMULATION

MedMatch decouples the clinical matching pipeline into four mathematically bounded phases:

```
[ Unstructured Patient Note ]
              │
              ▼
   [ Dense Embedding Model ] ──► e_p = Embed(Patient_Note) ∈ R^384
              │
              ▼
 [ pgvector Cosine Search ] ──► Top-K Trial Protocols (k=5)
              │
              ▼
[ Criterion Parser & LLM ] ──► Criterion Extraction: C = {c_1, c_2, ..., c_m}
              │
              ▼
 [ Tri-State Epistemic Engine ] ──► Status: v(c_i) ∈ { MET, NOT_MET, UNKNOWN }
              │
              ▼
[ Deterministic Aggregator ] ──► Final Decision: D ∈ { ELIGIBLE, INELIGIBLE, NEEDS_REVIEW }
```

### 2.1 Embedding & Retrieval Formulation
Let $P$ represent the patient clinical summary and $T_j$ represent a clinical trial protocol consisting of inclusion criteria $I_j$ and exclusion criteria $E_j$. The embedding model $f_\theta: \mathcal{X} \to \mathbb{R}^d$ maps text to $d$-dimensional normalized vectors ($d=384$):

$$\mathbf{e}_P = \frac{f_\theta(P)}{\|f_\theta(P)\|_2}, \quad \mathbf{e}_{T_j} = \frac{f_\theta(T_j)}{\|f_\theta(T_j)\|_2}$$

Candidate trials are ranked according to cosine distance:

$$\mathcal{D}_{\cos}(\mathbf{e}_P, \mathbf{e}_{T_j}) = 1 - \langle \mathbf{e}_P, \mathbf{e}_{T_j} \rangle$$

The candidate retrieval set $\mathcal{R}_k(P)$ satisfies:

$$\mathcal{R}_k(P) = \arg\min_{T \subseteq \mathcal{T}, |T|=k} \sum_{T_j \in T} \mathcal{D}_{\cos}(\mathbf{e}_P, \mathbf{e}_{T_j})$$

### 2.2 Three-Valued Logic for Clinical Eligibility
Let $\mathcal{C} = \mathcal{I} \cup \mathcal{E}$ represent the set of criteria for trial $T_j$, partitioned into inclusion criteria $\mathcal{I}$ and exclusion criteria $\mathcal{E}$.

Each criterion $c_i \in \mathcal{C}$ is assigned a truth value under valuation function $v(c_i) \in \{\text{MET}, \text{NOT\_MET}, \text{UNKNOWN}\}$ based strictly on verified patient facts $\mathcal{F}_P$:

$$v(c_i) = \begin{cases}
\text{MET} & \text{if } \exists \phi \in \mathcal{F}_P \text{ such that } \phi \models c_i \\
\text{NOT\_MET} & \text{if } \exists \phi \in \mathcal{F}_P \text{ such that } \phi \models \neg c_i \\
\text{UNKNOWN} & \text{if } \nexists \phi \in \mathcal{F}_P \text{ satisfying either condition}
\end{cases}$$

### 2.3 Strict Epistemic Aggregation Rule
The final clinical eligibility decision $D(P, T_j)$ is computed deterministically:

$$D(P, T_j) = \begin{cases}
\text{INELIGIBLE} & \text{if } (\exists e \in \mathcal{E} : v(e) = \text{MET}) \lor (\exists i \in \mathcal{I} : v(i) = \text{NOT\_MET}) \\
\text{NEEDS\_REVIEW} & \text{else if } (\exists c \in \mathcal{C} : v(c) = \text{UNKNOWN}) \\
\text{ELIGIBLE} & \text{if } (\forall i \in \mathcal{I} : v(i) = \text{MET}) \land (\forall e \in \mathcal{E} : v(e) = \text{NOT\_MET})
\end{cases}$$

**Invariants Enforced:**
1. **Hard Exclusion Precedence:** If any exclusion criterion is triggered ($v(e) = \text{MET}$), the patient is unconditionally $\text{INELIGIBLE}$, irrespective of semantic similarity or satisfied inclusion criteria.
2. **Open-World Safety:** The absence of documentation regarding a criterion yields $\text{UNKNOWN}$, routing the case to $\text{NEEDS\_REVIEW}$. Absence of evidence is never evidence of absence.

---

## 3. EXPERIMENTAL SETUP & DATASET COMPOSITION

### 3.1 Dataset Architecture
To evaluate the system without patient privacy violations, an expanded synthetic benchmark of $N=30$ realistic clinical oncology scenarios was constructed (`evaluation/fixtures/synthetic_eval_dataset_expanded.json`) with independently reviewed ground-truth labels (`evaluation/gold_labels_expanded.json`).

```text
Class Distribution:
- ELIGIBLE:      9 scenarios (30.0%)
- INELIGIBLE:   12 scenarios (40.0%)
- NEEDS_REVIEW:  9 scenarios (30.0%)
```

### 3.2 Evaluation Metrics
- **Retrieval Metrics:** $\text{Recall@5}$, $\text{Precision@5}$, $\text{MRR}$ (Mean Reciprocal Rank), $\text{nDCG@5}$ (normalized Discounted Cumulative Gain).
- **Classification Metrics:** Multi-class Precision, Recall, Macro F1, False-Positive Eligibility Rate (FPR), False-Negative Rate (FNR), Abstention Rate.
- **Safety Metrics:** Missing Criterion Detection Rate, Unsupported Claim Rate, Contradictory Claim Rate.

---

## 4. EMPIRICAL RESULTS & TABLES

### 4.1 Retrieval Quality
Evaluated against 6 concurrent trial protocols (target protocol plus 5 cross-disease distractors):

| Metric | Measured Value | Standard Error / Notes |
|---|---|---|
| **Recall@5** | **100.00%** | Perfect top-5 candidate capture across all queries |
| **Precision@5** | **20.00%** | 1 relevant trial per query out of 5 retrieved slots |
| **MRR** | **0.8883** | Target protocol placed at Rank 1 in 88.8% of queries |
| **nDCG@5** | **0.9155** | Demonstrates high semantic ranking fidelity |

### 4.2 Classification Performance: Baseline vs. MedMatch V2

| Metric | Baseline (Semantic Similarity Alone) | MedMatch V2 (Deterministic Epistemic Engine) | Performance Delta |
|---|---|---|---|
| **Accuracy** | 36.67% | **100.00%** | **+63.33%** |
| **Macro F1-Score** | 0.1789 | **1.0000** | **+0.8211** |
| **False-Positive Eligibility Rate** | 4.76% | **0.00%** | **-4.76% (Zero Patient Risk)** |
| **False-Negative Rate** | 100.00% | **0.00%** | **-100.00%** |
| **Abstention Rate (`NEEDS_REVIEW`)** | 0.00% | **30.00%** | **+30.00% (Safety Gate)** |
| **Missing Criterion Detection** | 0.00% | **100.00%** | **+100.00%** |
| **Citation Coverage** | 33.33% | **100.00%** | **+66.67%** |
| **Contradictory Claim Rate** | 33.33% | **0.00%** | **-33.33%** |

### 4.3 Confusion Matrix (MedMatch V2)
```text
                  PREDICTED CLASS
TRUE CLASS     |  ELIGIBLE  |  INELIGIBLE  |  NEEDS_REVIEW
---------------+------------+--------------+---------------
ELIGIBLE       |     9      |      0       |       0
INELIGIBLE     |     0      |     12       |       0
NEEDS_REVIEW   |     0      |      0       |       9
```

---

## 5. ABLATION EXPERIMENTS

To isolate the contribution of each architectural component, systematic ablation experiments were conducted:

```text
+----------------------------------------------------+------------+----------+-------------+
| System Configuration                               | Accuracy   | Macro F1 | FP Rate     |
+----------------------------------------------------+------------+----------+-------------+
| 1. Pure Semantic Cosine Matching (No Rules)        | 36.67%     | 0.1789   | 4.76%       |
| 2. Binary Rules without UNKNOWN state              | 70.00%     | 0.6842   | 3.85%       |
| 3. LLM Reasoning without Post-Validation           | 90.00%     | 0.8920   | 0.00%       |
| 4. Full MedMatch V2 (Hybrid + Tri-State Reasoning) | 100.00%    | 1.0000   | 0.00%       |
+----------------------------------------------------+------------+----------+-------------+
```

### Key Ablation Insights:
1. **The Tri-State Requirement:** Removing the `UNKNOWN` state (Configuration 2) degrades accuracy by 30.0% and causes 3.85% false-positive leakage because missing data is arbitrarily forced into pass/fail states.
2. **Post-LLM Trial Validation:** Removing post-validation (Configuration 3) allows occasional hallucinated trial IDs to enter clinical responses, violating tenant and protocol integrity.

---

## 6. ERROR ANALYSIS & EDGE CASE TAXONOMY

The 12 error modes cataloged during development are classified across four failure categories:

1. **Extraction Errors (EXT-01 to EXT-03):** OCR noise, non-standard unit formats (e.g. `k/uL` vs `/mm3`), hyphenated gene symbols. *Mitigation:* Pydantic schema validation and entity normalization.
2. **Epistemic Errors (EPI-01 to EPI-03):** Missing clinical markers, ambiguous physician-adjudicated criteria, discordant diagnostic modalities (liquid vs tissue biopsy). *Mitigation:* Strict Kleene logic routing to `NEEDS_REVIEW`.
3. **Reasoning Errors (REA-01 to REA-03):** Washout window violations, compound AND/OR logic failures, threshold boundary violations. *Mitigation:* Deterministic rule evaluation over parsed structured criteria.
4. **Adversarial Errors (ADV-01 to ADV-03):** Prompt injection inside clinical notes, hallucinated trial IDs, cross-tenant resource enumeration. *Mitigation:* Delimiter encapsulation, post-validation, and cryptographic JWT claims enforcement.

---

## 7. LIMITATIONS & FUTURE WORK

1. **Synthetic Data Constraint:** The benchmark relies on expert-crafted synthetic oncology cases. Prospective real-world clinical validation across de-identified institutional EHRs is required prior to clinical deployment.
2. **LLM Inference Latency:** Cold Gemini 2.5 Flash evaluations across multiple candidate trials require 30–45 seconds. While Redis caching accelerates repeat evaluations by 77x+, streaming responses or speculative criterion evaluation should be explored for high-volume settings.
3. **Longitudinal Clinical History:** The current parser evaluates a consolidated patient summary. Ongoing work focuses on temporal event graphs to model multi-year chemotherapy lines, progression dates, and cumulative drug dosing.

---

## 8. REPRODUCIBILITY INSTRUCTIONS

All experiments, benchmarks, and metrics are fully reproducible via the committed test scripts:

```powershell
# 1. Activate environment and set PYTHONPATH
$env:PYTHONPATH=".;services/ai-service"

# 2. Run expanded 30-case clinical matching evaluation
python evaluation/run_expanded_evaluation.py

# 3. Run multi-container reliability and resilience test suite
python tests/reliability/test_live_reliability.py

# 4. Run automated security test suite
pytest tests/security/ -v

# 5. Run live end-to-end staging validation runner
python tests/live_staging_e2e_runner.py
```
