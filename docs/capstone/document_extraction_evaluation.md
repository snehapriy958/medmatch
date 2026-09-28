# Clinical Trial Document Extraction — Evaluation Design & Metrics Specification

## Executive Summary & Disclaimers

> [!WARNING]
> **CRITICAL SCIENTIFIC & METHODOLOGICAL DISCLAIMER:**
> **No empirical extraction accuracy, precision, recall, or F1 scores are claimed in Phase 3.**
> The current system has established a deterministic structural validator and synthetic development fixtures for schema verification. Validating empirical extraction accuracy requires a dedicated, clinically annotated gold-standard corpus (e.g., ClinicalTrials.gov protocols annotated by double-blind clinical experts).
>
> This document specifies the **formal evaluation methodology, metric definitions, matching tolerances, and annotation requirements** to be executed once a verified research benchmark is incorporated.

---

## 1. Implemented Validation vs. Future Empirical Evaluation

It is essential to distinguish the two paradigms:

| Dimension | Implemented Deterministic Validation (Phase 3) | Future Empirical Evaluation (Post-Benchmark) |
| :--- | :--- | :--- |
| **Object of Evaluation** | Syntactic, structural, and referential integrity of extracted documents. | Semantic fidelity and clinical correctness against gold-standard manual annotations. |
| **Ground Truth Dependency** | Independent of external gold standard; operates on self-contained schema contracts. | Strictly dependent on dual-annotated, adjudicated clinical trial protocols. |
| **Primary Mechanism** | Deterministic Pydantic validation, regex syntax checks, ID uniqueness, and offset boundary checks. | Precision, Recall, F1, exact/token-overlap span matching, and ontology normalization accuracy. |
| **Failure Modes Caught** | Missing fields, orphan sections, duplicate IDs, invalid operators, start > end offsets, empty text. | Omission of critical criteria, clinical hallucinations, incorrect numeric ranges, misclassification. |

---

## 2. Evaluation Levels & Metric Formulations

### Level 1: Section Detection & Boundary Segmentation

Evaluates the ability of the extraction pipeline to identify structural sections (Inclusion, Exclusion, Eligibility, Study Population) and their exact boundaries in unstructured trial documents.

#### Metrics
- **Section Classification Precision, Recall, and Micro/Macro F1:**
  $$\text{Precision}_{\text{sec}} = \frac{|\text{True Positive Sections}|}{|\text{Predicted Sections}|}$$
  $$\text{Recall}_{\text{sec}} = \frac{|\text{True Positive Sections}|}{|\text{Gold Standard Sections}|}$$
- **Boundary IoU (Intersection over Union) / Token Overlap:**
  For a predicted section span $[s_p, e_p]$ and gold span $[s_g, e_g]$:
  $$\text{IoU}_{\text{span}} = \frac{\max(0, \min(e_p, e_g) - \max(s_p, s_g))}{\max(e_p, e_g) - \min(s_p, s_g)}$$
  A section boundary is counted as a true positive if $\text{IoU}_{\text{span}} \ge 0.80$ and section taxonomy matches.

---

### Level 2: Criterion Extraction & Granularity

Evaluates whether individual clinical criteria are correctly separated from narrative bullet points, paragraphs, and lists.

#### Metrics
- **Criterion Extraction F1:** Evaluated at two threshold levels:
  1. **Exact Text Match:** Verbatim string match between predicted `raw_text` and annotated criterion text.
  2. **Relaxed / Token Overlap Match:** Token-level F1 $\ge 0.85$ or ROUGE-L $\ge 0.85$.
- **Over-Splitting Rate:** Proportion of gold-standard atomic criteria incorrectly split into multiple fragmented fragments.
- **Under-Splitting Rate:** Proportion of multi-intent compound sentences incorrectly left as a single un-decomposed block.

---

### Level 3: Inclusion / Exclusion Classification

Evaluates whether each extracted criterion is correctly categorized as an Inclusion requirement, Exclusion requirement, or clinically Ambiguous.

#### Metrics
- **Classification Confusion Matrix:** Tracking true vs. predicted counts across classes:
  - Inclusion
  - Exclusion
  - Ambiguous / Discretionary
- **Macro-Averaged F1 Score:**
  $$\text{Macro-F1} = \frac{1}{|C|} \sum_{c \in C} F1_c$$
- **Safety Critical Asymmetric Penalty:**
  In oncology and clinical trial matching, an **Exclusion misclassified as Inclusion** represents a critical safety risk (a contraindicated patient enrolled in an ineligible trial). The evaluation framework must track this specific directional error rate:
  $$\text{Contraindication Leakage Rate} = \frac{|\text{Exclusion classified as Inclusion}|}{|\text{Total Gold Exclusions}|}$$

---

### Level 4: Atomicity & Structured Constraint Parsing

Evaluates whether compound sentences are broken down into semantically sound, indivisible atomic constraints.

#### Metrics
- **Atomicity Classification Accuracy:** Binary accuracy in classifying whether a criterion is atomic (`is_atomic=True`) or compound (`is_atomic=False`).
- **Structured Field Extraction Accuracy:**
  Evaluated across the 6 core components of `AtomicConstraint`:
  1. **Concept Resolution:** Normalized entity match (e.g., `platelet_count`, `ecog_performance_status`).
  2. **Operator Accuracy:** Exact match of `CriterionOperator` ($>=, <=, ==, \text{between}$, etc.).
  3. **Threshold Value Accuracy:** Numeric exact match (handling floating point tolerances $\pm 10^{-5}$) or categorical value match.
  4. **Unit Normalization Accuracy:** Correct mapping of clinical units to UCUM / standard representations (e.g., $10^9/L$ vs. cells $/ \mu L$).
  5. **Temporal Window & Anchor Accuracy:** Days and reference anchor match (e.g., within 28 days prior to Day 1).
  6. **Polarity / Negation Accuracy:** Correct detection of `is_negated`.

---

### Level 5: Provenance & Evidence Attribution

Evaluates whether the system preserves reliable, traceable evidence pointing back to the original source PDF/text.

#### Metrics
- **Page Attribution Accuracy:** Percentage of criteria whose attributed `page_number` matches the true source page:
  $$\text{Page Accuracy} = \frac{\sum_{i=1}^N \mathbb{I}(\text{page}_{\text{pred}}^{(i)} = \text{page}_{\text{gold}}^{(i)})}{N}$$
- **Span Offset Exact Match:** Percentage of criteria where character offsets $[s, e]$ in the source text slice the exact gold evidence span.
- **Provenance Hallucination Rate:** Percentage of criteria for which attributed source text does not appear in the source document. **Target: 0.0%.**

---

## 3. Benchmark Dataset Annotation Protocol (Prerequisite for Future Evaluation)

To produce empirical measurements using the above metrics, the capstone must construct or ingest a benchmark following this protocol:

1. **Dual Independent Clinical Annotation:**
   - Two clinical curators annotate protocols independently.
   - Annotators identify section headers, criterion spans, inclusion/exclusion polarities, and atomic constraints.
2. **Inter-Annotator Agreement (IAA):**
   - Measure agreement using Cohen's Kappa ($\kappa$) for categorical labels and token-level F1 for span boundaries.
   - Minimum acceptable threshold: $\kappa \ge 0.80$ before adjudication.
3. **Adjudication Consensus:**
   - Discrepancies resolved by a senior clinician/principal investigator.
4. **Data Freeze & Checksum:**
   - Adjudicated benchmark serialized as immutable JSONL with cryptographic SHA-256 manifests.
