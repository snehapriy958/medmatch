# MedMatch Capstone — Phase 6: Eligibility Reasoning Final Milestone Report
**Milestone:** Phase 6 — Eligibility Reasoning  
**Status:** IMPLEMENTATION COMPLETE — AWAITING USER ACCEPTANCE  
**Date:** 2026-09-28  

---

## 1. Executive Summary

Phase 6 establishes the research-grade **eligibility-reasoning layer** for MedMatch, building directly upon the retrieval foundation completed in Phase 5. The primary research question addressed is:
> *"Can evidence-grounded, criterion-level reasoning produce reproducible and auditable eligibility assessments while explicitly representing uncertainty and missing information?"*

To investigate this question without disrupting production infrastructure, Phase 6:
1. Audited current production eligibility evaluation (`MatchingService`, `PromptBuilder`, `TRIAL_MATCHING_PROMPT`, `EligibilityResponse`).
2. Defined a canonical 3-valued research model (`PASS`, `FAIL`, `UNKNOWN`) in `scripts/eligibility_schema.py`.
3. Designed and implemented pure deterministic aggregation (`scripts/eligibility_aggregator.py`), removing trial-level decision aggregation from the LLM.
4. Implemented an evidence-grounded reasoning engine (`scripts/eligibility_reasoner.py`) supporting clinical negations, numerical threshold validation, temporal windows, compound logic, and conflicting evidence detection.
5. Established an invariant-verifying validation harness (`scripts/validate_eligibility.py`) enforcing mandatory evidence citations for `PASS`/`FAIL` decisions.
6. Formulated comprehensive policies on evidence citation and uncertainty propagation (`eligibility_evidence_policy.md`, `eligibility_uncertainty_policy.md`).
7. Created a 15-class reasoning error taxonomy (`eligibility_reasoning_error_taxonomy.md`).
8. Verified full functionality across 31 Phase 6 unit tests (145 research tests in total) with zero modifications to production code.

---

## 2. Existing Production Architecture & Research Gaps

### 2.1 Production Baseline Audit
In the current production platform (`services/ai-service/app/services/matching_service.py`):
- `MatchingService.evaluate_eligibility` retrieves trial criteria via pgvector dense cosine search.
- The criteria are grouped by trial and injected into `PromptBuilder.build_matching_prompt`.
- A single monolithic prompt (`TRIAL_MATCHING_PROMPT`) is sent to Google Gemini via `LLMService.evaluate_eligibility`.
- Gemini directly returns `EligibilityResponse` objects containing an overall decision (`Eligible`, `Not Eligible`, `Possibly Eligible`) alongside unstructured lists of text strings (`matched_inclusion`, `failed_inclusion`, etc.).

### 2.2 Research Gaps Identified
1. **Unstructured Criterion Reasoning:** Production returns free-text strings rather than atomic criterion evaluation records with verified IDs, confidence scores, and character offsets.
2. **LLM-Controlled Aggregation:** Gemini directly decides trial-level eligibility. If a single exclusion criterion fails, the LLM may still erroneously label a trial "Eligible" or "Possibly Eligible".
3. **Absence of 3-Valued Semantics:** Missing information is often collapsed into either implicit satisfaction or disqualification without formal representation of epistemic uncertainty.
4. **Vulnerability to Uncited Assertions:** The LLM can assert that a criterion was met without citing a corresponding snippet from the patient chart.

---

## 3. Canonical Research Model & Schemas

Defined in [`scripts/eligibility_schema.py`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/eligibility_schema.py):

### 3.1 3-Valued Truth States (`CriterionEvaluationStatus`)
- **`PASS`**: Clinical evidence definitively satisfies the criterion.
- **`FAIL`**: Clinical evidence definitively contradicts or violates the criterion.
- **`UNKNOWN`**: Evidence is missing, incomplete, uncertain, or contradictory.

### 3.2 Canonical Data Structures
- **`EvidenceCitation`**: Grounds an evaluation in an exact text snippet, character spans (`start_char`, `end_char`), source field, and `fact_id`.
- **`CriterionEvaluationRecord`**: Atomic evaluation containing `criterion_id`, `criterion_type` (`INCLUSION`/`EXCLUSION`), `status`, `reasoning`, `evidence_citations`, `patient_fact_references`, `is_negated`, `temporal_constraint`, and `numerical_threshold`.
- **`TrialEligibilityEvaluation`**: Aggregated assessment containing `trial_id`, `status` (`ELIGIBLE`, `INELIGIBLE`, `NEEDS_REVIEW`), summary counts, and criterion ID partitions.

---

## 4. Evidence Grounding & Mandatory Citation Policy

Enforced by [`docs/capstone/eligibility_evidence_policy.md`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/eligibility_evidence_policy.md):
- **Mandatory Citation Invariant:** Any `PASS` or `FAIL` criterion evaluation **must** cite at least one verified evidence snippet or patient fact reference.
- **Unsupported Assertion Rejection:** Any evaluation attempting to emit `PASS` or `FAIL` without evidence is rejected by `validate_eligibility.py` or safely demoted to `UNKNOWN`.
- **Silence Rule:** *Absence of evidence is NEVER evidence of absence.* If a medical condition is unmentioned in the chart, it is classified as `UNKNOWN`, not `ABSENT`.

---

## 5. Negation, Assertion & Uncertainty Semantics

Implemented in [`scripts/eligibility_reasoner.py`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/eligibility_reasoner.py):
- Evaluates clinical assertion states from Phase 4 facts (`PRESENT`, `ABSENT`, `POSSIBLE`).
- **Inclusion Criteria:**
  - `PRESENT` $\to$ `PASS` (Supported requirement)
  - `ABSENT` $\to$ `FAIL` (Violated requirement)
  - `POSSIBLE` / Unmentioned $\to$ `UNKNOWN`
- **Exclusion Criteria:**
  - `PRESENT` $\to$ `FAIL` (Exclusion triggered)
  - `ABSENT` $\to$ `PASS` (Exclusion cleared / satisfied)
  - `POSSIBLE` / Unmentioned $\to$ `UNKNOWN`
- **Contradictory Evidence:** If patient facts document both `PRESENT` and `ABSENT` for the same condition, the reasoner flags the conflict and routes to `UNKNOWN`.

---

## 6. Numerical & Temporal Reasoning

### 6.1 Numerical & Laboratory Thresholds
- Supports operators ($<$, $\le$, $>$, $\ge$, $=$, $\ne$).
- Extracts parameters (e.g. `age`, `creatinine`, `platelets`, `ecog`).
- Verifies unit alignment: if criterion specifies `mg/dL` and patient fact provides `umol/L`, direct comparison is rejected and routed to `UNKNOWN` with a unit mismatch alert.

### 6.2 Temporal Constraint Calculus
- Checks temporal windows (e.g. "within 30 days").
- Compares criterion allowable windows against fact `duration_days`.
- Distinguishes active vs historical conditions: if criterion requires "active" disease and fact is marked historical, evaluates to `FAIL` or `UNKNOWN`.

---

## 7. Compound Criteria Logic (AND / OR)

- **`AND` Semantics:**
  - `FAIL` if **any** sub-criterion is `FAIL`.
  - `UNKNOWN` if no `FAIL`, but at least one sub-criterion is `UNKNOWN`.
  - `PASS` if **all** sub-criteria are `PASS`.
- **`OR` Semantics:**
  - `PASS` if **at least one** sub-criterion is `PASS`.
  - `FAIL` if **all** sub-criteria are `FAIL`.
  - `UNKNOWN` if no `PASS`, but at least one sub-criterion is `UNKNOWN`.

---

## 8. Deterministic Trial-Level Aggregation

Implemented in [`scripts/eligibility_aggregator.py`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/eligibility_aggregator.py):
The LLM is completely excluded from determining final trial-level eligibility. Aggregation is executed via pure, side-effect-free code:

$$\text{TrialStatus} = \begin{cases} 
\text{INELIGIBLE} & \text{if } |\{c \mid c.\text{status} = \text{FAIL}\}| > 0 \\ 
\text{NEEDS\_REVIEW} & \text{else if } |\{c \mid c.\text{status} = \text{UNKNOWN}\}| > 0 \\ 
\text{ELIGIBLE} & \text{else if } |\{c \mid c.\text{status} = \text{PASS}\}| = N \land N > 0 \\ 
\text{NEEDS\_REVIEW} & \text{else (empty criteria, } N = 0\text{)} 
\end{cases}$$

---

## 9. Evaluation Methodology & Error Taxonomy

- **Evaluation Design ([`phase6_eligibility_evaluation.md`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase6_eligibility_evaluation.md)):** Defines precision, recall, macro-F1, $3 \times 3$ confusion matrix across `{PASS, FAIL, UNKNOWN}`, trial-level macro-F1, and evidence grounding rates.
- **Error Taxonomy ([`eligibility_reasoning_error_taxonomy.md`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/eligibility_reasoning_error_taxonomy.md)):** Details 15 failure classes distinguishing reasoning errors (evidence omission, incorrect negation, unit mismatch) from upstream retrieval errors.
- **Empirical Status:** Empirical benchmark scoring remains **PENDING** real benchmark dataset ingestion. The Phase 2 6-patient synthetic fixture is NOT cited as empirical evidence.

---

## 10. Test Execution Results

### 10.1 Research Test Suites (Root Workspace)
Executed via `services\ai-service\.venv\Scripts\python.exe -m pytest tests -v`:
- **Phase 6 Eligibility Tests (`tests/eligibility/`):** **31 passed**
  - `test_eligibility_schema.py`: 6 passed
  - `test_eligibility_aggregator.py`: 8 passed
  - `test_eligibility_reasoner.py`: 13 passed
  - `test_eligibility_validator.py`: 4 passed
- **Phase 5 Retrieval Tests (`tests/retrieval/`):** **21 passed**
- **Phase 4 Patient Information Tests (`tests/patient_information/`):** **31 passed**
- **Phase 3 Document Intelligence Tests (`tests/document_intelligence/`):** **45 passed**
- **Phase 2 Dataset Tests (`tests/dataset/`):** **17 passed**
- **Total Research Tests:** **145 passed in 0.60s**

### 10.2 Production AI Service Test Suite
Executed via `.venv\Scripts\python.exe -m pytest tests -v` in `services/ai-service`:
- **Production Tests:** **45 passed in 52.17s** (all passed, zero regressions).

---

## 11. Production Impact & Phase Boundary

1. **Zero Modifications to Production Services:** `services/ai-service/` remains 100% untouched.
2. **Retrieval Pipeline Unchanged:** Phase 5 retrieval contracts and algorithms remain locked.
3. **Decoupled Architecture:** Phase 6 reasoning components reside entirely in `scripts/` and `tests/eligibility/`.
4. **No Premature Phase 7:** End-to-end evaluation, RAG-vs-non-RAG comparisons, and clinician validation studies belong to Phase 7 and have **NOT** been started.

---

## 12. Explicit Non-Validation Statement

> [!CAUTION]
> **DISCLAIMER:**  
> MedMatch is an academic capstone research decision-support framework. It is **NOT** a clinically validated autonomous diagnostic or eligibility determination system. It has not been approved by the FDA, EMA, or institutional review boards. All algorithmic outputs require human clinical review by a licensed oncologist or principal investigator.
