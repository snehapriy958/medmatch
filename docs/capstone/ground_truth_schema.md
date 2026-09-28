# MedMatch Capstone — Ground Truth Schema Specification

> **Status:** Specification Document  
> **Phase:** 1 — Research Problem & Evaluation Design  
> **Author:** MedMatch Research Team  
> **Date:** September 2026  
> **Target System:** MedMatch Clinical Decision-Support Prototype

---

## 1. Label Taxonomy & Distinction

To ensure scientific rigor and clinical safety, MedMatch maintains an explicit semantic distinction between **Criterion-Level Labels** and **Trial-Level Labels**.

```text
+---------------------------------------------------------------------------------+
|                                 LABEL TAXONOMY                                  |
+---------------------------------------------------------------------------------+
|  Level           | Permitted Values             | Evaluation Target             |
|------------------+------------------------------+-------------------------------|
| Criterion-Level  | PASS                         | Specific eligibility rule     |
|                  | FAIL                         | evaluated against clinical    |
|                  | UNKNOWN                      | evidence in patient record    |
|------------------+------------------------------+-------------------------------|
| Trial-Level      | ELIGIBLE                     | Overall trial enrollment      |
|                  | INELIGIBLE                   | recommendation aggregated     |
|                  | NEEDS_REVIEW                 | across all protocol criteria  |
+---------------------------------------------------------------------------------+
```

### 1.1 Criterion-Level Semantics
- **`PASS`**: The patient definitively meets an inclusion requirement (e.g., patient is 52 for an "Age $\ge 18$" criterion) or is confirmed free of an exclusion condition (e.g., negative MRI for "No brain metastases").
- **`FAIL`**: The patient definitively fails an inclusion requirement (e.g., ECOG performance status 3 for "ECOG $\le 1$") or triggers an active exclusion condition (e.g., active hepatitis B infection for "Exclude active hepatitis").
- **`UNKNOWN`**: The clinical encounter narrative or structured record contains insufficient evidence to confirm or refute the criterion (e.g., histology report is missing or molecular panel is pending).

### 1.2 Trial-Level Semantics
- **`ELIGIBLE`**: All protocol inclusion criteria are confirmed `PASS`, and all exclusion criteria are confirmed `PASS`.
- **`INELIGIBLE`**: One or more criteria (inclusion or exclusion) are evaluated as `FAIL`.
- **`NEEDS_REVIEW`**: No criteria are evaluated as `FAIL`, but one or more critical criteria are evaluated as `UNKNOWN`. Human clinical review or supplemental diagnostic testing is required.

---

## 2. Criterion-Level Ground-Truth Schema

Stored as individual records under `data/annotations/criterion_labels/{patient_id}_{trial_id}_{criterion_id}.json` or consolidated JSONL.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "CriterionGroundTruthAnnotation",
  "type": "object",
  "required": [
    "annotation_id",
    "patient_id",
    "trial_id",
    "criterion_id",
    "criterion_type",
    "domain",
    "ground_truth",
    "patient_evidence",
    "criterion_evidence",
    "annotator_metadata"
  ],
  "properties": {
    "annotation_id": {
      "type": "string",
      "description": "Unique identifier for this annotation record, e.g. 'ANN_P001_NCT02484404_C003'"
    },
    "patient_id": {
      "type": "string",
      "description": "Reference identifier of patient profile, e.g. 'P042'"
    },
    "trial_id": {
      "type": "string",
      "description": "Clinical trial NCT accession number, e.g. 'NCT02484404'"
    },
    "criterion_id": {
      "type": "string",
      "description": "Protocol-unique criterion identifier, e.g. 'INC_01' or 'EXC_04'"
    },
    "criterion_type": {
      "type": "string",
      "enum": ["inclusion", "exclusion"],
      "description": "Indicates whether the criterion is an inclusion requirement or an exclusion condition"
    },
    "domain": {
      "type": "string",
      "enum": [
        "demographics",
        "disease_status",
        "genomics_biomarkers",
        "prior_treatments",
        "laboratory_values",
        "performance_status",
        "comorbidities",
        "organ_function",
        "lifestyle_other"
      ],
      "description": "Standardized clinical domain category"
    },
    "ground_truth": {
      "type": "string",
      "enum": ["PASS", "FAIL", "UNKNOWN"],
      "description": "Gold-standard expert evaluation of criterion satisfaction"
    },
    "patient_evidence": {
      "type": "object",
      "required": ["has_evidence", "text_span", "start_char", "end_char", "source_section"],
      "properties": {
        "has_evidence": {
          "type": "boolean",
          "description": "True if evidence was found in patient record; false if UNKNOWN"
        },
        "text_span": {
          "type": "string",
          "description": "Verbatim text quoted from patient narrative supporting evaluation"
        },
        "start_char": {
          "type": "integer",
          "description": "0-based start character offset in raw patient narrative (-1 if absent)"
        },
        "end_char": {
          "type": "integer",
          "description": "0-based end character offset in raw patient narrative (-1 if absent)"
        },
        "source_section": {
          "type": "string",
          "description": "EHR section header where evidence occurs (e.g. 'Past Medical History', 'Laboratory Results')"
        }
      }
    },
    "criterion_evidence": {
      "type": "object",
      "required": ["verbatim_criterion_text"],
      "properties": {
        "verbatim_criterion_text": {
          "type": "string",
          "description": "Exact text from protocol eligibility section"
        }
      }
    },
    "annotator_metadata": {
      "type": "object",
      "required": ["annotator_id", "clinical_qualification", "confidence", "annotated_at"],
      "properties": {
        "annotator_id": { "type": "string" },
        "clinical_qualification": { "type": "string", "enum": ["oncologist", "clinical_fellow", "research_nurse", "nlp_researcher"] },
        "confidence": { "type": "number", "minimum": 1, "maximum": 5 },
        "annotator_notes": { "type": "string" },
        "annotated_at": { "type": "string", "format": "date-time" }
      }
    }
  }
}
```

---

## 3. Trial-Level Ground-Truth Schema

Stored under `data/annotations/trial_labels/{patient_id}_{trial_id}.json`.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "TrialGroundTruthAnnotation",
  "type": "object",
  "required": [
    "patient_id",
    "trial_id",
    "eligibility",
    "total_criteria_count",
    "passing_criteria",
    "failing_criteria",
    "unknown_criteria",
    "clinical_summary",
    "verified_by"
  ],
  "properties": {
    "patient_id": {
      "type": "string",
      "description": "Patient identifier"
    },
    "trial_id": {
      "type": "string",
      "description": "Trial NCT number"
    },
    "eligibility": {
      "type": "string",
      "enum": ["ELIGIBLE", "INELIGIBLE", "NEEDS_REVIEW"],
      "description": "Final gold-standard trial-level eligibility decision"
    },
    "total_criteria_count": {
      "type": "integer"
    },
    "passing_criteria": {
      "type": "array",
      "items": { "type": "string" },
      "description": "List of criterion_ids evaluated as PASS"
    },
    "failing_criteria": {
      "type": "array",
      "items": { "type": "string" },
      "description": "List of criterion_ids evaluated as FAIL"
    },
    "unknown_criteria": {
      "type": "array",
      "items": { "type": "string" },
      "description": "List of criterion_ids evaluated as UNKNOWN"
    },
    "clinical_summary": {
      "type": "string",
      "description": "Synthesized rationale explaining why the patient is eligible, ineligible, or needs review"
    },
    "verified_by": {
      "type": "string",
      "description": "Expert reviewer identifier"
    }
  }
}
```

---

## 4. Deterministic Consistency & Integrity Constraints

Any valid annotation pair must strictly satisfy the following logical consistency constraints:

1. **Partition Completeness:**
   $$|C_T| = |\text{passing\_criteria}| + |\text{failing\_criteria}| + |\text{unknown\_criteria}|$$
2. **Disqualification Dominance:**
   $$|\text{failing\_criteria}| > 0 \iff \text{eligibility} == \text{"INELIGIBLE"}$$
3. **Strict Compliance Requirement:**
   $$\left( |\text{failing\_criteria}| == 0 \land |\text{unknown\_criteria}| == 0 \right) \iff \text{eligibility} == \text{"ELIGIBLE"}$$
4. **Uncertainty Trigger:**
   $$\left( |\text{failing\_criteria}| == 0 \land |\text{unknown\_criteria}| > 0 \right) \iff \text{eligibility} == \text{"NEEDS\_REVIEW"}$$
5. **Span Verification:** If `ground_truth` is `PASS` or `FAIL`, `patient_evidence.has_evidence` MUST be `true`, and the string `patient_evidence.text_span` MUST be an exact substring of patient narrative $N_P$ between character indices `start_char` and `end_char`.
