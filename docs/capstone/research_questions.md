# MedMatch Capstone — Research Questions

> **Status:** Specification Document  
> **Phase:** 1 — Research Problem & Evaluation Design  
> **Author:** MedMatch Research Team  
> **Date:** September 2026  
> **Target System:** MedMatch Clinical Decision-Support Prototype

---

## 1. Overview and Formulation Philosophy

All research questions formulated below are strictly **investigative questions**, not empirical claims. In accordance with clinical informatics standards and rigorous machine learning evaluation methodology, no performance superiority is assumed prior to formal benchmark experimentation on held-out test data.

---

## 2. Primary Research Question

> **Primary RQ:**  
> **Can an evidence-grounded retrieval-augmented framework improve the accuracy, retrieval quality, and explainability of clinical trial eligibility matching compared with a baseline dense-retrieval and LLM reasoning pipeline?**

This primary question investigates whether decomposing monolithic trial matching into:
1. Decomposed structured criteria;
2. Multimodal lexical/semantic candidate retrieval;
3. Explicit criterion-level tri-state reasoning with textual evidence attribution; and
4. Deterministic clinical aggregation rules,

yields statistically and clinically meaningful gains over the current single-shot dense-retrieval baseline (`MiniLM-L6-v2` + monolithic `Gemini 2.5 Flash` prompt).

---

## 3. Secondary Research Questions

### RQ1 — Trial Information Extraction
> **Can structured extraction reliably transform unstructured clinical-trial documents into machine-readable eligibility criteria?**
- **Sub-question 1.1:** How accurately can semi-structured freeform inclusion and exclusion text blocks from ClinicalTrials.gov be segmented into atomic, independent eligibility criteria?
- **Sub-question 1.2:** Can extracted criteria be reliably classified into clinical semantic domains (e.g., Demographics, Biomarkers/Genomics, Prior Therapies, Organ Function/Labs, Performance Status)?

### RQ2 — Information Retrieval Quality
> **How effectively can the system retrieve the clinical-trial criteria relevant to a patient's clinical information?**
- **Sub-question 2.1:** How does hybrid retrieval (combining sparse BM25 lexical search with dense semantic embeddings) compare against pure dense vector retrieval (`MiniLM-L6-v2` cosine distance) in retrieving candidate trials and specific criteria?
- **Sub-question 2.2:** What is the impact of retrieval depth ($k \in \{1, 3, 5, 10, 20\}$) on the recall of clinically relevant trials and criteria?
- **Sub-question 2.3:** Does a secondary cross-encoder reranking step significantly improve precision at top ranks (nDCG@5, MRR) for criteria with strict numerical or genomic constraints?

### RQ3 — Eligibility Classification Performance
> **How accurately can the system classify patient-trial eligibility across explicit decision classes?**
- **Sub-question 3.1:** What is the macro-averaged F1 score across the three distinct clinical states: `ELIGIBLE`, `INELIGIBLE`, and `NEEDS_REVIEW`?
- **Sub-question 3.2:** How do false-positive rates (classifying an ineligible patient as eligible) compare between monolithic baseline reasoning and criterion-level grounded reasoning?
- **Sub-question 3.3:** When evaluated on a binary projection (`ELIGIBLE` vs. `NOT_ELIGIBLE`), does criterion-level evaluation preserve or enhance sensitivity and specificity?

### RQ4 — Retrieval-Augmented Generation (RAG) Contribution
> **Does retrieval-grounded reasoning provide measurable improvement over an LLM-only or non-retrieval baseline?**
- **Sub-question 4.1:** How does an LLM queried with the entire trial registry in context (or parametric LLM knowledge without trial context) compare in decision accuracy and hallucination frequency against a pipeline with explicit retrieved context?
- **Sub-question 4.2:** What is the sensitivity of classification performance to retrieval recall degradation (i.e., if a relevant criterion is omitted from the retrieved context)?

### RQ5 — Evidence Grounding and Provenance
> **To what extent are eligibility decisions supported by explicit patient evidence and trial criteria?**
- **Sub-question 5.1:** What proportion of evaluated criteria are supported by direct, verifiable character-level text spans extracted from the patient's record (Evidence Coverage)?
- **Sub-question 5.2:** What is the rate of unsupported or hallucinated clinical claims (Unsupported Claim Rate) in the reasoning outputs of the baseline system versus the grounded framework?
- **Sub-question 5.3:** Do cited patient text spans logically support the criterion-level conclusion when evaluated by medical annotators (Evidence-Criterion Consistency)?

### RQ6 — Clinical Uncertainty and Incompleteness
> **Can the system appropriately identify cases where available information is insufficient or contradictory?**
- **Sub-question 6.1:** Can the system reliably output `NEEDS_REVIEW` when critical lab values or staging information are omitted from the clinical note, rather than defaulting to speculative compliance or disqualification?
- **Sub-question 6.2:** How effectively does the system flag contradictory clinical evidence (e.g., negative pathology report juxtaposed with a positive clinical impression)?

### RQ7 — Systematic Error Analysis
> **What categories of clinical-trial matching errors remain after applying the proposed architecture?**
- **Sub-question 7.1:** Across a structured 12-category error taxonomy (E1–E12), what proportion of matching errors stem from upstream retrieval failures versus downstream reasoning or clinical negation errors?
- **Sub-question 7.2:** Are numerical threshold comparisons (e.g., lab cutoffs) and temporal reasoning (e.g., washout periods) disproportionately represented among residual errors?

---

## 4. Mapping of Research Questions to Capstone Phases

| Research Question | Primary Focus | Evaluated In | Metric Type |
|---|---|---|---|
| **RQ1** (Extraction) | Parsing & Decomposing Protocol Criteria | Phase 3 / Phase 4 | Parse Accuracy, Schema Validity |
| **RQ2** (Retrieval) | Vector/Sparse Candidate Search | Phase 4 / Phase 5 | Recall@K, MRR, nDCG@K |
| **RQ3** (Classification) | Trial-Level & Criterion-Level Decisions | Phase 4 / Phase 5 | Macro-F1, Precision, Recall, Accuracy |
| **RQ4** (RAG Value) | Baseline vs. RAG Comparative Study | Phase 5 | Comparative F1, Ablation Δ |
| **RQ5** (Grounding) | Textual Provenance & Hallucination Rate | Phase 4 / Phase 5 | Grounded Decision Rate, Unsupported Claim Rate |
| **RQ6** (Uncertainty) | Missing/Contradictory Evidence Calibration | Phase 4 / Phase 5 | `NEEDS_REVIEW` Calibration & Recall |
| **RQ7** (Error Analysis) | Residual Error Categorization | Phase 5 | 12-Factor Error Distribution |
