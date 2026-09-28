# MedMatch Capstone — Phase 8: Hallucination Error Taxonomy

**Document Version:** `1.0.0`  
**Phase:** 8 — Grounding Evaluation & Faithfulness Auditing  
**Date:** September 2026  
**Status:** Canonical Hallucination Taxonomy  

---

## 1. Overview & Research Principles

In generative clinical reasoning, hallucination can manifest in multiple subtle ways beyond simple fabrication of medical jargon. The **Phase 8 Hallucination Error Taxonomy** provides an operational, 10-class categorization ($H1$–$H10$) designed to classify reasoning failures systematically.

In accordance with capstone research integrity rules:
- All classes possess objective, programmatic detection rules.
- Severity levels reflect research error magnitude (Critical, Major, Moderate, Minor) based on decision impact rather than speculative clinical harm.

---

## 2. The 10-Class Hallucination Taxonomy ($H1$–$H10$)

```text
+----------------------------------------------------------------------------------------------------+
|                                    10-CLASS HALLUCINATION TAXONOMY                                 |
+-----+--------------------------------------+---------------------+---------------------------------+
| Code| Error Category                       | Severity            | Research Error Manifestation    |
+-----+--------------------------------------+---------------------+---------------------------------+
| H1  | Fabricated Patient Fact              | Critical            | Unmentioned medical condition   |
| H2  | Fabricated Trial Criterion           | Critical            | Invented protocol requirement   |
| H3  | Fabricated Numerical Value           | Major               | Distorted lab value or cutoff   |
| H4  | Fabricated Temporal Fact             | Major               | Invented date or duration       |
| H5  | Unsupported Clinical Inference       | Moderate            | Speculative unverified leap     |
| H6  | Contradiction of Source Evidence     | Critical            | Direct assertion conflict       |
| H7  | Provenance / Citation Mismatch       | Major               | Spurious/corrupted citation     |
| H8  | Unsupported Eligibility Conclusion   | Critical            | PASS/FAIL without evidence      |
| H9  | Evidence Omission                    | Major               | Ignoring available contra-fact  |
| H10 | Unsupported Certainty                | Minor               | Removing required hedging       |
+-----+--------------------------------------+---------------------+---------------------------------+
```

---

### H1 — Fabricated Patient Fact
- **Operational Definition:** A claim asserting that the patient has a specific diagnosis, biomarker, history, or symptom that does not appear anywhere in the patient record.
- **Detection Mechanism:** Patient fact lookup returns no concept match, synonym match, or character overlap in `patient_facts` or `patient_note`.
- **Severity / Research Interpretation:** *Critical*. Fundamentally corrupts the clinical decision basis.
- **Example:** Claiming `"Patient has confirmed HER2-positive breast cancer"` when the patient note only mentions lung adenocarcinoma.
- **Non-Example:** Stating `"Patient has non-small cell lung cancer"` when the note states `"biopsy-proven NSCLC"`. (Standard synonymy is supported).

---

### H2 — Fabricated Trial Criterion
- **Operational Definition:** A claim describing a trial inclusion/exclusion requirement that is absent from the trial's registered protocol or retrieved criteria.
- **Detection Mechanism:** Trial protocol text search returns no match for the claimed constraint in `criteria` or `retrieved_evidence`.
- **Severity / Research Interpretation:** *Critical*. Introduces arbitrary barriers or false gateways to eligibility.
- **Example:** Claiming `"The trial requires patient to have completed prior radiation therapy"` when no radiation criterion exists in the trial.
- **Non-Example:** Quoting `"Age >= 18"` when the criterion description is `"Must be 18 years of age or older"`.

---

### H3 — Fabricated Numerical Value
- **Operational Definition:** A numerical score, laboratory measurement, or demographic age stated in reasoning that differs from the recorded evidence value or cutoff.
- **Detection Mechanism:** Regex extraction of numbers/units followed by mathematical comparison against documented facts.
- **Severity / Research Interpretation:** *Major*. Alters quantitative threshold evaluations.
- **Example:** Claiming `"Patient's baseline creatinine is 0.8 mg/dL"` when the record shows `"creatinine 2.4 mg/dL"`, or claiming `"HbA1c cutoff is 6.5%"` when the criterion requires `< 8.0%`.
- **Non-Example:** Expressing `"62 years old"` when the patient profile lists `"age: 62"`.

---

### H4 — Fabricated Temporal Fact
- **Operational Definition:** A claim asserting an exact chronological date, elapsed duration, or temporal relation that is not documented in the record.
- **Detection Mechanism:** Temporal parser extracts calendar dates or intervals from reasoning that have no anchor in patient facts.
- **Severity / Research Interpretation:** *Major*. Distorts evaluation of washout periods or recent recurrence windows.
- **Example:** Claiming `"The patient was diagnosed on October 12, 2023"` when the record only says `"diagnosed recently"`.
- **Non-Example:** Stating `"Patient received prior chemotherapy"` when facts list `"platinum-based chemotherapy completed 2022"`.

---

### H5 — Unsupported Clinical Inference
- **Operational Definition:** A deductive clinical leap where intermediate conclusions are treated as factual without supporting evidence in the record.
- **Detection Mechanism:** Extracted proposition contains speculative phrases (`likely`, `suggests`, `assumed`) paired with an unsubstantiated clinical attribute.
- **Severity / Research Interpretation:** *Moderate*. Inappropriate substitution of probabilistic heuristics for explicit documentation.
- **Example:** Claiming `"Because patient has hypertension, they likely have underlying renal impairment."`
- **Non-Example:** Stating `"Patient meets hypertension requirement based on documented ICD-10 I10"`.

---

### H6 — Contradiction of Source Evidence
- **Operational Definition:** A claim that directly and explicitly contradicts a verified statement in the source evidence.
- **Detection Mechanism:** Automated contradiction detector identifies opposite assertion states (`PRESENT` vs. `ABSENT`) or mutually exclusive clinical concepts.
- **Severity / Research Interpretation:** *Critical*. Represents an overt failure of comprehension or faithfulness.
- **Example:** Reasoning asserts `"Patient has no prior immunotherapy"` when patient facts state `"pembrolizumab administered 2023 (assertion: PRESENT)"`.
- **Non-Example:** Concluding `UNKNOWN` when the clinical fact states `assertion: UNKNOWN`.

---

### H7 — Provenance / Citation Mismatch
- **Operational Definition:** An attached citation that points to a nonexistent fact ID, mismatched trial ID, incorrect criterion ID, or character span that does not match the cited snippet.
- **Detection Mechanism:** Validator inspects `EvidenceCitation`: checks if `fact_id` exists in `patient_facts`, checks if `patient_note[start_char:end_char] == snippet`, and checks trial ID consistency.
- **Severity / Research Interpretation:** *Major*. Illusion of verifiability; creates a false audit trail.
- **Example:** Citation references `fact_id="fact-999"` (nonexistent), or cites `start_char=10, end_char=30` which contains completely different text.
- **Non-Example:** Setting `start_char=-1, end_char=-1` when character positions are unlocatable under project conventions.

---

### H8 — Unsupported Eligibility Conclusion
- **Operational Definition:** Concluding `PASS` or `FAIL` on a criterion when the intermediate reasoning and evidence are absent, contradictory, or inconclusive.
- **Detection Mechanism:** Evaluator compares `CriterionEvaluationStatus` against the set of extracted and verified claims. If no supporting claims exist, but status is `PASS` or `FAIL`, $H8$ is triggered.
- **Severity / Research Interpretation:** *Critical*. Directly yields an invalid eligibility determination.
- **Example:** Emitting `status: "PASS"` on `"Must have documented EGFR T790M"` when reasoning explicitly says `"EGFR status is not documented in clinical record"`.
- **Non-Example:** Emitting `status: "UNKNOWN"` when evidence is missing.

---

### H9 — Evidence Omission
- **Operational Definition:** Reasoning fails to acknowledge or evaluate documented clinical evidence that directly invalidates or satisfies a criterion.
- **Detection Mechanism:** A patient fact exists that matches the criterion concept, but reasoning states `"No evidence found"` and emits `UNKNOWN`.
- **Severity / Research Interpretation:** *Major*. Unnecessary epistemic abstention leading to false `NEEDS_REVIEW`.
- **Example:** Emitting `"Status is unknown because histological type is not mentioned"`, when the patient note explicitly states `"histology: invasive ductal carcinoma"`.
- **Non-Example:** Abstaining with `UNKNOWN` when the specific required lab test was indeed unmentioned.

---

### H10 — Unsupported Certainty
- **Operational Definition:** Expressing definitive confidence on an ambiguous, hedged, or uncertain clinical observation without preserving documented uncertainty.
- **Detection Mechanism:** Source fact has `assertion: "UNKNOWN"` or `uncertainty_flag: true`, but reasoning asserts the condition definitively without qualification.
- **Severity / Research Interpretation:** *Minor*. Epistemic overconfidence.
- **Example:** Note says `"suspected mild neuropathy"`, but reasoning states `"Patient has confirmed peripheral neuropathy"`.
- **Non-Example:** Stating `"Patient has suspected neuropathy"` preserving the original epistemic qualification.
