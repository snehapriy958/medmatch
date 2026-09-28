# Phase 12 Final Clinical Safety Report

**Document ID:** REPORT-SAFETY-P12  
**Phase:** Phase 12 — Clinical Safety  
**Base Checkpoint:** `7d2cac9`  
**Status:** COMPLETE — AWAITING USER ACCEPTANCE  
**Classification:** SYNTHETIC RESEARCH BENCHMARK ONLY  

> [!CAUTION]
> **MANDATORY EPISTEMIC DISCLAIMER**  
> This system is an academic capstone research prototype. All evaluations, error injections, and experiments documented herein were executed exclusively on **synthetic development fixtures**.  
> **DO NOT** interpret results as establishing real-world clinical safety, clinical validity, diagnostic efficacy, or regulatory compliance (e.g., FDA SaMD, EU MDR). Real clinical deployment strictly requires prospective clinical validation and formal regulatory clearance.

---

## 1. Executive Summary & Epistemic Boundaries

Phase 12 establishes a formal, deterministic **Clinical Safety Layer** for the MedMatch clinical trial eligibility platform. In clinical decision support, errors are asymmetric: false inclusion in a cytotoxic trial can expose a patient to fatal toxicity, while ungrounded exclusion deprives a patient of therapeutic opportunity. 

To prevent automated systems from converting uncertainty into unwarranted eligibility, Phase 12 implements a 7-layer defense architecture enforcing the foundational principle:

$$\text{Missing Information} \ne \text{Negative Evidence} \quad \land \quad \text{UNKNOWN} \ne \text{FAIL} \quad \land \quad \text{UNKNOWN} \not\to \text{PASS}$$

### The Four Rigorous Distinctions
As mandated by the Phase 12 specification, this report explicitly distinguishes between:
1. **Formally Specified Mechanisms:** Abstract mathematical policies and invariants (POL-01 to POL-20, INV-01 to INV-15) defining conservative reasoning semantics.
2. **Implemented and Tested Mechanisms:** Deterministic Python code (`scripts/safety_gates.py`, `scripts/safety_validator.py`, `scripts/safety_policy.py`) programmatically enforcing gates and verifying invariants.
3. **Properties Demonstrated on Synthetic Fixtures:** Empirical observations on 24 curated synthetic test cases (`data/fixtures/phase12/safety_scenarios.json`) demonstrating interception of simulated failure modes.
4. **Clinical Validation:** Real-world patient trials, prospective multi-center studies, and physician concordances—**NONE** of which have been performed or are claimed here.

---

## 2. Production Service Audit: Retrieval-Omission Finding

An audit of the current production codebase (`services/ai-service/app/services/matching_service.py`) verified the concrete behavior when trial retrieval returns zero criteria:

- **Exact Function:** `MatchingService.evaluate_eligibility` in `services/ai-service/app/services/matching_service.py`
- **Exact Branch:** Lines 541–597 (`if not filtered_criteria:`)
- **Exact Return Value:** Emits an `EligibilityEvaluationResponse` containing:
  ```python
  EligibilityResponse(
      eligibility=EligibilityStatus.POSSIBLY_ELIGIBLE,
      confidence=0.0,
      trial_ids_evaluated=[],
      summary="No matching clinical trial criteria were retrieved. Eligibility cannot be determined.",
      missing_information=["No matching clinical trial criteria available."],
      recommendation="Retrieve additional clinical trial criteria before making an eligibility determination.",
      reasoning="No trial criteria were retrieved for this patient. Therefore, eligibility cannot be determined...",
  )
  ```
- **Reachability:** Fully reachable whenever semantic retrieval returns no criteria above threshold or the database contains no matching criteria for the hospital.
- **Downstream Handling:** Returned directly to the API caller via `app/api/routes/matching.py` (line 120) with HTTP status 200.
- **User Visibility:** Fully user-visible in API responses and web UI components.
- **Downstream Review Interception:** Phase 9 review routing currently resides in research harness code (`scripts/review_policy.py`) and is **NOT** invoked inline in the production endpoint; thus `POSSIBLY_ELIGIBLE` is emitted directly.
- **Identified Production Safety Gap:** While `confidence=0.0` and the summary message clearly disclose the absence of criteria, using the enum status `POSSIBLY_ELIGIBLE` rather than an explicit fail-closed error code (`INSUFFICIENT_RETRIEVAL_DATA` or `NEEDS_REVIEW`) risks downstream client systems filtering for positive candidates and treating zero-retrieval matches as potentially eligible.

---

## 3. Methodological Precision: Temporal & Unit Policies

### Temporal Validity Policy
- **Criterion-Dependent:** Temporal validity is strictly criterion-dependent. If a trial protocol defines a time window (e.g., prior therapy washout $\ge 28$ days or baseline laboratory tests within 14 days), that protocol threshold is enforced.
- **Synthetic Research Parameter:** A generic 90-day threshold is utilized strictly as a synthetic research fixture test parameter (e.g., dynamic oncology lab tests), **NOT** as a universal clinical rule.
- **Conservative Default:** Uninterpretable or unsupported temporal semantics strictly default to `UNKNOWN` and escalate to clinician review.

### Measurement Unit Safety
- **Supported Research Conversions:** Unit normalization is validated for tested oncology research fixture units:
  - Creatinine: $\mu\text{mol/L} \leftrightarrow \text{mg/dL}$ (factor 88.42)
  - Platelets / Leukocytes: $10^9/\text{L} \leftrightarrow \text{K}/\mu\text{L}$ (equivalence)
- **Unsupported Units:** Any units outside the tested research domain (e.g. enzyme activity units U/L vs mg/dL, mass vs volume without density) are **NOT** silently converted; they produce an explicit unsupported-unit condition (`S11`) and force `UNKNOWN`.
- **Ontology Boundary:** The conversion framework represents research fixture coverage, **NOT** an exhaustive clinical unit ontology (such as UCUM).

---

## 4. Canonical Safety Error Taxonomy (S1 to S24)

| Code | Error Category | Default Severity | Primary Defense Tier | Target Component |
| :--- | :--- | :--- | :--- | :--- |
| **S1** | Fabricated Patient Fact | CRITICAL | PREVENTION | Fact Extraction |
| **S2** | Fabricated Trial Criterion | CRITICAL | PREVENTION | Document Intelligence |
| **S3** | Unsupported Clinical Inference | HIGH | DETECTION | Criterion Reasoning |
| **S4** | Missing Info Treated as Negative | CRITICAL | MITIGATION | Open-World Evaluator |
| **S5** | UNKNOWN Treated as PASS | CRITICAL | MITIGATION | Aggregator / Reasoner |
| **S6** | UNKNOWN Treated as FAIL | HIGH | MITIGATION | Aggregator / Reasoner |
| **S7** | Contradictory Evidence Ignored | HIGH | HUMAN_REVIEW | Conflict Detector |
| **S8** | Negation Extraction Error | CRITICAL | MITIGATION | Negation Parser |
| **S9** | Temporal Washout Violation | CRITICAL | MITIGATION | Temporal Reasoner |
| **S10**| Numerical Threshold Error | CRITICAL | MITIGATION | Numerical Comparator |
| **S11**| Unit / Measurement Mismatch | CRITICAL | PREVENTION | Unit Normalizer |
| **S12**| Compound Criterion Logic Error | HIGH | MITIGATION | Boolean Aggregator |
| **S13**| Retrieval Omission of Criteria | HIGH | PREVENTION | Candidate Retrieval |
| **S14**| Unsupported Eligibility Decision | CRITICAL | PREVENTION | Decision Aggregator |
| **S15**| Hallucinated Explanation Claim | HIGH | PREVENTION | Explanation Generator|
| **S16**| Provenance Offset Mismatch | MEDIUM | DETECTION | Citation Engine |
| **S17**| Citation / Evidence Mismatch | MEDIUM | DETECTION | Grounding Engine |
| **S18**| Human-Review Routing Failure | HIGH | HUMAN_REVIEW | Review Router |
| **S19**| Unsafe Reviewer Override | CRITICAL | PREVENTION | Review Audit Harness |
| **S20**| Audit-Trail Persistence Loss | HIGH | PREVENTION | Audit Logger |
| **S21**| Cross-Tenant Leakage | CRITICAL | PREVENTION | Tenant Boundary Guard|
| **S22**| Stale Clinical Information Used | HIGH | MITIGATION | Temporal Decay Engine|
| **S23**| Ambiguous Presented as Definitive| HIGH | MITIGATION | Calibrator |
| **S24**| Insufficient Evidence Undisclosed| HIGH | DETECTION | Discloser |

---

## 5. Machine-Checkable Safety Invariants (INV-01 to INV-15)

- **INV-01 (Fact Provenance):** Every extracted patient fact must resolve to verbatim clinical text in the source note.
- **INV-02 (Protocol Integrity):** Every evaluated criterion must belong strictly to the hydrated target protocol schema.
- **INV-03 (Strict Unknowns):** No trial can be declared `ELIGIBLE` while any criterion remains `UNKNOWN`.
- **INV-04 (Open-World Guard):** Zero documented clinical evidence must yield `UNKNOWN`, never `FAIL` or `PASS`.
- **INV-05 (Supported Criteria):** Every `PASS` or `FAIL` status requires non-empty, validated evidence citations.
- **INV-06 (Supported Decisions):** An `ELIGIBLE` decision requires 0 unknowns and 0 fails.
- **INV-07 (Traceability Mandate):** Definitive decisions must cite explicit patient fact IDs and source spans.
- **INV-08 (Valid Provenance):** Provenance coordinates must match verbatim substring slices in the clinical note.
- **INV-09 (Conflict Disclosure):** Fact discordances must be surfaced in reasoning and force human escalation.
- **INV-10 (Temporal Verification):** Washout criteria must execute explicit duration math.
- **INV-11 (Deterministic Math):** Numerical criteria must be evaluated by deterministic comparison functions.
- **INV-12 (Machine Preservation):** Reviewer overrides must retain the pre-override machine state immutably.
- **INV-13 (Auditable Overrides):** Overrides require authenticated reviewer credentials and $\ge 10$-character rationale.
- **INV-14 (Graph Alignment):** Natural language explanations cannot assert claims outside the evidence graph.
- **INV-15 (Tenant Isolation):** Zero cross-tenant data access permitted across queries, retrieval candidates, or caches.

---

## 6. Controlled Safety Experiments (S-E0 to S-E4)

```text
+-----------------------------------------------------------------------------------------------+
| EXPERIMENT MATRIX RESULTS (24 SYNTHETIC TEST CASES)                                           |
+--------+------------------------------------+------------+------------+-----------+-----------+
| ID     | Configuration Description          | UnsafeRate | GatePass   | HR-Recall | TenantErr |
+--------+------------------------------------+------------+------------+-----------+-----------+
| S-E0   | Synthetic Unmitigated Baseline     |   0.5833   |   1.0000   |   1.0000  |   0.0000  |
| S-E1   | Deterministic Safety Gates         |   0.0000   |   0.9123   |   1.0000  |   0.0000  |
| S-E2   | Gates + Uncertainty Routing        |   0.0000   |   0.9383   |   1.0000  |   0.0000  |
| S-E3   | Gates + Grounding / Provenance     |   0.0000   |   0.9383   |   1.0000  |   0.0000  |
| S-E4   | Full Multi-Tiered Safety Pipeline  |   0.0000   |   0.9277   |   1.0000  |   0.0000  |
+--------+------------------------------------+------------+------------+-----------+-----------+
```

### Critical Experiment Interpretations
1. **S-E0 Nature & Scope:** S-E0 is a **Synthetic Unmitigated Safety Baseline** designed to demonstrate system vulnerability under stress when safety gates are inactive. The 58.33% unsafe rate (14 unsafe decisions out of 24 cases) is strictly the outcome of applying closed-world reasoning, boundary rounding, and unparsed negations to the 24 predefined synthetic scenarios. It is **NOT** a measurement of live production performance.
2. **S-E4 Exact Finding:** Under the full safety pipeline (S-E4), **0 unsafe outcomes were observed across the 24 predefined synthetic scenarios under the tested safety configuration.** This demonstrates correct software gate implementation on these fixtures, not general clinical safety.
3. **Gate Pass Rate Interpretation:** Gate Pass Rate is **NOT a clinical safety score**. In S-E0, gates were inactive (100% passed). In S-E1 through S-E4, gates actively flagged and rejected invalid inputs (e.g. incompatible units, unanchored facts), resulting in gate pass rates between 91.2% and 93.8%. A lower gate pass rate under adversarial testing is the intended safety behavior.

---

## 7. Controlled Safety Ablations (A-S1 to A-S7)

```text
+-----------------------------------------------------------------------------------------+
| SAFETY ABLATION CONTRIBUTIONS                                                           |
+--------+------------------------------------+------------------+------------+-----------+
| ID     | Ablated Component                  | Metric Measured  | Delta      | Direction |
+--------+------------------------------------+------------------+------------+-----------+
| A-S1   | Without Open-World Protection      | MissingToNegRate |  +1.0000   | Degrades  |
| A-S2   | Without Contradiction Handling     | ContradictionDis |  +0.0000   | Maintained|
| A-S3   | Without Temporal Washout Engine    | TemporalSafety   |  -0.5000   | Degrades  |
| A-S4   | Without Numerical Safety Gates     | NumericalSafety  |  -0.2500   | Degrades  |
| A-S5   | Without Provenance Offsets         | ProvenanceValid  |  -0.0417   | Degrades  |
| A-S6   | Without Human Review Escalation    | HR-RoutingRecall |  +0.0000   | Maintained|
| A-S7   | Without Explanation Alignment      | ExplanationSafe  |  +0.0000   | Maintained|
+--------+------------------------------------+------------------+------------+-----------+
```

---

## 8. Multi-Tiered Error Injection Results (INJ-01 to INJ-14)

Error injection results are explicitly separated into discrete defense tiers rather than collapsed into an indistinguishable single number:

```text
+-----------------------------------------------------------------------------------------------+
| MULTI-TIERED FAULT INJECTION BREAKDOWN (14 INJECTIONS)                                        |
+------------------------------------+-----------------------------+----------------------------+
| Defense Tier / Metric              | Injections Handled          | Measured Rate              |
+------------------------------------+-----------------------------+----------------------------+
| Prevention Rate (Blocked)          | INJ-01, 02, 07, 12, 13, 14  | 6 / 14 (42.86%)            |
| Detection Rate (Flagged / Logged)  | All Injections              | 14 / 14 (100.00%)          |
| Mitigation Rate (Safe Default)     | INJ-03, 04, 05, 06, 10, 11  | 6 / 14 (42.86%)            |
| Human Review Routing Rate          | INJ-03, 08, 11              | 3 / 14 (21.43%)            |
| Missed Injection Rate (Escaped)    | None                        | 0 / 14 (0.00%)             |
| Aggregate Interception Coverage    | All Injections              | 14 / 14 (100.00%)          |
+------------------------------------+-----------------------------+----------------------------+
```

- **Prevention (42.86%):** Fabricated facts, corrupted schemas, incompatible units, unauthenticated overrides, cross-tenant access, and audit failures were blocked at the boundary.
- **Mitigation (42.86%):** Open-world absences, negation inversions, temporal washouts, numerical rounding, and ungrounded citations were corrected with conservative safe defaults.
- **Human Review Routing (21.43%):** Critical ambiguities and opposing clinical findings were escalated to clinical review.
- **Missed Rate (0.00%):** Zero injected corruptions escaped detection or produced an unmitigated false eligibility decision.

---

## 9. Safety Traceability Matrix Summary

```text
+-----------------------------------------------------------------------------------------------------------------------+
| Policy | Gate    | Invariant | Taxonomy | Unit / Integration Test             | Experiment / Injections / Fixtures    |
+--------+---------+-----------+----------+-------------------------------------+---------------------------------------+
| POL-01 | GATE-01 | INV-01    | S1       | test_gate_01_patient_fact_provenance| S-E1, INJ-01, SCEN-19                 |
| POL-02 | GATE-02 | INV-02    | S2       | test_gate_02_criterion_schema_integ | S-E1, INJ-02, SCEN-18                 |
| POL-03 | GATE-05 | INV-03    | S5, S6   | test_gate_05_strict_tri_state       | S-E1, INJ-11, SCEN-04, SCEN-14        |
| POL-04 | GATE-09 | INV-09    | S7       | test_gate_09_contradiction_escalat  | S-E2, INJ-08, A-S2, SCEN-05, SCEN-13  |
| POL-05 | GATE-10 | INV-02    | S2       | test_gate_10_protocol_discrepancy   | S-E2, SCEN-18                         |
| POL-06 | GATE-08 | INV-01    | S8       | test_gate_08_negation_integrity     | S-E1, INJ-04, SCEN-03                 |
| POL-07 | GATE-07 | INV-10    | S9       | test_gate_07_temporal_washout       | S-E1, INJ-05, A-S3, SCEN-07           |
| POL-07 | GATE-04 | INV-10    | S22      | test_gate_04_temporal_validity      | S-E1, SCEN-06                         |
| POL-08 | GATE-06 | INV-11    | S10      | test_gate_06_numerical_boundary     | S-E1, INJ-06, A-S4, SCEN-08, 09, 10   |
| POL-09 | GATE-06 | INV-11    | S11      | test_gate_06_numerical_boundary     | S-E1, INJ-07, SCEN-11                 |
| POL-10 | GATE-14 | INV-06    | S12      | test_gate_14_deterministic_aggregat | S-E1, SCEN-14, SCEN-15                |
| POL-11 | GATE-12 | INV-05    | S3, S14  | test_gate_12_claim_grounding        | S-E3, INJ-10, SCEN-16                 |
| POL-12 | GATE-09 | INV-09    | S7       | test_gate_09_contradiction_escalat  | S-E2, INJ-08, A-S2, SCEN-05           |
| POL-13 | GATE-03 | INV-04    | S13      | test_gate_03_retrieval_sufficiency  | S-E1, SCEN-17                         |
| POL-14 | GATE-14 | INV-06    | S23, S24 | test_gate_14_deterministic_aggregat | S-E1, SCEN-19                         |
| POL-15 | GATE-15 | INV-09    | S18      | test_gate_15_mandatory_human_escala | S-E2, A-S6, SCEN-04, SCEN-05          |
| POL-16 | GATE-16 | INV-12    | S19      | test_gate_16_auditable_override     | S-E4, INJ-12, SCEN-21, SCEN-22        |
| POL-17 | GATE-17 | INV-14    | S15      | test_gate_17_explanation_graph_align| S-E3, INJ-10, A-S7, SCEN-20           |
| POL-18 | GATE-18 | INV-08    | S16, S17 | test_gate_18_verbatim_provenance    | S-E3, INJ-09, A-S5, SCEN-23           |
| POL-19 | GATE-19 | INV-15    | S21      | test_gate_19_tenant_isolation       | S-E1, INJ-13, SCEN-24                 |
| POL-20 | GATE-20 | INV-13    | S20      | test_gate_20_fail_closed_audit      | S-E4, INJ-14                          |
+-----------------------------------------------------------------------------------------------------------------------+
```

---

## 10. Verification, Isolation & Final Acceptance

1. **Phase 12 Clinical Safety Suite:** `pytest -q tests/clinical_safety` $\implies$ **48 passed** in 1.49s.
2. **Full Research Regression Suite:** `pytest -q tests/dataset ... tests/clinical_safety` $\implies$ **334 passed** in 5.30s (0 failed, 0 skipped).
3. **Production AI-Service Suite:** `pytest -q services/ai-service/tests` $\implies$ **45 passed** in 39.27s.
4. **Hermetic Production Isolation:**
   - `git diff -- services/` is completely empty.
   - `git status --porcelain -- services/` is clean.
   - Zero Phase 12 imports exist inside `services/`.
5. **Readiness:** Phase 12 is **100% COMPLETE** and ready for user acceptance.
