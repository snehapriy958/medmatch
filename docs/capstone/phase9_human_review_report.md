# Phase 9 Final Report: Formal Uncertainty & Human Review Foundation

## 1. Executive Summary & Objective

Phase 9 establishes the formal uncertainty and human-review foundation for MedMatch. The objective is to make clinical and epistemic uncertainty **explicit, measurable, auditable, and safely routable to human clinician review**.

The goal is **not** to make the model artificially more confident or autonomous. Instead, Phase 9 ensures that whenever information is missing, conflicting, ambiguous, ungrounded, or insufficient, automated eligibility reasoning safely yields to human clinical judgment through a reproducible, transparent adjudication workflow.

---

## 2. Audit Findings

Documented in [`docs/capstone/phase9_uncertainty_audit.md`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase9_uncertainty_audit.md):

1. **Patient Fact Uncertainty (Phase 4)**: Captured via `ClinicalFact` uncertainty and assertion enums. Phase 4 established the critical distinction between `NOT_MENTIONED` and negative assertions.
2. **Retrieval Uncertainty (Phase 5)**: Captured via chunk similarity scores and rank. Low or empty chunk sets were previously returned as empty evidence without explicit uncertainty propagation.
3. **Reasoning Uncertainty (Phase 6)**: Three-valued criterion evaluations (`PASS`, `FAIL`, `UNKNOWN`) and deterministic trial aggregation (`ELIGIBLE`, `INELIGIBLE`, `NEEDS_REVIEW`). Phase 6 maintained strict aggregation rules but lacked fine-grained tracking of the root cause of `UNKNOWN` verdicts.
4. **Grounding Uncertainty (Phase 8)**: Phase 8 identified ungrounded claims (`UNSUPPORTED`), contradictions (`CONTRADICTED`), and hallucination categories (H1–H10), but did not provide a workflow to route detected hallucinations to human oversight.
5. **Phase 9 Integration**: Connects these layers into an end-to-end uncertainty propagation pipeline.

---

## 3. Implemented Components

All Phase 9 components are implemented as modular, research-grade software under `scripts/`:

### 3.1 Canonical Uncertainty Model ([`scripts/uncertainty_schema.py`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/uncertainty_schema.py))
- Strongly typed Pydantic models:
  - `UncertaintyStatus`: `RESOLVED`, `MISSING`, `CONFLICTING`, `AMBIGUOUS`, `STALE`, `LOW_CONFIDENCE`, `INSUFFICIENT_EVIDENCE`.
  - `UncertaintySeverity`: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.
  - `UncertaintyType`: 10 distinct taxonomic origins including missing facts, document conflicts, temporal/numerical ambiguity, grounding contradictions, and clinical boundary ambiguity.
  - `ConflictEvidenceItem`: Detailed representation of competing assertions across documents/dates.
  - `UncertaintyRecord`: Atomic verifiable uncertainty representation with severity-based machine decision constraints.
  - `UncertaintyProfile`: Case-level aggregation of uncertainties with automated count recomputation.

### 3.2 Human Review Decision Model ([`scripts/review_schema.py`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/review_schema.py))
- Strongly typed workflow models:
  - `ReviewStatus`: `NOT_REQUIRED`, `PENDING_REVIEW`, `IN_REVIEW`, `RESOLVED`, `ESCALATED`.
  - `ReviewerDecision`: `CONFIRM_PASS`, `CONFIRM_FAIL`, `RESOLVE_PASS`, `RESOLVE_FAIL`, `INSUFFICIENT_EVIDENCE`, `ESCALATE`.
  - `ReviewPriority`: `ROUTINE`, `PRIORITY`, `ESCALATED`.
  - `ReviewerIdentity`: Synthetic, non-PHI reviewer identity.
  - `HumanReviewRecord`: Complete review record preserving `original_machine_output` immutably.
  - `ReviewResolutionRequest`: Enforces that reviewer overrides (`RESOLVE_PASS`, `RESOLVE_FAIL`) strictly require supporting evidence citations.

### 3.3 Review-Routing Policy ([`scripts/review_policy.py`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/review_policy.py))
- Connects Phase 6 aggregation and Phase 8 grounding to Phase 9 review states:
  - Clean `ELIGIBLE`: Permitted autonomously only when all criteria PASS with zero unresolved uncertainties.
  - Clean `INELIGIBLE`: Permitted autonomously only when failure is grounded and free of conflict.
  - Intercepted to `PENDING_REVIEW` when criteria are UNKNOWN, facts missing, data ambiguous, or machine claims unsupported.
  - Escalated to `ESCALATED` on active contraindication conflicts or grounding contradictions (H6).

### 3.4 Review Prioritization Engine ([`scripts/review_priority.py`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/review_priority.py))
- Transparent, deterministic triage assigning `ROUTINE`, `PRIORITY`, or `ESCALATED` based on safety severity, contradiction presence, single gatekeeper impact, and uncertainty accumulation ($\ge 3$ unresolved).

### 3.5 Conflict Resolution Policy ([`docs/capstone/phase9_conflict_resolution.md`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase9_conflict_resolution.md))
- Formal rules governing dynamic lab recency updates versus unresolvable cross-document discordance.

### 3.6 Audit Trail & Resolution Manager ([`scripts/review_audit.py`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/review_audit.py))
- Chronological append-only lifecycle tracking: `uncertainty_detected`, `review_requested`, `review_started`, `reviewer_decision_recorded`, `review_resolved`, `review_escalated`.
- Enforces immutability of machine reasoning and rejects reviewer overrides lacking evidence.

### 3.7 Uncertainty Metrics Engine ([`scripts/uncertainty_metrics.py`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/uncertainty_metrics.py))
- Computes 11 formal metrics (UR, MIR, CR, AR, IER, RRR, ResR, ER, ARRR, UADR, EBRR) with zero-denominator safety.

### 3.8 Experiment Harness ([`scripts/human_review_experiment.py`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/human_review_experiment.py))
- End-to-end execution harness with empirical benchmark guardrail (`has_validated_benchmark() == False`).

### 3.9 Core Safety Guardrails (12 Mandatory Invariants)
Formalized in [`docs/capstone/phase9_error_taxonomy.md`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase9_error_taxonomy.md) and programmatically validated across `tests/human_review/`:
1. **Missing $\neq$ Negative**: Chart silence (`NOT_MENTIONED`) is never treated as negative evidence; yields `UNKNOWN`.
2. **Unknown $\neq$ FAIL**: Indeterminate criteria are never collapsed into disqualifications without explicit contradictory evidence.
3. **Unknown Must Not Silently Become PASS**: Indeterminate criteria never satisfy an inclusion or clear an exclusion.
4. **Unsupported Evidence Cannot Become a Definitive Decision**: Claims flagged `UNSUPPORTED` (H1/H8) cannot generate autonomous `ELIGIBLE` status.
5. **Contradicted Evidence Cannot Be Silently Ignored**: Claims flagged `CONTRADICTED` (H6) escalate immediately and block approval.
6. **Reviewer Decisions Must Not Erase Machine Outputs**: Adjudication records append to audit history; `original_machine_output` remains strictly immutable.
7. **Reviewer Overrides Require Evidence**: Overrides (`RESOLVE_PASS`, `RESOLVE_FAIL`) strictly require supporting evidence references or are rejected with `ValueError`.
8. **Automated Decisions Must Remain Deterministic**: Identical patient and protocol inputs always yield identical routing and priority states.
9. **Uncertainty Must Be Observable & Measurable**: All uncertainties are instantiated as structured `UncertaintyRecord` items with verifiable provenance.
10. **Human Review Is Mandatory Under Predefined Conditions**: When uncertainty criteria trigger review, routing cannot be bypassed by model confidence.
11. **No Fact Fabrication**: Clinical entities, dates, or values absent from evidence cannot be synthesized to bridge missing facts.
12. **No Unwarranted Clinical Validation Claims**: Guardrail `has_validated_benchmark() == False` strictly enforced; empirical clinical performance claims are prohibited without external benchmark ingestion.

---

## 4. Synthetic Development Test Fixtures

Located in [`data/fixtures/phase9/human_review_fixtures.json`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/data/fixtures/phase9/human_review_fixtures.json), with documentation in [`data/fixtures/phase9/README.md`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/data/fixtures/phase9/README.md).

Contains **18 comprehensive test scenarios**:
1. `case-01-complete-evidence-eligible`: Full evidence $\rightarrow$ automatic `ELIGIBLE` (`NOT_REQUIRED`).
2. `case-02-complete-disqualifying-ineligible`: Grounded disqualification $\rightarrow$ automatic `INELIGIBLE` (`NOT_REQUIRED`).
3. `case-03-missing-required-patient-fact`: Missing HER2 status $\rightarrow$ `PENDING_REVIEW` (`PRIORITY`).
4. `case-04-conflicting-patient-facts`: Conflicting penicillin allergy $\rightarrow$ `ESCALATED` (`ESCALATED`).
5. `case-05-conflicting-documents`: Discordant histology across reports $\rightarrow$ `PENDING_REVIEW` (`PRIORITY`).
6. `case-06-ambiguous-temporal-relationship`: Vague "recent" chemo $\rightarrow$ `PENDING_REVIEW` (`PRIORITY`).
7. `case-07-ambiguous-numerical-value`: Approximated ~8% HbA1c $\rightarrow$ `PENDING_REVIEW` (`PRIORITY`).
8. `case-08-insufficient-retrieval-evidence`: Empty protocol retrieval $\rightarrow$ `PENDING_REVIEW` (`PRIORITY`).
9. `case-09-grounding-unsupported-intercepted`: Machine hallucination intercepted $\rightarrow$ `PENDING_REVIEW` (`PRIORITY`).
10. `case-10-grounding-contradicted-escalated`: Contradicted smoking assertion $\rightarrow$ `ESCALATED` (`ESCALATED`).
11. `case-11-reviewer-resolves-unknown`: Reviewer resolves with outside pathology $\rightarrow$ `RESOLVED`.
12. `case-12-reviewer-confirms-fail`: Reviewer confirms low ejection fraction $\rightarrow$ `RESOLVED`.
13. `case-13-reviewer-confirms-pass-eligible`: Single unknown resolved $\rightarrow$ patient becomes `ELIGIBLE`.
14. `case-14-reviewer-escalates`: Quiescent autoimmune disease referred to PI $\rightarrow$ `ESCALATED`.
15. `case-15-multiple-unresolved-criteria-priority`: 4 unrecorded labs $\rightarrow$ triage `PRIORITY`.
16. `case-16-resolved-review-preserves-machine-output`: `original_machine_output` preserved intact after resolution.
17. `case-17-missing-evidence-never-negative`: Absence of diabetes mention remains `UNKNOWN`.
18. `case-18-reviewer-override-without-evidence-rejected`: Override lacking citations rejected with `ValueError`.

---

## 5. Verification & Test Results

All test suites were executed deterministically:

### 5.1 Phase 9 Human Review Suite (`tests/human_review/`)
- Total Tests: **26 passed in 0.91s** (100% passing)
  - `test_uncertainty_schema.py`: 5 passed
  - `test_review_schema.py`: 5 passed
  - `test_review_policy.py`: 6 passed
  - `test_review_audit.py`: 4 passed
  - `test_uncertainty_metrics.py`: 2 passed
  - `test_phase9_fixtures.py`: 2 passed (validating all 18 cases)
  - `test_phase9_isolation.py`: 2 passed

### 5.2 Complete Research Regression Test Suites (Phases 2–8)
- `tests/grounding_evaluation` (Phase 8): **36 passed**
- `tests/rag_evaluation` (Phase 7): **29 passed**
- `tests/eligibility` (Phase 6): **31 passed**
- `tests/retrieval` (Phase 5): **21 passed**
- `tests/patient_information` (Phase 4): **31 passed**
- `tests/document_intelligence` (Phase 3): **45 passed**
- `tests/dataset` (Phase 2): **17 passed**
- **Combined Research Test Count**: **236 passed** across all research suites.

### 5.3 Production AI-Service Suite
- `services/ai-service/tests`: **45 passed, 1 warning** (0 failures).

---

## 6. Production Isolation Verification

Strict production isolation was verified:
1. `git diff --stat services/`: Completely empty (0 files modified).
2. AST and regex pattern scan across `services/`: **Zero** Phase 9 modules or classes imported.
3. Matcher behavior, Gemini prompts, API routes, database schemas, and Alembic migrations remain completely untouched.

---

## 7. Empirical Benchmark Guardrails

- `has_validated_benchmark() == False` is programmatically enforced.
- No empirical clinical claims, clinical trial matching accuracy gains, or clinical safety metrics are asserted.
- All evaluation is explicitly designated as **development validation only**.

---

## 8. Limitations

1. **Synthetic Scenarios**: The 18 test fixtures model archetypal clinical edge cases; they do not represent real hospital EHR patient distributions.
2. **Rule-Based Triage**: Priority categories (`ROUTINE`, `PRIORITY`, `ESCALATED`) are deterministic triage heuristic aids, not medical acuity scores.
3. **No Interactive UI**: In accordance with the Phase 9 scope boundary, review adjudication is currently an API/Python contract; UI dashboards and explainability graphs are reserved for Phase 10.

---

## 9. Phase 10 Boundary

The following systems are **strictly excluded** from Phase 9 and reserved for future phases:
- Explainability & interactive evidence graph UI (Phase 10)
- Production clinician authentication and portal integration
- Real hospital EHR connector ingestion
- External benchmark dataset ingestion

Phase 9 terminates at the **formal uncertainty representation and human-review foundation**.

---

## 10. Final Verification Checklist

| Item | Description | Status | Evidence |
|:---|:---|:---|:---|
| **A** | **Uncertainty Model** | **PASS** | [`scripts/uncertainty_schema.py`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/uncertainty_schema.py) implements 7 statuses, 4 severities, 10 types, conflict details, and profile containers. |
| **B** | **Review Workflow Model** | **PASS** | [`scripts/review_schema.py`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/review_schema.py) implements review states, decisions, priority, and resolution request contracts. |
| **C** | **Routing Policy** | **PASS** | [`scripts/review_policy.py`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/review_policy.py) connects Phase 6 and 8 outputs; permits autonomous decisions only when verified; routes uncertainty. |
| **D** | **Review Prioritizer** | **PASS** | [`scripts/review_priority.py`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/review_priority.py) deterministically assigns ROUTINE, PRIORITY, ESCALATED. |
| **E** | **Conflict Resolution** | **PASS** | [`docs/capstone/phase9_conflict_resolution.md`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase9_conflict_resolution.md) formalizes temporal recency rules and discordance handling. |
| **F** | **Audit Trail** | **PASS** | [`scripts/review_audit.py`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/review_audit.py) records append-only events and preserves original machine output immutably. |
| **G** | **Safety Guardrails** | **PASS** | 12 guardrails enforced (missing $\neq$ negative, evidence required for override, machine output preserved). |
| **H** | **Uncertainty Metrics** | **PASS** | [`scripts/uncertainty_metrics.py`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/scripts/uncertainty_metrics.py) computes 11 formal metrics with zero-denominator safety. |
| **I** | **Development Fixtures** | **PASS** | 18 scenarios in [`data/fixtures/phase9/human_review_fixtures.json`](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/data/fixtures/phase9/human_review_fixtures.json). |
| **J** | **Tests** | **PASS** | 26 Phase 9 tests passing, 236 research tests passing, 45 production tests passing. |
| **K** | **Production Isolation** | **PASS** | `git diff --stat services/` is clean; zero production imports. |
| **L** | **Phase 10 Boundary** | **PASS** | No evidence graph UI or Phase 10 features started. Work stopped at review foundation. |
