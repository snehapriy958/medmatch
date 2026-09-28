# MedMatch Capstone — Hypotheses

> **Status:** Specification Document  
> **Phase:** 1 — Research Problem & Evaluation Design  
> **Author:** MedMatch Research Team  
> **Date:** September 2026  
> **Target System:** MedMatch Clinical Decision-Support Prototype

---

## 1. Scientific Protocol and Non-Claim Statement

In compliance with empirical machine learning and clinical evaluation standards:
- **No performance claim is assumed to be true *a priori*.**
- **No speculative numerical improvements** (e.g., "will improve F1 by 15%") are assigned.
- All hypotheses are formalized as paired **Null ($H_0$)** and **Alternative ($H_1$)** hypotheses, specifying independent variables, dependent metrics, and designated statistical tests.
- Hypotheses will be empirically tested in Phase 5 on a strictly held-out test split.

---

## 2. Formal Hypotheses

### Hypothesis 1: Retrieval-Grounded Reasoning vs. LLM-Only Baseline
- **Context:** Large language models queried zero-shot without explicit trial retrieval must either rely on memorized parametric knowledge or ingest arbitrary trial text.
- **Null Hypothesis ($H_{1,0}$):** There is no difference in trial-level eligibility classification macro-F1 between an evidence-grounded retrieval-augmented pipeline and a non-retrieval LLM baseline.
- **Alternative Hypothesis ($H_{1,1}$):** An evidence-grounded retrieval-augmented pipeline achieves a statistically significant improvement in trial-level eligibility classification macro-F1 compared to a non-retrieval LLM baseline on the benchmark dataset.
- **Independent Variable:** Reasoning architecture (Retrieval-Augmented Generation vs. Non-Retrieval LLM).
- **Dependent Metric:** Macro-averaged $F_1$ score across `{ELIGIBLE, INELIGIBLE, NEEDS_REVIEW}`.
- **Statistical Test:** McNemar's test for paired classification accuracy and 95% bootstrap confidence intervals for Macro-$F_1$.

---

### Hypothesis 2: Hybrid Retrieval vs. Pure Dense Retrieval
- **Context:** Dense vector models (such as `MiniLM-L6-v2`) capture broad semantic themes but frequently suffer from "lexical blindness" regarding specific gene mutations (e.g., *BRAF V600E* vs. *BRAF wild-type*), exact staging codes (*T3N1M0*), and laboratory thresholds (*ANC $\ge 1500/\mu\text{L}$*).
- **Null Hypothesis ($H_{2,0}$):** Hybrid retrieval (sparse BM25 + dense semantic embeddings) yields no improvement in retrieval recall or ranking over pure dense retrieval for clinical trial criteria containing exact medical terminology, biomarkers, or numerical cutoffs.
- **Alternative Hypothesis ($H_{2,1}$):** Hybrid retrieval achieves higher Recall@K ($k \in \{5, 10, 20\}$) and Mean Reciprocal Rank (MRR) than pure dense retrieval on trial criteria characterized by exact lexical terminology, genomic variants, and numerical lab values.
- **Independent Variable:** Candidate retrieval mechanism (Dense only vs. Hybrid BM25 + Dense).
- **Dependent Metric:** Recall@5, Recall@10, Recall@20, MRR, nDCG@10.
- **Statistical Test:** Wilcoxon signed-rank test on paired per-query ranking metrics across test queries.

---

### Hypothesis 3: Structured Clinical Profile vs. Raw Unstructured Clinical Note
- **Context:** The Phase 0 audit confirmed that the current MedMatch backend passes raw unstructured notes directly into the prompt without extracting structured clinical entities, despite the existence of patient demographic and clinical fields.
- **Null Hypothesis ($H_{3,0}$):** Extracting and presenting a structured clinical profile (demographics, normalized conditions, biomarker statuses, and lab values) alongside the raw note does not alter the eligibility classification error rate compared to feeding raw clinical notes alone.
- **Alternative Hypothesis ($H_{3,1}$):** Providing a structured clinical profile alongside the clinical narrative significantly reduces false-positive eligibility determinations (ineligible patients misclassified as eligible) and improves classification macro-F1.
- **Independent Variable:** Patient representation format (Raw clinical narrative alone vs. Structured profile + narrative).
- **Dependent Metric:** False Positive Rate (FPR), Precision for `ELIGIBLE`, Macro-$F_1$.
- **Statistical Test:** Paired Permutation Test on classification error distributions.

---

### Hypothesis 4: Evidence Grounding and Provenance Attribution
- **Context:** Monolithic LLM prompts can output accurate-sounding decisions supported by plausible but ungrounded or hallucinated assertions.
- **Null Hypothesis ($H_{4,0}$):** Enforcing explicit character-level evidence span extraction and criterion-level provenance does not decrease the rate of unsupported assertions compared to monolithic prompt reasoning.
- **Alternative Hypothesis ($H_{4,1}$):** A modular architecture requiring character-level text span citation for each criterion evaluation achieves a significantly higher Grounded Decision Rate and a lower Unsupported Claim Rate than monolithic LLM generation.
- **Independent Variable:** Provenance constraint (Unconstrained monolithic generation vs. Span-grounded criterion evaluation).
- **Dependent Metric:** Grounded Decision Rate (%), Unsupported Claim Rate (%), Evidence Coverage (%).
- **Statistical Test:** Paired t-test on per-case Grounded Decision Rates; Fisher's Exact Test on unsupported claim incidence.

---

### Hypothesis 5: Tri-State Criterion Reasoning and Uncertainty Modeling
- **Context:** Real-world patient records frequently omit specific laboratory values, genetic test results, or prior therapy details. Forcing a binary decision (`ELIGIBLE` vs. `INELIGIBLE`) leads to risky speculative classifications.
- **Null Hypothesis ($H_{5,0}$):** Modeling criterion evaluations as tri-state values (`PASS`, `FAIL`, `UNKNOWN`) aggregated via formal clinical rules does not improve calibration or decision safety over a system forced to output binary eligibility decisions.
- **Alternative Hypothesis ($H_{5,1}$):** A tri-state criterion evaluation framework that surfaces `NEEDS_REVIEW` when critical criteria are unknown achieves superior expected calibration error (ECE) and significantly reduces unsafe false-positive classifications on incomplete clinical profiles.
- **Independent Variable:** Decision space and aggregation logic (Binary forced classification vs. Tri-state criterion aggregation).
- **Dependent Metric:** Expected Calibration Error (ECE), Selective Classification Risk-Coverage curve, False Positive Rate on incomplete patient records.
- **Statistical Test:** DeLong test on risk-coverage curves; Brier score comparison.

---

## 3. Summary of Hypotheses and Variable Specifications

| ID | Focus | Independent Variable | Primary Dependent Metric | Baseline Comparison |
|---|---|---|---|---|
| **H1** | System Utility | Retrieval-Augmented vs. LLM-only | Classification Macro-$F_1$ | Zero-shot LLM without retrieval |
| **H2** | Retrieval Quality | Hybrid (BM25 + Dense) vs. Dense | Recall@K, MRR | Current `all-MiniLM-L6-v2` dense retrieval |
| **H3** | Patient Input | Structured Profile + Note vs. Note alone | False Positive Rate, Macro-$F_1$ | Current raw `patient_note` input |
| **H4** | Grounding | Span-grounded reasoning vs. Monolithic | Unsupported Claim Rate | Current monolithic prompt (`trial_matching_prompt.py`) |
| **H5** | Uncertainty | Tri-state aggregation vs. Binary forced | Calibration Error (ECE), Safety Recall | Uncalibrated binary classification |
