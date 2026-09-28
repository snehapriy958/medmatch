# MedMatch Capstone — Canonical Eligibility Reasoning Contract
**Contract Version:** `1.0.0`  
**Phase:** 6 — Eligibility Reasoning  

---

## 1. Overview & Architectural Role

The Eligibility Reasoning Contract defines the canonical data exchange boundaries between:
1. **Patient Evidence & Retrieved Criteria Sources:** Structured clinical facts from Phase 4 and candidate trial criteria retrieved in Phase 5.
2. **Eligibility Reasoner:** Evaluates individual atomic criteria into 3-valued truth states (`PASS`, `FAIL`, `UNKNOWN`).
3. **Deterministic Aggregator:** Computes final trial-level eligibility decisions (`ELIGIBLE`, `INELIGIBLE`, `NEEDS_REVIEW`) using strict programmatic rules.
4. **Audit & Downstream Consumers:** Clinician review workflows and verification harnesses.

```
┌─────────────────────────────────┐      ┌──────────────────────────────────┐
│ Phase 4 Patient Clinical Profile│      │ Phase 5 Retrieved Trial Criteria │
│ (ClinicalFacts, Demographics)   │      │ (Inclusion / Exclusion Criteria) │
└────────────────┬────────────────┘      └─────────────────┬────────────────┘
                 │                                         │
                 └────────────────────┬────────────────────┘
                                      ▼
                        ┌───────────────────────────┐
                        │ EligibilityReasoningRequest│
                        └─────────────┬─────────────┘
                                      ▼
                        ┌───────────────────────────┐
                        │ Criterion-Level Reasoner  │
                        │ (PASS / FAIL / UNKNOWN)   │
                        └─────────────┬─────────────┘
                                      ▼
                        ┌───────────────────────────┐
                        │ Deterministic Aggregator  │
                        │ (ELIGIBLE / INELIGIBLE /  │
                        │  NEEDS_REVIEW)            │
                        └─────────────┬─────────────┘
                                      ▼
                        ┌───────────────────────────┐
                        │EligibilityReasoningResponse│
                        └───────────────────────────┘
```

---

## 2. Input Contract: `EligibilityReasoningRequest`

```json
{
  "request_id": "req-20260928-001",
  "patient_id": "patient-synth-001",
  "tenant_id": "hospital-uuid-1234",
  "patient_note": "Optional raw narrative string...",
  "demographics": {
    "age": 62,
    "gender": "FEMALE"
  },
  "patient_facts": [
    {
      "fact_id": "fact-001",
      "concept": "non-small cell lung cancer",
      "assertion": "PRESENT",
      "start_char": 25,
      "end_char": 54,
      "snippet": "diagnosed with non-small cell lung cancer",
      "is_current": true
    },
    {
      "fact_id": "fact-002",
      "concept": "EGFR L858R mutation",
      "assertion": "PRESENT",
      "start_char": 70,
      "end_char": 89,
      "snippet": "confirmed EGFR L858R mutation",
      "is_current": true
    }
  ],
  "candidate_trials": [
    {
      "trial_id": "NCT05212345",
      "title": "Study of Osimertinib in Advanced NSCLC",
      "criteria": [
        {
          "id": "crit-001",
          "criteria_type": "INCLUSION",
          "description": "Histologically confirmed advanced or metastatic non-small cell lung cancer."
        },
        {
          "id": "crit-002",
          "criteria_type": "INCLUSION",
          "description": "Documented presence of EGFR L858R or Exon 19 deletion."
        },
        {
          "id": "crit-003",
          "criteria_type": "EXCLUSION",
          "description": "Prior treatment with third-generation EGFR TKI."
        }
      ]
    }
  ],
  "reasoning_mode": "rule_based"
}
```

---

## 3. Output Contract: `TrialEligibilityEvaluation` & `CriterionEvaluationRecord`

### 3.1 Criterion-Level Assessment (`CriterionEvaluationRecord`)
```json
{
  "criterion_id": "crit-001",
  "trial_id": "NCT05212345",
  "criterion_type": "INCLUSION",
  "criterion_text": "Histologically confirmed advanced or metastatic non-small cell lung cancer.",
  "status": "PASS",
  "reasoning": "Patient is confirmed to have required condition 'non-small cell lung cancer'. Inclusion criterion satisfied.",
  "evidence_citations": [
    {
      "fact_id": "fact-001",
      "text_snippet": "diagnosed with non-small cell lung cancer",
      "source_field": "patient_facts",
      "start_char": 25,
      "end_char": 54,
      "assertion_type": "PRESENT"
    }
  ],
  "patient_fact_references": ["fact-001"],
  "trial_criterion_reference": "trial:NCT05212345#crit-001",
  "is_negated": false,
  "temporal_constraint": null,
  "numerical_threshold": null,
  "uncertainty_notes": null,
  "evaluator": "rule_based_research_reasoner_v1",
  "schema_version": "1.0.0"
}
```

### 3.2 Trial-Level Aggregated Assessment (`TrialEligibilityEvaluation`)
```json
{
  "trial_id": "NCT05212345",
  "trial_title": "Study of Osimertinib in Advanced NSCLC",
  "status": "NEEDS_REVIEW",
  "criterion_evaluations": [
    { "criterion_id": "crit-001", "status": "PASS", "...": "..." },
    { "criterion_id": "crit-002", "status": "PASS", "...": "..." },
    { "criterion_id": "crit-003", "status": "UNKNOWN", "...": "..." }
  ],
  "total_criteria_evaluated": 3,
  "passed_count": 2,
  "failed_count": 0,
  "unknown_count": 1,
  "failed_criterion_ids": [],
  "unknown_criterion_ids": ["crit-003"],
  "passed_criterion_ids": ["crit-001", "crit-002"],
  "clinical_summary": "Needs Review: No criteria failed, but 1 criterion/criteria are unknown (crit-003).",
  "evaluator": "deterministic_aggregator",
  "timestamp": "2026-09-28T21:18:00.000Z"
}
```

---

## 4. Aggregation Rules Invariant

The trial-level status is computed strictly via the following deterministic decision table:

| Condition | Trial Eligibility Status | Clinical Interpretation | Action Required |
| :--- | :--- | :--- | :--- |
| $\text{failed\_count} > 0$ | `INELIGIBLE` | Definitive disqualification: patient violates at least one criterion. | Screen out candidate trial. |
| $\text{failed\_count} == 0 \land \text{unknown\_count} > 0$ | `NEEDS_REVIEW` | Potential candidate: missing or unverifiable clinical data prevents definitive eligibility. | Flag for human clinician manual chart review. |
| $\text{failed\_count} == 0 \land \text{unknown\_count} == 0 \land \text{passed\_count} > 0$ | `ELIGIBLE` | Full qualification: every evaluated criterion is grounded and satisfied. | Recommend trial enrollment evaluation. |
| $\text{total\_criteria} == 0$ | `NEEDS_REVIEW` | Undetermined: zero criteria were provided or evaluated. | Re-run ingestion and criteria extraction. |

---

## 5. Security & Isolation Semantics

- **Tenant Isolation:** Patient facts from Tenant A cannot be evaluated against criteria assigned to Tenant B.
- **Data Minimization:** Raw notes are not persisted to persistent audit tables; evaluations store character offsets and fact pointers.
- **Fail-Safe Abstention:** If a model produces invalid schemas, non-3-valued truth states, or uncited PASS/FAIL decisions, the evaluation fails safely to `NEEDS_REVIEW` with an audit error.
