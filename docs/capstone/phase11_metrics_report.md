# Phase 11 Metrics Specification & Evaluation Report

**Document ID:** METRICS-REP-P11  
**Phase:** Phase 11 — Evaluation & Ablation  
**Scope:** Mathematical Formulations, Zero-Denominator Behaviors, and Development-Fixture Metrics Across E0–E4

---

## 1. Overview of Evaluation Dimensions

The Phase 11 evaluation engine assesses systems across five core dimensions:
1. **Candidate Retrieval ($R_k$):** Quality of protocol candidate ranking.
2. **Eligibility Reasoning ($E$):** Trial-level and criterion-level clinical classification performance.
3. **Evidence Grounding ($G$):** Faithfulness and citation precision of generated reasoning.
4. **Clinical Uncertainty ($U$):** Calibration and routing of ambiguous cases to human review.
5. **Explainability & Traceability ($X$):** End-to-end evidence graph integrity and decision auditability.

---

## 2. Formal Metric Definitions & Zero-Denominator Safeguards

### 2.1. Candidate Retrieval Metrics

| Metric | Mathematical Formula | Numerator / Denominator | Unit of Analysis | Zero-Denominator Behavior |
|:---|:---|:---|:---|:---|
| **Recall@K** | $\frac{\vert \text{TopK}(q) \cap \text{Rel}(q) \vert}{\vert \text{Rel}(q) \vert}$ | Retrieved relevant trials / Total gold relevant trials | Query (Patient) | Returns $1.0$ if $\vert \text{Rel}(q) \vert = 0$ and top-k empty; else $0.0$. |
| **Precision@K** | $\frac{\vert \text{TopK}(q) \cap \text{Rel}(q) \vert}{K}$ | Retrieved relevant trials in top-k / $K$ | Query (Patient) | Returns $0.0$ if $K = 0$. |
| **MRR** | $\frac{1}{\vert Q \vert} \sum_{q \in Q} \frac{1}{\text{rank}_1(q)}$ | Sum of reciprocal ranks of first hit / Total queries | Query set | Returns $0.0$ if $\vert Q \vert = 0$. |
| **nDCG@K** | $\frac{\text{DCG}@K}{\text{IDCG}@K}$ | Discounted cumulative gain / Ideal DCG | Query (Patient) | Returns $0.0$ if $\text{IDCG} = 0$. |

### 2.2. Eligibility Classification Metrics

Evaluated across three trial classes ($\mathcal{C} = \{\text{ELIGIBLE}, \text{INELIGIBLE}, \text{NEEDS\_REVIEW}\}$) and criterion states ($\{\text{PASS}, \text{FAIL}, \text{UNKNOWN}\}$):

| Metric | Mathematical Formula | Numerator / Denominator | Zero-Denominator Behavior |
|:---|:---|:---|:---|
| **Accuracy** | $\frac{\sum_{c \in \mathcal{C}} \text{TP}_c}{N}$ | Correct trial predictions / Total trials evaluated | Returns $0.0$ if $N = 0$. |
| **Macro-Precision** | $\frac{1}{\vert \mathcal{C} \vert} \sum_{c} \frac{\text{TP}_c}{\text{TP}_c + \text{FP}_c}$ | Unweighted mean of per-class precision | Returns $0.0$ for classes with $\text{TP}_c + \text{FP}_c = 0$. |
| **Macro-Recall** | $\frac{1}{\vert \mathcal{C} \vert} \sum_{c} \frac{\text{TP}_c}{\text{TP}_c + \text{FN}_c}$ | Unweighted mean of per-class recall | Returns $0.0$ for classes with $\text{TP}_c + \text{FN}_c = 0$. |
| **Macro-$F_1$** | $\frac{1}{\vert \mathcal{C} \vert} \sum_{c} \frac{2 \cdot P_c \cdot R_c}{P_c + R_c}$ | Unweighted mean of per-class harmonic mean | Returns $0.0$ for classes with $P_c + R_c = 0$. |

### 2.3. Evidence Grounding Metrics

| Metric | Mathematical Formula | Zero-Denominator Behavior |
|:---|:---|:---|
| **Claim Support Rate (CSR)** | $\frac{\text{Supported Claims}}{\text{Total Claims}}$ | Returns $1.0$ if total claims $= 0$. |
| **Unsupported Claim Rate (UCR)** | $\frac{\text{Unsupported Claims}}{\text{Total Claims}}$ | Returns $0.0$ if total claims $= 0$. |
| **Contradiction Rate (CR)** | $\frac{\text{Contradicted Claims}}{\text{Total Claims}}$ | Returns $0.0$ if total claims $= 0$. |
| **Citation Validity Rate (CVR)** | $\frac{\text{Valid Character Spans}}{\text{Total Citations}}$ | Returns $1.0$ if total citations $= 0$. |
| **Evidence Coverage (EC)** | $\frac{\text{Criteria with Grounded Evidence}}{\text{Total Criteria Evaluated}}$ | Returns $1.0$ if evaluated criteria $= 0$. |
| **Grounding Score** | $\max(0, \min(1, 0.4 \cdot \text{CSR} + 0.3 \cdot \text{CVR} + 0.3 \cdot \text{EC} - 0.5 \cdot \text{CR} - 0.3 \cdot \text{UCR}))$ | Scaled in $[0.0, 1.0]$. |

### 2.4. Clinical Uncertainty & Review Metrics

| Metric | Mathematical Formula | Zero-Denominator Behavior |
|:---|:---|:---|
| **Uncertainty Rate** | $\frac{\text{Evaluations with Unknowns}}{\text{Total Evaluations}}$ | Returns $0.0$ if total evaluations $= 0$. |
| **Review Routing Rate** | $\frac{\text{Cases Routed to NEEDS\_REVIEW}}{\text{Total Evaluations}}$ | Returns $0.0$ if total evaluations $= 0$. |
| **Unresolved Uncertainty Rate** | $\frac{\text{Over-routed Uncertain Cases}}{\text{Total Evaluations}}$ | Returns $0.0$ if total evaluations $= 0$. |

### 2.5. Explainability & Evidence Graph Metrics

| Metric | Definition | Zero-Denominator Behavior |
|:---|:---|:---|
| **Decision Traceability Rate (DTR)** | Fraction of trial decisions where all contributing evaluations resolve in graph | Returns $1.0$ if total decisions $= 0$. |
| **Criterion Traceability Rate (CTR)** | Fraction of criteria evaluations linking to patient fact nodes | Returns $1.0$ if total criteria $= 0$. |
| **Provenance Validity Rate (PVR)** | Fraction of evidence nodes with verified character offsets $\ge -1$ | Returns $1.0$ if total evidence nodes $= 0$. |
| **Graph Integrity Rate (GIR)** | Fraction of synthesized graphs adhering to invariants G1–G12 | Returns $1.0$ if total graphs $= 0$. |

---

## 3. Observed Development-Fixture Metrics (E0–E4)

The table below reports exact observed values produced by running [`scripts/run_phase11_pipeline.py`](file:///C:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/run_phase11_pipeline.py) against the local development test fixture ($n=6$ patient encounters, $1$ trial protocol, $48$ criterion evaluations):

> [!NOTE]
> **DEVELOPMENT-FIXTURE OBSERVATION ONLY:**  
> These metrics validate the end-to-end mathematical execution of the evaluation engine. Because the evaluation cohort is small ($n=6$), these numbers must **not** be cited as clinical benchmark performance.

```text
+-------------------------------------------------------------------------------------------------------------+
|                                  OBSERVED DEVELOPMENT FIXTURE METRICS                                      |
+------------------------------+-------------+---------------------+-------------+--------------+-------------+
| Metric                       | E0 Baseline | E1 Structured Prof  | E2 Dense RAG| E3 Hybrid RAG| E4 Reranked |
+------------------------------+-------------+---------------------+-------------+--------------+-------------+
| Sample Size (Patients)       | 6           | 6                   | 6           | 6            | 6           |
| Retrieval Recall@5           | 0.5000      | 0.5000              | 0.5000      | 0.5000       | 0.5000      |
| Retrieval MRR                | 0.5000      | 0.5000              | 0.5000      | 0.5000       | 0.5000      |
| Trial Eligibility Accuracy   | 1.0000      | 1.0000              | 1.0000      | 1.0000       | 1.0000      |
| Trial Macro-F1               | 1.0000      | 1.0000              | 1.0000      | 1.0000       | 1.0000      |
| Criterion Accuracy           | 0.9375      | 1.0000              | 1.0000      | 1.0000       | 1.0000      |
| Criterion Macro-F1           | 0.8762      | 1.0000              | 1.0000      | 1.0000       | 1.0000      |
| Grounding Score              | 0.9187      | 0.9875              | 0.9875      | 0.9875       | 0.9875      |
| Hallucination Rate           | 0.0625      | 0.0000              | 0.0000      | 0.0000       | 0.0000      |
| Evidence Coverage            | 0.8750      | 0.9583              | 0.9583      | 0.9583       | 0.9583      |
| Decision Traceability Rate   | 1.0000      | 1.0000              | 1.0000      | 1.0000       | 1.0000      |
| Criterion Traceability Rate  | 0.0000      | 0.8333              | 0.8333      | 0.8333       | 0.8333      |
| Provenance Validity Rate     | 1.0000      | 1.0000              | 1.0000      | 1.0000       | 1.0000      |
| Graph Integrity Rate (G1–G12)| 1.0000      | 1.0000              | 1.0000      | 1.0000       | 1.0000      |
+------------------------------+-------------+---------------------+-------------+--------------+-------------+
```

---

## 4. Observations & Constraints

1. **Ablation Sensitivity between E0 and E1:**
   - E0 (audited production baseline using raw clinical note and PromptBuilder prompt reasoning) achieves **0.9375 criterion accuracy** (45/48 criteria correct) and **0.0000 criterion traceability** because raw narrative text lacks explicit, structured fact identifiers.
   - E1 (structured `PatientClinicalProfile`) improves criterion accuracy to **1.0000** (48/48 correct), grounding score from **0.9187 to 0.9875** ($\Delta = +0.0688$), and criterion traceability from **0.0000 to 0.8333** ($\Delta = +0.8333$).
2. **Retrieval Invariance on Single-Trial Fixture ($N=1$):**
   - Because the candidate pool contains exactly 1 trial protocol (`NCT02484404`), all retrieval methods (Dense, Hybrid RRF, and Reranking) rank that single protocol at Rank 1.
   - Consequently, retrieval metrics are identical across E0–E4 purely due to candidate pool size constraint ($N=1$).
3. **Downstream Classification on Synthetic Patients:**
   - The 6 synthetic patients in `data/fixtures/patients.json` were specifically hand-crafted in Phase 2 to test each of the 8 criteria of `NCT02484404`. Once structured facts are provided (E1–E4), the reasoner evaluates all 8 criteria with 100% agreement with ground truth.
   - Distinct execution paths are verified by citations: E1 contains zero retrieval citations; E2 cites `dense:trial:NCT02484404`; E3 cites `hybrid_rrf:trial:NCT02484404`; E4 cites `hybrid_reranked:trial:NCT02484404`.
4. **Development-Fixture Guardrails:**
   - All results remain strictly classified as `DEVELOPMENT/TEST FIXTURE ONLY`.
   - Sample size $n=6$ is statistically insufficient for hypothesis testing. No claims of clinical superiority or generalizable accuracy improvements are asserted.
