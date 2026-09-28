# MedMatch Capstone — Eligibility Reasoning Error Taxonomy
**Document Version:** `1.0.0`  
**Phase:** 6 — Eligibility Reasoning  

---

## 1. Scope & Purpose

This taxonomy defines and categorizes failure modes specific to the **eligibility reasoning and aggregation layers**. It explicitly separates reasoning errors from upstream retrieval errors (documented in Phase 5: `retrieval_error_taxonomy.md`).

---

## 2. 15 Canonical Eligibility Reasoning Error Classes

| Error ID | Error Name | Clinical Description & Example | Severity | Mitigation Strategy |
| :---: | :--- | :--- | :---: | :--- |
| **ERR-REA-01** | **Evidence Omission** | Fails to recognize existing patient evidence in EHR that satisfies/violates criterion. (e.g. Note states "ECOG 1", reasoner marks ECOG as UNKNOWN). | High | Multi-synonym medical entity normalization; structured fact extraction. |
| **ERR-REA-02** | **Evidence Hallucination** | System invents non-existent diagnoses, lab values, or medications not in note. | Critical | Mandatory `EvidenceCitation` validation; character offset verification. |
| **ERR-REA-03** | **Incorrect Negation** | Negation is flipped or scope misattributed. (e.g. "No history of stroke" evaluated as having stroke, causing inclusion PASS or exclusion FAIL). | Critical | Dedicated negation scope parsing; assertion validation (`PRESENT` vs `ABSENT`). |
| **ERR-REA-04** | **Temporal Reasoning Error** | Misjudging recency or durations. (e.g. Surgery performed 90 days ago evaluated as "within 30 days"). | High | Formal temporal representation (`duration_days`, anchor-based relative calculus). |
| **ERR-REA-05** | **Numerical Threshold Error** | Misinterpreting operator ($<$, $>$, $\ge$, $\le$) or boundary conditions. (e.g. Platelets 95 x10^9/L evaluated as PASS for $\ge 100$). | High | Deterministic numerical comparison logic; float boundary checks. |
| **ERR-REA-06** | **Unit Error** | Incompatible units compared directly without conversion. (e.g. Creatinine 1.2 mg/dL compared against threshold of 100 $\mu$mol/L). | High | Unit normalization and unit mismatch detection (yielding UNKNOWN). |
| **ERR-REA-07** | **Compound-Logic Error** | Misinterpreting Boolean structures (AND vs OR). (e.g. In "Age $\ge$ 18 AND ECOG $\le$ 1", satisfying age alone is marked as PASS). | High | Explicit compound AST parser and recursive Boolean evaluation. |
| **ERR-REA-08** | **Conflicting-Evidence Error** | Arbitrarily choosing one assertion when patient chart contains contradictory statements. | High | Conflict detection across fact assertion states; mandatory routing to UNKNOWN. |
| **ERR-REA-09** | **UNKNOWN Converted to PASS** | Inferring satisfaction from silence (over-optimistic hallucination). | Critical | Epistemic non-collapsing invariant; absence of evidence is not satisfaction. |
| **ERR-REA-10** | **UNKNOWN Converted to FAIL** | Disqualifying a patient merely because an attribute is unmentioned. | High | Epistemic non-collapsing invariant; absence of evidence is not disqualification. |
| **ERR-REA-11** | **Criterion Misinterpretation** | Misunderstanding clinical intent of criterion (e.g. confusing adjuvant vs neoadjuvant chemotherapy). | High | Ontology mapping and structured criterion decomposition. |
| **ERR-REA-12** | **Unsupported Inference** | Making ungrounded speculative clinical leaps (e.g. inferring liver failure from mildly elevated AST without diagnosis). | High | Restricting reasoner to explicit documented assertions. |
| **ERR-REA-13** | **Provenance Loss** | Evaluating criterion as PASS/FAIL but losing pointer to patient note snippet or fact ID. | Moderate | Strict Pydantic validation requiring evidence citations for PASS/FAIL. |
| **ERR-REA-14** | **Schema Failure** | Output schema validation failure (e.g. missing required fields, non-enum status). | Moderate | Pydantic strict parsing with safe abstention fallback. |
| **ERR-REA-15** | **Aggregation Error** | Inconsistent trial-level aggregation (e.g. trial with 1 FAIL criterion marked as ELIGIBLE). | Critical | Pure programmatic deterministic aggregator (`EligibilityAggregator`). |

---

## 3. Separation from Retrieval Errors

| Upstream Retrieval Error (Phase 5) | Downstream Reasoning Error (Phase 6) |
| :--- | :--- |
| Candidate trial not retrieved from database. | Candidate trial retrieved, but criterion evaluated incorrectly. |
| Omission of relevant exclusion criterion during search. | Exclusion criterion present in context, but negated status misunderstood. |
| Cross-tenant leakage of trial embedding. | Valid tenant context, but aggregation rule violated. |

This taxonomy guarantees that when benchmark evaluation is executed, failure causes are attributed to the exact pipeline stage responsible.
