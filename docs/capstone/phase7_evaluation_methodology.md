# MedMatch Capstone — Phase 7: Evaluation Methodology & Statistical Protocol

**Document Version:** `1.0.0`  
**Phase:** 7 — RAG vs. Non-RAG Experimental Evaluation  
**Date:** September 2026  
**Status:** Evaluation Standard  

---

## 1. Overview & Evaluation Goals

This specification details the formal mathematical metrics, paired statistical tests, and reporting requirements for comparing **E5 (Non-RAG Baseline)** against **E6 (RAG-Grounded Reasoning)**.

The evaluation answers three core analytical questions:
1. **Classification Quality:** Does RAG improve criterion-level and trial-level Macro-$F_1$ without inflating false positives?
2. **Grounding & Safety:** Does RAG eliminate unsupported assertions and establish verified evidence provenance for clinical decisions?
3. **Statistical Significance:** Are observed differences between E5 and E6 statistically significant when evaluated on paired patient-trial benchmarks?

---

## 2. Quantitative Metric Formulations

### 2.1 Criterion-Level Metrics
Evaluated across classes $\mathcal{C} = \{\text{PASS}, \text{FAIL}, \text{UNKNOWN}\}$:

1. **Per-Class Precision, Recall, and $F_1$:**
   $$\text{Precision}_c = \frac{TP_c}{TP_c + FP_c}, \quad \text{Recall}_c = \frac{TP_c}{TP_c + FN_c}, \quad F1_c = \frac{2 \cdot \text{Precision}_c \cdot \text{Recall}_c}{\text{Precision}_c + \text{Recall}_c}$$

2. **Macro-Averaged $F_1$ (Criterion Macro-$F_1$):**
   $$\text{Macro-}F_1 = \frac{1}{|\mathcal{C}|} \sum_{c \in \mathcal{C}} F1_c$$

3. **UNKNOWN Rate ($UR$):**
   $$UR = \frac{|\{c \mid \hat{y}_c = \text{UNKNOWN}\}|}{N_{\text{criteria}}}$$

4. **Evidence Grounding Rate ($EGR$):**
   $$EGR = \frac{|\{c \mid \hat{y}_c \in \{\text{PASS}, \text{FAIL}\} \land \text{len}(c.\text{evidence\_citations}) \ge 1\}|}{|\{c \mid \hat{y}_c \in \{\text{PASS}, \text{FAIL}\}\}|}$$

5. **Unsupported Assertion Rate ($UAR$):**
   $$UAR = 1.0 - EGR$$

### 2.2 Trial-Level Metrics
Evaluated across classes $\mathcal{T} = \{\text{ELIGIBLE}, \text{INELIGIBLE}, \text{NEEDS\_REVIEW}\}$:
- **Trial-Level Macro-$F_1$, Precision, and Recall.**
- **Trial Confusion Matrix ($3 \times 3$):** Tracks transitions between ground truth and predicted status.
- **Safe Abstention Rate ($SAR$):** Percentage of ground-truth `NEEDS_REVIEW` cases correctly classified as `NEEDS_REVIEW`.

### 2.3 Operational & Computational Metrics
- **End-to-End Latency (ms):** Mean and 95th percentile execution time per patient query.
- **Token Efficiency:** Mean prompt and completion tokens per evaluation.
- **Retrieval Overhead:** Time spent in vector/lexical retrieval vs. reasoning.

---

## 3. Paired Statistical Evaluation Protocol

Because E5 and E6 evaluate the exact same patient-trial pairs, evaluations are naturally paired:

### 3.1 McNemar's Test for Paired Binary Decisions
For binary eligibility outcomes (e.g. `ELIGIBLE` vs `NOT_ELIGIBLE` where `NEEDS_REVIEW` is treated as negative/abstention):
$$\chi^2 = \frac{(|b - c| - 1)^2}{b + c}$$
where $b$ is the count of cases where E6 was correct and E5 was incorrect, and $c$ is the count where E5 was correct and E6 was incorrect.
- *Sample size prerequisite:* $b + c \ge 25$ required for valid asymptotic $\chi^2$ approximation. If $b + c < 25$, exact binomial test must be reported.

### 3.2 Bootstrap Confidence Intervals (95% CI)
- Resample patient cases with replacement ($B = 1,000$ iterations).
- Compute metric $\theta^{(b)}$ for each bootstrap sample.
- Report the percentile interval $[\theta_{0.025}, \theta_{0.975}]$ for Macro-$F_1$ and $\Delta F_1 = F_1(\text{E6}) - F_1(\text{E5})$.

### 3.3 Sample Size & Statistical Guardrails
- **Inadequate Sample Size Warning:** Statistical significance testing must **NOT** be run on tiny development fixtures ($N < 30$).
- **No Overclaiming:** If $p > 0.05$ or confidence intervals span zero, the report must state that no statistically significant difference was detected.

---

## 4. Current Status: Empirical Evaluation Pending

All metric functions, confusion matrix generators, and paired bootstrap harnesses are implemented in `scripts/run_phase7_experiment.py`. However, quantitative benchmarking remains **PENDING** real benchmark dataset ingestion.
