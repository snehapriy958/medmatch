# MedMatch Capstone — Phase 8: Evidence Grounding & Hallucination Audit

**Document Version:** `1.0.0`  
**Phase:** 8 — Grounding Evaluation & Hallucination Auditing  
**Date:** September 2026  
**Status:** Audit Complete  
**Software Baseline:** `c528894` (Phase 7 RAG vs. Non-RAG Evaluation)  

---

## 1. Executive Summary

This audit establishes the empirical and architectural baseline for Phase 8 of the MedMatch capstone. Building upon the Phase 5 retrieval engine, Phase 6 eligibility reasoning layer, and Phase 7 RAG/NON-RAG experimental framework, Phase 8 defines a formal, reproducible methodology to evaluate:
- **Hallucination:** Generation of ungrounded clinical facts, invented trial criteria, fabricated numerical measurements, or unmentioned dates.
- **Evidence Grounding:** The extent to which generated eligibility claims are strictly entailed by verified patient records and candidate trial documents.
- **Provenance & Citation Correctness:** The exact verification of document pointers, clinical fact identifiers, character offsets, and retrieval metadata.
- **Faithfulness of Reasoning:** Whether the intermediate justifications in `CriterionEvaluationRecord.reasoning` mathematically and clinically support the final `PASS`, `FAIL`, or `UNKNOWN` determination.

Crucially, **Phase 8 does NOT assume that generated text is truthful merely because an evidence citation is attached**. Phase 8 builds the automated, deterministic validation layer that scrutinizes the generated reasoning itself.

---

## 2. Tracing the Information Flow Across Reasoning Pipelines

To evaluate grounding rigorously, we must trace where clinical data enters, where provenance is bound, and what information is visible to an independent evaluator.

### 2.1 Information Entry Points
```text
                      +---------------------------------------+
                      |         CLINICAL PATIENT DATA         |
                      |   PatientClinicalProfile / Fact List  |
                      +-------------------+-------------------+
                                          |
                                          | (patient_facts, demographics, note)
                                          v
                      +---------------------------------------+
                      |         ELIGIBILITY REASONER          |
                      |    RuleBasedEligibilityReasoner       |
                      +-------------------+-------------------+
                                          ^
                                          | (criteria, retrieved_evidence)
                      +-------------------+-------------------+
                      |      TRIAL & RETRIEVAL ENGINE         |
                      |   Phase 5 Candidate Pools & Passages  |
                      +---------------------------------------+
```

1. **Patient Clinical Facts:**
   - **Entry point:** [`RuleBasedEligibilityReasoner.evaluate_criterion`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/eligibility_reasoner.py#L90-L130).
   - **Data structure:** List of dictionaries conformant to [`ClinicalFact`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/patient_schema.py#L40-L54) containing `fact_id`, `concept`, `assertion` (`PRESENT`, `ABSENT`, `UNKNOWN`), `snippet`, `start_char`, `end_char`, and optional `temporality`.
   - **Demographics:** Passed as an auxiliary dictionary (`{"age": int, "gender": str}`).

2. **Trial Criteria Definitions:**
   - **Entry point:** Passed to `evaluate_criterion` as a dictionary containing `id`, `description`, `criteria_type` (`INCLUSION` or `EXCLUSION`), and canonical text.

3. **Retrieved Candidate Protocol Evidence (RAG Pathways):**
   - **Entry point:** In [`RAGExperimentRunner.evaluate_trial`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/rag_experiment.py#L236-L327), candidate evidence originates from the Phase 5 retrieval engine (`DenseRetriever`, `HybridRRFRetriever`, `RerankingRetriever`).
   - **Data structure:** A structured dictionary containing `trial_id`, `trial_title`, `trial_summary`, `retrieval_method`, `retrieval_score`, `retrieval_rank`, and `source_reference` (`trial:{trial_id}`).

---

### 2.2 Provenance Binding & Citation Attachment

- **Patient Citations:**
  When a patient fact matches a criterion requirement, an [`EvidenceCitation`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/eligibility_schema.py#L50-L62) is created:
  ```python
  EvidenceCitation(
      fact_id=fact.get("fact_id"),
      text_snippet=fact.get("snippet", ""),
      source_field="patient_note",
      start_char=fact.get("start_char", -1),
      end_char=fact.get("end_char", -1),
      assertion_type=fact.get("assertion", "PRESENT"),
  )
  ```
- **Retrieval Context Citations:**
  In RAG evaluations where retrieved candidate text clarifies an otherwise `UNKNOWN` criterion, the citation is bound with retrieval provenance:
  ```python
  citation.source_field = f"{retrieval_method}:{source_reference}"  # e.g., "dense:trial:NCT001"
  ```
- **Trial Pointers:**
  Recorded in [`CriterionEvaluationRecord.trial_criterion_reference`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/eligibility_schema.py#L79) (e.g., `"trial:NCT001"`).

---

### 2.3 Generation of Reasoning & Decisions

1. **Criterion-Level Reasoning:**
   - `eval_record.reasoning` is populated with clinical justifications:
     - For direct fact matches: `"Direct evidence found: 'confirmed metastatic NSCLC' matches criterion (assertion: PRESENT)"`.
     - For age/demographics: `"Age evaluation: patient age 62 meets requirement 'Age >= 18'"`.
     - For RAG resolutions: `"Resolved via dense (rank=1, score=0.892): retrieved trial protocol confirms '...' satisfies requirements."`
     - For unknown/missing facts: `"No documented evidence found for criterion: 'must have failed prior platinum chemotherapy'"`.
2. **Three-Valued Truth Determination:**
   - Produced strictly as [`CriterionEvaluationStatus`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/eligibility_schema.py#L28-L36): `PASS`, `FAIL`, or `UNKNOWN`.
   - Never collapsed into a binary score.
3. **Trial-Level Deterministic Aggregation:**
   - Handled exclusively by [`EligibilityAggregator.aggregate_trial`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/eligibility_aggregator.py#L40-L100):
     - At least 1 `FAIL` $\implies$ `INELIGIBLE`.
     - 0 `FAIL` and $\ge 1$ `UNKNOWN` $\implies$ `NEEDS_REVIEW`.
     - All criteria `PASS` $\implies$ `ELIGIBLE`.

---

## 3. Evaluator Visibility Matrix

What an independent grounding evaluator can and cannot inspect from existing data structures:

| Data Attribute | Visible to Evaluator? | Storage Location | Grounding Utility |
| :--- | :---: | :--- | :--- |
| **Criterion Canonical Text** | YES | `CriterionEvaluationRecord.criterion_text` | Source truth for criterion claims |
| **Patient Structured Facts** | YES | `patient_facts` list / `PatientClinicalProfile` | Source truth for patient facts |
| **Patient Raw Note Text** | YES | `patient_note` parameter | Span and substring verification |
| **Cited Fact IDs** | YES | `EvidenceCitation.fact_id` | Verifies existence of cited fact |
| **Cited Offsets** | YES | `EvidenceCitation.start_char / end_char` | Exact substring character matching |
| **Retrieved Evidence Context** | YES | `retrieved_evidence` dict / Phase 5 response | Verifies protocol context |
| **Retrieval Metadata** | YES | `retrieval_method`, `rank`, `score` | Verifies provenance integrity |
| **Generated Justification** | YES | `CriterionEvaluationRecord.reasoning` | Text subject to claim extraction |
| **Evaluation Status** | YES | `CriterionEvaluationRecord.status` | Target of conclusion grounding |
| **Uncertainty Notes** | YES | `CriterionEvaluationRecord.uncertainty_notes` | Verifies epistemic hedging |
| **Latent Model Logits/Weights** | NO | Internal to external API / runtime | Unusable for deterministic evaluation |
| **Un-ingested Benchmark EHRs** | NO | External repository / un-ingested corpus | Unavailable until ingested |

**Key Finding:** The existing Phase 6 and Phase 7 data models provide **complete structured access** to all source evidence, citations, offsets, and generated text needed to execute rigorous, deterministic grounding evaluation.

---

## 4. Fundamental Distinctions in Grounding Evaluation

A rigorous grounding framework must never conflate distinct error modes. Phase 8 establishes strict conceptual and operational boundaries between the following seven categories:

```text
+----------------------------------------------------------------------------------------------------+
|                                    GROUNDING & FAITHFULNESS TAXONOMY                               |
+---+----------------------------+-------------------------------------------------------------------+
| A | Factual Support            | Claim is directly entailed by verified source evidence.           |
| B | Evidence Provenance        | Citations point to real, uncorrupted, and accurate document spans.|
| C | Unsupported Inference      | Plausible clinical conclusion drawn without explicit evidence.    |
| D | Contradiction              | Claim directly conflicts with verified patient facts or criteria. |
| E | Missing Evidence           | Evidence absent in record; must trigger UNKNOWN, not negation.    |
| F | Provenance Mismatch        | Citation points to wrong trial, wrong criterion, or offset drift. |
| G | Hallucinated Clinical Fact | Invented medical condition, lab value, or temporal milestone.     |
+---+----------------------------+-------------------------------------------------------------------+
```

### Detailed Distinctions:

1. **A. Factual Support vs. C. Unsupported Inference:**
   - *Factual Support:* Source says "Patient has stage IV adenocarcinoma." Reasoning states "Patient has metastatic adenocarcinoma." Supported.
   - *Unsupported Inference:* Source says "Patient presents with cough and weight loss." Reasoning states "Patient has suspected lung malignancy." Clinically reasonable, but **unsupported** by the record. Must be flagged as `UNSUPPORTED`.

2. **D. Contradiction vs. E. Missing Evidence:**
   - *Contradiction:* Source says "ECOG performance status is 2." Reasoning claims "Patient has ECOG 0." Directly conflicts with evidence. Flagged as `CONTRADICTED`.
   - *Missing Evidence:* Source has no mention of ECOG. Claim states "Patient has ECOG 0." This is **not** a contradiction of existing facts, but a **hallucinated patient fact** ($H1$) and unsupported claim. If reasoning concludes `UNKNOWN` because ECOG is unmentioned, that is valid epistemic abstention.

3. **B. Evidence Provenance vs. F. Provenance Mismatch:**
   - *Valid Provenance:* Citation references `fact_id="f1"`, snippet matches `patient_note[10:45]`, and source refers to the active trial.
   - *Provenance Mismatch:* Citation cites `fact_id="f99"` (nonexistent), cites criterion `c2` when discussing criterion `c1`, points to `start_char=500` in a 100-character note, or prefixes `dense:` when lexical retrieval was executed.

4. **G. Hallucinated Clinical Facts vs. Permissible Paraphrasing:**
   - *Permissible Paraphrasing:* "NSCLC" mapped to "non-small cell lung cancer" via standard clinical terminology.
   - *Hallucinated Fact:* Injecting "Patient was diagnosed on 2024-03-15" when the record only stated "diagnosed recently," or claiming "creatinine is 1.1 mg/dL" when no lab panel was present.

---

## 5. Architectural Gap in Current Implementation

Before Phase 8, the system enforced that:
1. `PASS` and `FAIL` must have at least one citation (`EligibilityValidator`).
2. Input payloads cannot leak retrieval metadata into Non-RAG (`InformationLeakageError`).

However, **there was no validator checking whether the text inside `reasoning` actually matched the cited facts**, nor whether all claims in the reasoning paragraph were grounded. An adversarial or buggy reasoner could emit:
```json
{
  "status": "PASS",
  "reasoning": "Patient was diagnosed with stage IV EGFR lung cancer in 2024 and completed 6 cycles of cisplatin.",
  "evidence_citations": [
    {
      "fact_id": "f_nsclc",
      "text_snippet": "history of lung cancer",
      "source_field": "patient_note",
      "start_char": 0,
      "end_char": 22
    }
  ]
}
```
In Phase 6, this would pass validation because `evidence_citations` is non-empty. However, the reasoning contains **fabricated stage IV**, **fabricated EGFR mutation**, **fabricated date 2024**, and **fabricated cisplatin therapy**!

**Phase 8 closes this critical gap** by introducing:
- **Claim Extraction:** Decomposing `reasoning` into atomic statements.
- **Grounding Verification:** Checking every atomic statement against facts and retrieved text.
- **Citation Validation:** Verifying that cited offsets and IDs actually exist and match verbatim.
- **Hallucination Metrics:** Quantifying the hallucination rate and citation validity rate.
