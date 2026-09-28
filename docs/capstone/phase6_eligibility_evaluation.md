# MedMatch Capstone — Phase 6: Eligibility Reasoning Evaluation Methodology
**Document Version:** `1.0.0`  
**Phase:** 6 — Eligibility Reasoning  

---

## 1. Evaluation Objectives

This document establishes the experimental and mathematical evaluation framework for clinical trial eligibility reasoning. The goal is to evaluate:
1. **Criterion-level accuracy:** How effectively does the reasoner classify atomic criteria into `PASS`, `FAIL`, and `UNKNOWN`?
2. **Trial-level correctness:** How accurately does the deterministic aggregator categorize trials into `ELIGIBLE`, `INELIGIBLE`, and `NEEDS_REVIEW`?
3. **Evidence grounding:** What percentage of `PASS` and `FAIL` decisions cite valid, verifiable clinical evidence spans?
4. **Epistemic safety:** Does the system safely classify missing, ambiguous, and contradictory clinical cases into `UNKNOWN` and `NEEDS_REVIEW` without hallucinated decisions?

> [!IMPORTANT]
> In accordance with capstone research rules, empirical benchmark evaluation remains **PENDING** until the external research benchmark (e.g. TREC Precision Medicine / clinical trial collections) is ingested into the repository. The 6-patient Phase 2 synthetic fixture is a development unit test fixture and **must not** be cited as empirical benchmark evidence.

---

## 2. Evaluation Metrics

### 2.1 Criterion-Level Classification Metrics
Evaluated across classes $\mathcal{C} = \{\text{PASS}, \text{FAIL}, \text{UNKNOWN}\}$:

1. **Per-Class Precision, Recall, and F1:**
   $$\text{Precision}_c = \frac{TP_c}{TP_c + FP_c}, \quad \text{Recall}_c = \frac{TP_c}{TP_c + FN_c}, \quad F1_c = \frac{2 \cdot \text{Precision}_c \cdot \text{Recall}_c}{\text{Precision}_c + \text{Recall}_c}$$

2. **Macro-Averaged F1 (Macro-F1):**
   $$\text{Macro-F1} = \frac{1}{|\mathcal{C}|} \sum_{c \in \mathcal{C}} F1_c$$

3. **Confusion Matrix ($3 \times 3$):**
   Rows represent ground-truth labels; columns represent predicted labels. Captures critical clinical error directions:
   - $\text{UNKNOWN} \to \text{PASS}$ (Over-optimistic hallucination error)
   - $\text{UNKNOWN} \to \text{FAIL}$ (Premature disqualification on silence)
   - $\text{FAIL} \to \text{PASS}$ (Catastrophic safety error: enrolling an ineligible patient)

### 2.2 Trial-Level Aggregation Metrics
Evaluated across classes $\mathcal{T} = \{\text{ELIGIBLE}, \text{INELIGIBLE}, \text{NEEDS\_REVIEW}\}$:
- **Trial Macro-F1, Precision, and Recall.**
- **Safe Abstention Rate:** Percentage of incomplete or contradictory cases correctly routed to `NEEDS_REVIEW`.

### 2.3 Evidence Grounding & Safety Metrics
1. **Evidence Grounding Rate ($EGR$):**
   $$EGR = \frac{|\{c \in \text{Evaluations} \mid c.\text{status} \in \{\text{PASS}, \text{FAIL}\} \land \text{len}(c.\text{evidence\_citations}) \ge 1\}|}{|\{c \in \text{Evaluations} \mid c.\text{status} \in \{\text{PASS}, \text{FAIL}\}\}|}$$
   Target: $100\%$ (enforced by schema validator).

2. **Hallucination Rate ($HR$):**
   Percentage of evaluations citing non-existent patient facts or incorrect character spans.

3. **Silence Inference Error Rate ($SIER$):**
   Percentage of unmentioned concepts erroneously classified as `ABSENT` rather than `UNKNOWN`.

---

## 3. Evaluation Splits & Protocol

Once the external research benchmark is ingested, evaluation will follow strict split discipline:
1. **Validation / Tuning Set:** Used for prompt engineering, rule refinement, and threshold alignment.
2. **Held-Out Test Set:** Evaluated exactly once. No hyperparameters or rules may be tuned on this set.
3. **Stress Test Set:** Evaluated on adversarial edge cases (negation scoping, temporal bounds, contradictory notes).

---

## 4. Current Status: Empirical Evaluation Pending

- All mathematical metrics, validation harnesses, and aggregation functions are implemented and verified via unit tests.
- Empirical benchmark tables and score reporting remain **PENDING** real benchmark dataset ingestion.
