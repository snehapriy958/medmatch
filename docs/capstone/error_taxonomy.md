# MedMatch Capstone — Error Taxonomy Specification

> **Status:** Specification Document  
> **Phase:** 1 — Research Problem & Evaluation Design  
> **Author:** MedMatch Research Team  
> **Date:** September 2026  
> **Target System:** MedMatch Clinical Decision-Support Prototype

---

## 1. Overview and Purpose

A critical research requirement for clinical AI systems is systematic, structured error categorization. Rather than treating failures as undifferentiated classification mistakes, MedMatch defines a 12-factor error taxonomy (**E1 through E12**) spanning the complete lifecycle: retrieval, information extraction, reasoning, evidence grounding, aggregation, and structured output.

```text
+---------------------------------------------------------------------------------------------------------+
|                                        12-FACTOR ERROR TAXONOMY                                         |
+-----+---------------------------------------+---------------------+-------------------------------------+
| ID  | Error Category                        | Pipeline Stage      | Primary Failure Mechanism           |
+-----+---------------------------------------+---------------------+-------------------------------------+
| E1  | Retrieval Failure                     | Stage 1: Retrieval  | Candidate omitted from top-K        |
| E2  | Incorrect Criterion Extraction        | Pre-processing      | Protocol parsing/segmentation error |
| E3  | Patient Information Extraction Failure| Pre-processing      | Clinical entity in note missed      |
| E4  | Medical Terminology Normalization     | Pre-processing/RAG  | Synonym or ontology mismatch        |
| E5  | Criterion Interpretation Failure      | Stage 2: Reasoning  | Misinterpreting clinical intent     |
| E6  | Numerical Threshold Error             | Stage 2: Reasoning  | Inequality comparison or unit error |
| E7  | Temporal Reasoning Error              | Stage 2: Reasoning  | Washout period or timing mismatch   |
| E8  | Negation Error                        | Stage 2: Reasoning  | Reversing clinical assertion status |
| E9  | Missing Evidence Handling Error       | Stage 2: Reasoning  | Speculating instead of UNKNOWN      |
| E10 | Hallucinated / Unsupported Evidence   | Stage 2: Grounding  | Citing phantom text or facts        |
| E11 | Incorrect Aggregation                 | Stage 3: Aggregation| Violating deterministic logic       |
| E12 | LLM Formatting / Schema Failure       | Output / Interface  | JSON decode error or schema break   |
+-----+---------------------------------------+---------------------+-------------------------------------+
```

---

## 2. Detailed Error Categories

### E1 — Retrieval Failure
- **Definition:** The target trial or critical eligibility criterion is omitted from the top-$K$ candidate list returned by Stage 1 retrieval.
- **Clinical Example:** A patient with rare *ROS1* rearrangement fails to retrieve a matching phase II trial because the dense embedding similarity fell below the cutoff rank ($k > 5$).
- **Root Cause:** Vocabulary mismatch, dense embedding lexical blindness, or insufficiently deep retrieval window.
- **Detection:** Automated benchmark comparison against ground-truth trial IDs ($\text{Recall@}K = 0$).
- **Mitigation:** Implement hybrid BM25 + dense retrieval with Reciprocal Rank Fusion and cross-encoder reranking.

---

### E2 — Incorrect Criterion Extraction
- **Definition:** Failure to cleanly parse semi-structured protocol eligibility criteria blocks into atomic, single-intent criteria.
- **Clinical Example:** A compound sentence ("ANC $\ge 1500/\mu\text{L}$, Platelets $\ge 100,000/\mu\text{L}$, and Bilirubin $\le 1.5 \times \text{ULN}$") is extracted as a single unparsed string, causing the downstream evaluator to miss platelet failure.
- **Root Cause:** Inadequate text splitting, complex semi-structured bullet points, or irregular punctuation in ClinicalTrials.gov descriptions.
- **Detection:** Pre-ingestion validation against gold-standard criterion counts.
- **Mitigation:** Protocol criteria parser with boundary segmentation rules and clinical domain tagging.

---

### E3 — Patient Information Extraction Failure
- **Definition:** Clinical facts, laboratory values, or diagnoses present in the patient record are overlooked by the model.
- **Clinical Example:** The patient narrative notes "Patient diagnosed with small cell transformation on repeat biopsy," but the model evaluates histology as classical NSCLC.
- **Root Cause:** High narrative density, buried information in historical sections, or LLM attention dilution across lengthy clinical notes.
- **Detection:** Discrepancy between gold-standard patient evidence spans and empty model evidence extractions.
- **Mitigation:** Extract structured clinical profiles ($D_P, E_P$) with targeted entity recognition before matching.

---

### E4 — Medical Terminology Normalization Failure
- **Definition:** Failure to align clinical synonyms, brand names, or hierarchical disease concepts with protocol terminology.
- **Clinical Example:** Patient record lists "Keytruda," but the exclusion criterion specifies "prior anti-PD-1 antibody therapy (pembrolizumab)," and the system fails to recognize equivalence.
- **Root Cause:** Lack of biomedical ontology mapping (RxNorm, UMLS, SNOMED CT, NCI Thesaurus).
- **Detection:** Manual clinical audit of false-positive decisions.
- **Mitigation:** Domain-specific ontology normalization dictionary mapping drug brand names and ICD-O-3 histological variants.

---

### E5 — Criterion Interpretation Failure
- **Definition:** The model fundamentally misunderstands the clinical or semantic intent of a criterion.
- **Clinical Example:** A trial excludes patients with "active CNS metastases, unless treated and asymptomatic for $\ge 3$ months." The model treats any history of CNS metastases as disqualifying, ignoring the stability exception.
- **Root Cause:** Complex subordinate clauses, exception conditions, or confusing inclusion versus exclusion framing.
- **Detection:** Criterion-level audit comparing model rationale to expert clinical annotation.
- **Mitigation:** Few-shot prompt exemplars featuring compound conditional rules and exception handling.

---

### E6 — Numerical Threshold Error
- **Definition:** Miscalculating mathematical inequalities ($<, \le, >, \ge$) or failing to convert clinical laboratory measurement units.
- **Clinical Example:** Criterion requires "Absolute Neutrophil Count (ANC) $\ge 1.5 \times 10^9/\text{L}$." Patient narrative states "ANC: $1400/\mu\text{L}$." Model evaluates as `PASS` ($1400 \ge 1.5$), failing to standardize units.
- **Root Cause:** Pure LLM autoregressive token generation without symbolic numerical execution.
- **Detection:** Automated regex check comparing extracted numerical values against criterion boundary values.
- **Mitigation:** Programmatic regex/symbolic unit converter and mathematical comparison layer.

---

### E7 — Temporal Reasoning Error
- **Definition:** Inability to accurately calculate time intervals, therapy washout periods, or chronology of clinical events.
- **Clinical Example:** Criterion requires "$\ge 28$ days since last cytotoxic chemotherapy." Patient received Carboplatin 18 days prior to screening date. Model evaluates as `PASS`.
- **Root Cause:** LLM difficulty with relative date arithmetic between narrative timestamps and the screening reference date.
- **Detection:** Timestamp diff audits on temporal criterion subsets.
- **Mitigation:** Explicit date normalization and temporal diff calculation in the patient pre-processing pipeline.

---

### E8 — Negation Error
- **Definition:** Inverting the clinical polarity of a finding (treating a ruled-out condition as present or vice-versa).
- **Clinical Example:** Clinical note states "Patient has no history of venous thromboembolism." Model evaluates exclusion criterion "History of DVT/PE" as `FAIL` because it matched "venous thromboembolism."
- **Root Cause:** Naive keyword matching or failure of LLM attention over negation cues ("no evidence of", "denies", "negative for").
- **Detection:** Negation check audits on exclusion criteria.
- **Mitigation:** Dedicated clinical negation detection (e.g., ConText/NegEx principles) in structured entity extraction.

---

### E9 — Missing Evidence Handling Error (Hallucinatory Speculation)
- **Definition:** The model asserts `PASS` or `FAIL` on a criterion when the required medical information is completely absent from the clinical narrative, rather than outputting `UNKNOWN`.
- **Clinical Example:** Protocol requires "LVEF $\ge 50\%$ by ECHO/MUGA." Patient note mentions no cardiac history and no echocardiogram. Model outputs `PASS` with the rationale: "Patient has no heart failure symptoms."
- **Root Cause:** Sycophancy or default compliance bias in generative LLMs without strict conservative uncertainty constraints.
- **Detection:** Checking model predictions on synthetic Category 3 (Missing Information) control cases.
- **Mitigation:** Strict negative constraint prompts: "If not explicitly documented, you MUST evaluate UNKNOWN. Never assume negative or normal."

---

### E10 — Hallucinated / Unsupported Evidence
- **Definition:** The model produces an evidence citation or text span that does not exist in the source patient narrative.
- **Clinical Example:** Model outputs: `patient_evidence: "EGFR exon 19 deletion confirmed on biopsy 04/12/2025"` when that sentence does not appear anywhere in the patient record.
- **Root Cause:** Generative hallucination under high token generation temperature or complex multi-trial prompts.
- **Detection:** Automated substring verification: $\text{assert } \text{span} \subseteq N_P$.
- **Mitigation:** Temperature set to 0.0, extractive text-span indexing, and programmatic post-hoc verification rejection.

---

### E11 — Incorrect Aggregation
- **Definition:** The trial-level eligibility determination violates the deterministic aggregation logic applied over the criterion-level evaluations.
- **Clinical Example:** Criterion 1 is `FAIL` (disqualified), Criterion 2 is `PASS`, Criterion 3 is `PASS`, but the trial-level output is `ELIGIBLE`.
- **Root Cause:** In monolithic LLM reasoning, the LLM hallucinates an overall positive summary despite recognizing a failing criterion earlier in its generation.
- **Detection:** Programmatic consistency validator: $\text{assert } (\exists y_i = \text{FAIL} \implies Y = \text{INELIGIBLE})$.
- **Mitigation:** Remove aggregation from the LLM prompt entirely; compute $Y = \Lambda(\{y_i\})$ deterministically in Python.

---

### E12 — LLM Formatting / Schema Failure
- **Definition:** The LLM returns malformed JSON, truncated tokens, missing required keys, or invalid enum values that fail Pydantic parsing.
- **Clinical Example:** Model truncates output mid-stream due to max token limits, or outputs markdown backticks around invalid JSON.
- **Root Cause:** Context window overflow, prompt length, or non-deterministic provider API errors.
- **Detection:** Pydantic `ValidationError` or `json.JSONDecodeError` during response ingestion.
- **Mitigation:** Native Gemini structured output schema enforcement (`response_schema`), token budgeting, and automated retries.
