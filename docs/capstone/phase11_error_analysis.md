# Phase 11 Error Analysis: Taxonomy & Failure Categorization

**Document ID:** ERR-ANALYSIS-P11  
**Phase:** Phase 11 — Evaluation & Ablation  
**Scope:** Unified Error Taxonomy, Failure Categorization, and Case-Level Audits Across E0–E4

---

## 1. Unified Error Taxonomy

Phase 11 consolidates the failure modes identified across Phases 3 through 10 into a standardized, deterministic error classification taxonomy:

```text
+---------------------------------------------------------------------------------------------------------+
|                                      MEDMATCH UNIFIED ERROR TAXONOMY                                     |
+----+------------------------------------------+---------------------+-----------------------------------+
| Code | Error Category                         | Upstream Source     | Definition                        |
+----+------------------------------------------+---------------------+-----------------------------------+
| E-R1 | RETRIEVAL_RECALL_MISS                  | Phase 5 (Retrieval) | Gold-eligible trial omitted from  |
|      |                                        |                     | top-k candidate pool              |
| E-R2 | FALSE_RETRIEVAL_RANK                   | Phase 5 (Retrieval) | Irrelevant trial ranked above     |
|      |                                        |                     | clinically relevant protocol      |
| E-C1 | CRITERION_POLARITY_MISCLASSIFICATION   | Phase 6 (Reasoning) | PASS classified as FAIL or vice   |
|      |                                        |                     | versa on explicit evidence        |
| E-C2 | TRI_STATE_REASONING_ERROR              | Phase 6 (Reasoning) | UNKNOWN classified as PASS/FAIL   |
|      |                                        |                     | or definitive evidence as UNKNOWN |
| E-C3 | TEMPORAL_REASONING_ERROR               | Phase 4 & Phase 6   | Washout interval arithmetic       |
|      |                                        |                     | calculation failure               |
| E-C4 | NUMERICAL_BOUNDARY_ERROR               | Phase 6 (Reasoning) | Lab threshold inequality          |
|      |                                        |                     | boundary failure (< vs <=)        |
| E-C5 | NEGATION_ASSERTION_ERROR               | Phase 4 & Phase 6   | Patient negative assertion treated|
|      |                                        |                     | as positive condition             |
| E-G1 | UNSUPPORTED_CLAIM                      | Phase 8 (Grounding) | Reasoning claim lacks verifiable  |
|      |                                        |                     | patient fact citation             |
| E-G2 | EVIDENCE_OMISSION                      | Phase 8 (Grounding) | Definitive verdict rendered with  |
|      |                                        |                     | zero evidence citations           |
| E-G3 | CONTRADICTION_UNSURFACED               | Phase 8 (Grounding) | Conflicting clinical records      |
|      |                                        |                     | not disclosed in evaluation       |
| E-U1 | UNCERTAINTY_ROUTING_ERROR              | Phase 9 (Review)    | Missing clinical information not  |
|      |                                        |                     | routed to NEEDS_REVIEW            |
| E-U2 | CONSERVATIVE_OVER_ROUTING              | Phase 9 (Review)    | Definitive case unnecessarily     |
|      |                                        |                     | routed to clinical review queue   |
| E-X1 | EXPLANATION_TRACEABILITY_FAILURE       | Phase 10 (Graph)    | Trial decision disconnected from  |
|      |                                        |                     | contributing criteria in graph    |
+----+------------------------------------------+---------------------+-----------------------------------+
```

---

## 2. Descriptive Language Protocol

> [!IMPORTANT]
> **CORRELATION VS. CAUSATION GUARDRAIL:**  
> In accordance with Phase 11 scientific reporting standards, all errors are strictly described using **"categorized as"** or **"classified under"** rather than **"caused by"**. Causal claims are prohibited unless isolated by a controlled counterfactual ablation.

---

## 3. Case-Level Error Categorization on Development Fixture

The 6-patient development fixture contains specific stress cases that provoke predictable error modes:

### Case 1: `SYN_P003` — Missing EGFR & Brain MRI Data
- **Ground Truth:** `NEEDS_REVIEW` (Missing critical biomarker assay & staging imaging).
- **Observed Prediction:** Categorized as `ELIGIBLE` under rule-based reasoner because missing data was not flagged by an explicit assertion absence rule.
- **Taxonomy Classification:** `E-U1: UNCERTAINTY_ROUTING_ERROR`.
- **Description:** Patient `SYN_P003` requires conservative clinical review due to pending EGFR mutation assays, but the rule engine evaluated non-mention as non-violation.

### Case 2: `SYN_P004` — Conflicting Biopsy Evidence
- **Ground Truth:** `NEEDS_REVIEW` (Conflicting tissue biopsy EGFR positive vs. liquid biopsy negative).
- **Observed Prediction:** Categorized as `ELIGIBLE`.
- **Taxonomy Classification:** `E-G3: CONTRADICTION_UNSURFACED`.
- **Description:** Multiple contradictory facts present in the patient record were not resolved prior to aggregation, allowing the positive fact to satisfy the inclusion requirement while omitting the contradiction.

### Case 3: `SYN_P005` — Numerical Boundary Condition
- **Ground Truth:** `INELIGIBLE` (Platelets $= 99 \times 10^9/\text{L}$ vs. $\ge 100 \times 10^9/\text{L}$ required).
- **Observed Prediction:** Categorized as `ELIGIBLE` in raw baseline E0 due to lack of numerical extraction.
- **Taxonomy Classification:** `E-C4: NUMERICAL_BOUNDARY_ERROR`.
- **Description:** Numerical inequality threshold failed in raw text baseline due to lack of structured laboratory parsing.

### Case 4: `SYN_P006` — Temporal Washout Interval
- **Ground Truth:** `INELIGIBLE` (Chemotherapy completed 27 days prior vs. $\ge 28$ days required).
- **Observed Prediction:** Categorized as `ELIGIBLE` in baseline E0.
- **Taxonomy Classification:** `E-C3: TEMPORAL_REASONING_ERROR`.
- **Description:** Temporal elapsed date calculation failed without structured date offsets from Phase 4.

---

## 4. Aggregate Error Summary Across Experiments

From `results/phase11/error_analysis.json`:

```text
+------------------------------------------------------------------------------------------------+
|                             CATEGORIZED ERROR COUNTS BY EXPERIMENT                             |
+------------------------------------+------+------+------+------+------+------------------------+
| Error Category                     | E0   | E1   | E2   | E3   | E4   | Taxonomy Mapping       |
+------------------------------------+------+------+------+------+------+------------------------+
| UNCERTAINTY_ROUTING_ERROR          | 2    | 2    | 2    | 2    | 2    | E-U1 (Missing/Conflict)|
| ELIGIBILITY_AGGREGATION_MISMATCH   | 2    | 2    | 2    | 2    | 2    | E-C1 (Boundary Cases)  |
| RETRIEVAL_RECALL_MISS              | 0    | 0    | 0    | 0    | 0    | E-R1 (Top-1 hit)       |
| EXPLANATION_TRACEABILITY_FAILURE   | 0    | 0    | 0    | 0    | 0    | E-X1 (100% Graph G1–G12)|
+------------------------------------+------+------+------+------+------+------------------------+
| Total Categorized Errors           | 4    | 4    | 4    | 4    | 4    | Out of 6 Encounters    |
+------------------------------------+------+------+------+------+------+------------------------+
```

### Analysis:
1. **Uncertainty Routing Omissions:** The 2 uncertainty routing errors correspond directly to `SYN_P003` (missing data) and `SYN_P004` (conflicting data). The evaluation engine correctly captures and logs these failures under Phase 9 error taxonomies.
2. **Boundary Discrepancies:** The 2 aggregation mismatches correspond to `SYN_P005` (platelet boundary) and `SYN_P006` (chemo washout).
3. **Traceability Stability:** Zero explanation traceability failures or graph corruption errors occurred across any experimental condition, confirming that Phase 10 graph synthesis remains robust.
