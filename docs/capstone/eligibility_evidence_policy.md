# MedMatch Capstone — Eligibility Evidence Policy
**Document Version:** `1.0.0`  
**Phase:** 6 — Eligibility Reasoning  

---

## 1. Principle of Mandatory Evidence Grounding

In high-stakes clinical decision support, an eligibility assertion without verifiable grounding is clinically hazardous. Therefore, MedMatch enforces a strict **Evidence Grounding Policy**:

> **Core Rule:**  
> Every criterion evaluation yielding `PASS` or `FAIL` **MUST** explicitly cite at least one verified patient evidence snippet and link to a canonical `ClinicalFact` or demographic record. Any evaluation lacking supporting evidence is formally classified as an **Unsupported Assertion** and must be converted to `UNKNOWN` or rejected by the validator.

---

## 2. Minimum Evidence Requirements

To qualify as valid evidence grounding, an `EvidenceCitation` must provide:
1. **Source Document / Field:** Identification of the originating document (e.g. `patient_facts`, `demographics`, `clinical_note`).
2. **Text Snippet:** The exact verbatim text fragment from the patient record demonstrating the clinical observation.
3. **Character Spans:** Character offsets (`start_char`, `end_char`) where the snippet appears in the source document, or `-1` if extracted from structured demographic metadata.
4. **Fact Reference:** The unique `fact_id` assigned by the Phase 4 patient extractor (e.g. `fact-10293`).
5. **Assertion Alignment:** The assertion state of the cited fact (`PRESENT`, `ABSENT`, `POSSIBLE`) must logically support the evaluated status:
   - For an **Inclusion** criterion: `PASS` requires `PRESENT`; `FAIL` requires `ABSENT`.
   - For an **Exclusion** criterion: `PASS` requires `ABSENT`; `FAIL` requires `PRESENT`.

---

## 3. Evidence Sources & Hierarchy

When evaluating eligibility criteria, evidence must be sourced from authorized, verified data layers in the following hierarchy:

| Priority | Evidence Layer | Examples | Trust Level |
| :---: | :--- | :--- | :---: |
| **1** | **Structured Demographics & Vitals** | Patient Age, Sex, Verified Date of Birth | Highest (Deterministic) |
| **2** | **Quantitative Laboratory Facts** | Serum Creatinine, Platelet Count, Absolute Neutrophil Count | High (Numeric + Unit verified) |
| **3** | **Structured Clinical Facts** | Histopathology, Mutation Status (EGFR L858R), Staging | High (Bi-directionally grounded in EHR) |
| **4** | **Unstructured Clinical Narrative** | Free-text physician notes with character offsets | Moderate (Requires lexical/semantic verification) |

Unverified external assumptions, clinical intuitions, or general medical knowledge are **NEVER** acceptable evidence sources for patient-specific eligibility.

---

## 4. Unsupported Assertion Handling

If an AI reasoner or LLM emits a `PASS` or `FAIL` status without providing supporting evidence:
1. **Validator Rejection:** `scripts/validate_eligibility.py` automatically flags an `Evidence violation` error.
2. **Safe Fallback Conversion:** If fallback is enabled, the reasoning engine automatically demotes the status to `UNKNOWN`:
   - `status` $\to$ `UNKNOWN`
   - `uncertainty_notes` $\to$ `"Demoted from PASS/FAIL due to missing evidence citations (Unsupported Assertion)."`
   - `reasoning` $\to$ `"Evaluation lacked grounded evidence citations in patient facts."`
3. **Audit Logging:** An audit alert is logged noting the generation of an ungrounded model output.

---

## 5. Provenance Tracing Chain

Every decision must maintain an unbroken chain of provenance:
```
Trial Criterion (ID, Text, Type)
       ▲
       │ evaluates
       ▼
CriterionEvaluationRecord
       │
       ├─► EvidenceCitation (Snippet, start_char, end_char)
       │         ▲
       │         │ grounds
       │         ▼
       └─► PatientClinicalProfile Fact (fact_id, concept, assertion)
                 ▲
                 │ extracted from
                 ▼
           Source EHR Note / Demographic Record
```

This bidirectional chain ensures that any clinician, auditor, or regulatory body can inspect an eligibility decision and trace it down to the exact sentence in the medical chart that justified the decision.
