# Patient Clinical Information Extraction — Evaluation Design & Metrics Specification

## Executive Summary & Disclaimers

> [!WARNING]
> **CRITICAL SCIENTIFIC & METHODOLOGICAL DISCLAIMER:**
> **No empirical clinical extraction accuracy, precision, recall, or F1 scores are claimed in Phase 4.**
> The current system has established a deterministic structural validator and controlled synthetic development fixtures for schema verification. Validating empirical extraction accuracy requires a dedicated, clinically annotated gold-standard corpus (e.g., MIMIC-IV or double-annotated EHR clinical notes from clinical oncology trials).
>
> This document specifies the **formal evaluation methodology, metric definitions, matching tolerances, and annotation requirements** to be executed once a verified research benchmark is incorporated.

---

## 1. Implemented Structural Validation vs. Future Empirical Evaluation

| Dimension | Implemented Deterministic Validation (Phase 4) | Future Empirical Evaluation (Post-Benchmark) |
| :--- | :--- | :--- |
| **Object of Evaluation** | Syntactic, structural, and referential integrity of extracted patient profiles. | Semantic fidelity, clinical accuracy, and completeness against expert clinical annotations. |
| **Ground Truth Dependency** | Independent of external gold standard; operates on self-contained schema contracts. | Strictly dependent on dual-annotated, adjudicated clinical oncology records. |
| **Primary Mechanism** | Deterministic Pydantic validation, regex syntax checks, ID uniqueness, and offset boundary checks. | Precision, Recall, F1, exact/token-overlap span matching, and ontology normalization accuracy. |
| **Failure Modes Caught** | Missing fields, duplicate IDs, invalid operators, negative durations, start > end offsets, empty text. | Omission of critical diagnoses, hallucinated medications, inverted negation, temporal misinterpretations. |

---

## 2. Evaluation Levels & Metric Formulations

### Level 1: Clinical Fact Identification & Extraction

Evaluates whether individual clinical concepts (diagnoses, lab values, biomarkers, medications) mentioned in the narrative are detected.

#### Metrics
- **Fact Extraction Precision, Recall, and F1:**
  $$\text{Precision}_{\text{fact}} = \frac{|\text{True Positive Facts}|}{|\text{Predicted Facts}|}$$
  $$\text{Recall}_{\text{fact}} = \frac{|\text{True Positive Facts}|}{|\text{Gold Standard Facts}|}$$
  $$\text{F1}_{\text{fact}} = 2 \times \frac{\text{Precision}_{\text{fact}} \times \text{Recall}_{\text{fact}}}{\text{Precision}_{\text{fact}} + \text{Recall}_{\text{fact}}}$$
- **Span Boundary Matching:**
  - **Exact Match:** Verbatim string match of `source_text`.
  - **Relaxed / Token Overlap Match:** Token-level F1 $\ge 0.85$ or character IoU $\ge 0.80$ against gold span.

---

### Level 2: Assertion & Negation Classification

Evaluates whether each extracted fact is correctly classified as `affirmed`, `negated`, `possible`, `historical`, or `unknown`.

#### Metrics
- **Assertion Macro-F1:**
  $$\text{Macro-F1}_{\text{assertion}} = \frac{1}{|A|} \sum_{a \in A} F1_a$$
  Where $A = \{\text{affirmed}, \text{negated}, \text{possible}, \text{historical}, \text{unknown}\}$.
- **Negation Inversion Error Rate (Safety-Critical):**
  Measuring the frequency with which an explicitly negated condition (e.g., "no brain metastases") is incorrectly extracted as affirmed:
  $$\text{Negation Inversion Rate} = \frac{|\text{Negated Gold Facts classified as Affirmed}|}{|\text{Total Negated Gold Facts}|}$$
  **Target: 0.0%.**

---

### Level 3: Temporal Context & Anchoring Accuracy

Evaluates whether the temporal nature of facts (current vs. historical, dates, relative intervals, event anchors) is correctly determined.

#### Metrics
- **Temporality Classification Accuracy:** Multiclass accuracy across `TemporalityType` categories.
- **Relative Interval Offset Error:** Mean Absolute Error (MAE) in days between predicted `relative_days_offset` and gold standard offset when explicit reference dates are known:
  $$\text{MAE}_{\text{days}} = \frac{1}{N} \sum_{i=1}^N |\text{offset}_{\text{pred}}^{(i)} - \text{offset}_{\text{gold}}^{(i)}|$$
- **Washout Window Misclassification Rate:** Percentage of patients whose time-from-last-treatment is misclassified relative to standard trial washout thresholds (14, 28, 42 days).

---

### Level 4: Value & Unit Normalization Accuracy

Evaluates the extraction and normalization of quantified clinical metrics (lab values, vital signs, performance scores).

#### Metrics
- **Numeric Value Exact Match:** Percentage of quantitative measurements matching gold standard within clinical tolerance ($\pm 1\%$).
- **Unit Normalization Accuracy:** Percentage of units correctly mapped to standard UCUM representation.

---

### Level 5: Epistemic Uncertainty & Completeness

Evaluates whether the system appropriately distinguishes confirmed facts from unmentioned or uncertain variables.

#### Metrics
- **Uncertainty Classification F1:** Evaluated across `KNOWN`, `UNKNOWN`, `NOT_MENTIONED`, `UNCERTAIN`, `CONFLICTING`, `PATIENT_REPORTED`, and `CLINICIAN_DOCUMENTED`.
- **False Negative Assumption Rate (Absence Fallacy):**
  Frequency with which an unmentioned clinical variable (`NOT_MENTIONED`) is incorrectly marked as absent or negated. **Target: 0.0%.**

---

## 3. Protocol for Future Empirical Benchmarking

Before empirical extraction metrics can be reported, the research workflow requires:
1. **Annotation Guidelines:** Developing a comprehensive oncology clinical fact annotation guide following i2b2/n2c2 or cTAKES conventions.
2. **Double Blind Annotation:** Independent annotation by two board-certified oncology specialists.
3. **Inter-Annotator Agreement:** Measuring agreement ($\kappa \ge 0.85$ for assertion/uncertainty; F1 $\ge 0.90$ for entities).
4. **Adjudication & Data Freeze:** Formal reconciliation by a third senior oncologist and immutable JSONL serialization with SHA-256 checksums.
