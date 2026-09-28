# Phase 12 Clinical Safety Model & Deterministic Safety Gates

**Document ID:** SAFETY-MODEL-P12  
**Phase:** Phase 12 — Clinical Safety  
**Scope:** Multi-Layered Safety Architecture, Interception Points, Deterministic Safety Gates (GATE-01 to GATE-20), and Safety Traceability Matrix  
**Status:** DRAFT — RESEARCH SPECIFICATION ONLY  

---

## 1. Executive Summary & Architecture

The MedMatch Clinical Safety Model organizes system defenses into a seven-layer hierarchy. Each layer acts as an independent barrier against the propagation of clinical reasoning errors.

```text
+----------------------------------------------------------------------------------------------------+
|                                MEDMATCH SEVEN-LAYER SAFETY ARCHITECTURE                            |
+----------------------------------------------------------------------------------------------------+
|                                                                                                    |
|  LAYER 1: Input & Tenant Boundary Validation                                                       |
|    - Validates user JWT hospital_id matches requested hospital.                                    |
|    - Enforces strict tenant separation on queries, candidate retrieval, and cache keys.            |
|    - Gates: GATE-19 (Tenant Boundary Enforcement Gate)                                             |
|                                                                                                    |
|  LAYER 2: Document & Fact Extraction Integrity                                                      |
|    - Asserts provenance character spans for patient facts and protocol criteria.                  |
|    - Normalizes assertion polarity (PRESENT, ABSENT, UNKNOWN).                                     |
|    - Gates: GATE-01 (Fact Provenance), GATE-02 (Criterion Schema), GATE-08 (Negation Integrity),    |
|             GATE-10 (Protocol Discrepancy Gate)                                                    |
|                                                                                                    |
|  LAYER 3: Retrieval Sufficiency & Evidence Boundary                                                |
|    - Validates candidate trial retrieval completeness.                                             |
|    - Returns INSUFFICIENT_RETRIEVAL_DATA if zero criteria match; bypasses LLM reasoning.           |
|    - Gates: GATE-03 (Retrieval Sufficiency Gate)                                                   |
|                                                                                                    |
|  LAYER 4: Deterministic Criterion Evaluation Gates                                                 |
|    - Evaluates numerical inequalities via deterministic code.                                      |
|    - Enforces criterion-dependent temporal validity and washout calculations.                      |
|    - Detects conflicting evidence and maps to UNKNOWN.                                             |
|    - Gates: GATE-04 (Temporal Evidence Validity), GATE-06 (Numerical Math & Unit Safety),          |
|             GATE-07 (Washout), GATE-09 (Conflict Escalation), GATE-11 (Open-World Completeness)     |
|                                                                                                    |
|  LAYER 5: Deterministic Aggregation & Tri-State Gating                                             |
|    - Aggregates criteria states strictly (1 FAIL -> INELIGIBLE, 1 UNKNOWN -> NEEDS_REVIEW).        |
|    - Prohibits UNKNOWN -> PASS conversion.                                                         |
|    - Gates: GATE-05 (Tri-State Invariant), GATE-14 (Deterministic Aggregation Gate)                |
|                                                                                                    |
|  LAYER 6: Uncertainty & Human Review Routing                                                       |
|    - Evaluates uncertainty dimensions and calculates priority (P1 to P4).                          |
|    - Enforces auditable human reviewer overrides with immutable machine states.                    |
|    - Gates: GATE-15 (Review Escalation), GATE-16 (Auditable Override Gate)                         |
|                                                                                                    |
|  LAYER 7: Explanation & Evidence Graph Alignment                                                   |
|    - Verifies natural language claims against underlying graph nodes.                              |
|    - Writes fail-closed persistent audit log.                                                      |
|    - Gates: GATE-12 (Claim Grounding), GATE-17 (Graph Alignment), GATE-18 (Verbatim Provenance),    |
|             GATE-20 (Fail-Closed Audit Gate)                                                       |
|                                                                                                    |
+----------------------------------------------------------------------------------------------------+
```

> [!WARNING]
> **GATE PASS RATE INTERPRETATION NOTICE**  
> Gate Pass Rate is **NOT** an overall clinical safety score.  
> Gate Pass Rate measures the proportion of fact/criterion assertions that satisfied all validity conditions without triggering a gate violation. When evaluated on adversarial or boundary test suites, safety gates **must fail** when encountering corruptions, stale facts, or incompatible units in order to prevent an unsafe decision downstream. Lower gate pass rates under stress indicate active interception of non-compliant inputs.

---

## 2. Deterministic Safety Gate Specifications (GATE-01 to GATE-20)

### GATE-01: Patient Fact Provenance Gate
- **Layer:** Layer 2 (Extraction Integrity).
- **Trigger:** Any clinical fact node presented for eligibility reasoning.
- **Verification Rule:** The fact must possess verified character offsets $[start, end]$ matching the verbatim source note substring, or explicitly designate unanchored status with $start == -1$.
- **Action on Failure:** Reject fact node; emit `Taxonomy: S1 (Fabricated Fact)`.

### GATE-02: Criterion Schema Integrity Gate
- **Layer:** Layer 2 (Extraction Integrity).
- **Trigger:** Protocol criterion hydrated from database or document extractor.
- **Verification Rule:** Criterion must have a non-empty `criterion_id`, valid `trial_id`, and explicit `criteria_type` (`INCLUSION` or `EXCLUSION`). Compound boolean operators (AND/OR) must be valid AST nodes.
- **Action on Failure:** Halt evaluation of that protocol; emit `Taxonomy: S2 (Fabricated/Corrupt Criterion)`.

### GATE-03: Retrieval Sufficiency Gate
- **Layer:** Layer 3 (Retrieval Boundary).
- **Trigger:** Candidate retrieval query execution.
- **Verification Rule:** If retrieved criteria list is empty, the system MUST return `INSUFFICIENT_RETRIEVAL_DATA` and skip LLM reasoning entirely.
- **Action on Failure:** Abort matching; prevent false `POSSIBLY_ELIGIBLE` emission (fixing production risk `R-RET-01`).

### GATE-04: Temporal Evidence Validity Gate
- **Layer:** Layer 4 (Criterion Evaluation).
- **Trigger:** Clinical observation or laboratory fact evaluated against a protocol requirement.
- **Verification Rule:** Temporal validity is **criterion-dependent**. If a protocol specifies a validity window (e.g., labs within 14 days), that threshold is enforced. If unstated, a 90-day threshold is used strictly as a synthetic research fixture parameter. Uninterpretable temporal semantics strictly default to `UNKNOWN`.
- **Action on Failure:** Downgrade fact to `AssertionType.UNKNOWN`; emit `Taxonomy: S22 (Stale Info Used)`.

### GATE-05: Strict Tri-State Evidence Gate
- **Layer:** Layer 5 (Deterministic Aggregation).
- **Trigger:** Any criterion evaluating to `PASS` or `FAIL`.
- **Verification Rule:** Criterion cannot be marked `PASS` or `FAIL` unless the supporting evidence array is non-empty ($\text{len}(\text{evidence}) > 0$). An empty evidence array MUST result in `CriterionEvaluationStatus.UNKNOWN`.
- **Action on Failure:** Overwrite status to `UNKNOWN`; emit `Taxonomy: S5 / S6`.

### GATE-06: Deterministic Numerical Boundary Gate
- **Layer:** Layer 4 (Criterion Evaluation).
- **Trigger:** Quantitative laboratory or physiological threshold criterion.
- **Verification Rule:** Numerical inequalities must be computed deterministically in Python using verified units. Supported unit pairs (creatinine $\mu\text{mol/L} \leftrightarrow \text{mg/dL}$, platelets $10^9/\text{L} \leftrightarrow \text{K}/\mu\text{L}$) are converted; unsupported units strictly fail closed to `UNKNOWN`.
  $$x \ge T \implies \text{evaluates True strictly if } x \ge T$$
- **Action on Failure:** Correct LLM evaluation with deterministic mathematical result; emit `Taxonomy: S10 / S11`.

### GATE-07: Conservative Temporal Washout Gate
- **Layer:** Layer 4 (Criterion Evaluation).
- **Trigger:** Prior treatment criterion with mandatory washout window.
- **Verification Rule:** If elapsed duration is ambiguous or strictly less than protocol washout days ($\Delta t < T_{\text{washout}}$), the criterion must evaluate to `FAIL` (exclusion satisfied $\implies$ patient excluded) or `UNKNOWN`.
- **Action on Failure:** Force ineligibility or review escalation; emit `Taxonomy: S9 (Temporal Error)`.

### GATE-08: Negation Integrity Gate
- **Layer:** Layer 2 (Extraction Integrity).
- **Trigger:** Clinical narrative finding containing negation cues.
- **Verification Rule:** Negated findings must map strictly to `AssertionType.ABSENT`. An absence of a finding in an exclusion criterion must evaluate to `PASS` (exclusion not triggered).
- **Action on Failure:** Re-assert `ABSENT` status; emit `Taxonomy: S8 (Negation Error)`.

### GATE-09: Contradiction Escalation Gate
- **Layer:** Layer 4 (Criterion Evaluation).
- **Trigger:** Multiple clinical facts with opposing assertions for the same medical concept.
- **Verification Rule:** Opposing assertions cannot be resolved by majority vote or first-parsed heuristic. Criterion must evaluate to `UNKNOWN` and synthesize a `ContradictionNode`.
- **Action on Failure:** Escalate case to `ReviewPriority.P1_CRITICAL`; emit `Taxonomy: S7 (Conflict Ignored)`.

### GATE-10: Protocol Discrepancy Gate
- **Layer:** Layer 2 (Extraction Integrity).
- **Trigger:** Discrepant criteria text between trial registry synopsis and protocol body.
- **Verification Rule:** Apply the strict conservative subset and flag the discrepancy for clinical coordinator audit.
- **Action on Failure:** Emit discrepancy alert; route trial to `NEEDS_REVIEW`; emit `Taxonomy: S2`.

### GATE-11: Open-World Completeness Gate
- **Layer:** Layer 4 (Criterion Evaluation).
- **Trigger:** Unmentioned clinical entities in patient record.
- **Verification Rule:** Absence of mention must evaluate to `UNKNOWN`. Closed-world assumptions (absence = negative) are strictly prohibited.
- **Action on Failure:** Overwrite status to `UNKNOWN`; emit `Taxonomy: S4 (Missing Info as Negative)`.

### GATE-12: Claim Grounding Verification Gate
- **Layer:** Layer 7 (Explanation & Graph Alignment).
- **Trigger:** Natural language explanatory sentences or reasoning claims.
- **Verification Rule:** Every sentence must resolve to at least one verified `FactNode` or `CriterionNode` with support status `SUPPORTED`.
- **Action on Failure:** Strip unsupported claims; emit `Taxonomy: S3 / S14 (Ungrounded Claim)`.

### GATE-14: Deterministic Aggregation Gate
- **Layer:** Layer 5 (Deterministic Aggregation).
- **Trigger:** Roll-up of criterion evaluation states to trial eligibility.
- **Verification Rule:** If $\ge 1$ FAIL $\implies$ INELIGIBLE. If 0 FAIL and $\ge 1$ UNKNOWN $\implies$ NEEDS_REVIEW. If all criteria PASS $\implies$ ELIGIBLE.
- **Action on Failure:** Force conservative status; emit `Taxonomy: S14`.

### GATE-15: Mandatory Human Escalation Gate
- **Layer:** Layer 6 (Uncertainty & Review).
- **Trigger:** Any evaluation containing unresolved UNKNOWN criteria or conflicts.
- **Verification Rule:** Evaluates uncertainty dimensions and places case into clinical review queue.
- **Action on Failure:** Force queue entry; emit `Taxonomy: S18`.

### GATE-16: Auditable Override Gate
- **Layer:** Layer 6 (Uncertainty & Review).
- **Trigger:** Clinician submits an override to an automated machine decision.
- **Verification Rule:** Machine state must be preserved immutably; override requires reviewer ID, timestamp, and clinical rationale $\ge 10$ characters.
- **Action on Failure:** Reject override submission; emit `Taxonomy: S19`.

### GATE-17: Explanation Graph Alignment Gate
- **Layer:** Layer 7 (Explanation Alignment).
- **Trigger:** Natural language summary generated for patient or clinician.
- **Verification Rule:** Explanation claims cannot introduce entities not present in underlying evidence graph.
- **Action on Failure:** Suppress natural language; fall back to tabular summary; emit `Taxonomy: S15`.

### GATE-18: Verbatim Provenance Gate
- **Layer:** Layer 7 (Provenance).
- **Trigger:** Document citation with character offsets $[start, end]$.
- **Verification Rule:** Sliced source text must match verbatim snippet string.
- **Action on Failure:** Reset offset to $-1$; emit `Taxonomy: S16`.

### GATE-19: Tenant Boundary Enforcement Gate
- **Layer:** Layer 1 (Tenant Boundary).
- **Trigger:** Incoming matching request, candidate retrieval, or cached trial access.
- **Verification Rule:** `user.hospital_id == request.hospital_id == candidate.hospital_id`.
- **Action on Failure:** Abort transaction immediately with `TenantIsolationViolationError`; emit `Taxonomy: S21`.

### GATE-20: Fail-Closed Audit Gate
- **Layer:** Layer 7 (Audit).
- **Trigger:** Clinical decision event persistence to audit trail.
- **Verification Rule:** If audit log persistence fails, transaction must abort immediately.
- **Action on Failure:** Roll back decision; emit `Taxonomy: S20`.

---

## 3. Canonical Safety Traceability Matrix

Every implemented policy, gate, invariant, taxonomy code, test, and experiment maps to a verified lifecycle path with **zero orphaned components**:

```text
+--------------------------------------------------------------------------------------------------------------------------------+
| CANONICAL SAFETY TRACEABILITY MATRIX                                                                                           |
+--------+---------+--------+----------+-------------------------------------+---------------------------------------------------+
| Policy | Gate    | Invar. | Taxonomy | Unit / Integration Test             | Experiment / Fault Injection / Fixture            |
+--------+---------+--------+----------+-------------------------------------+---------------------------------------------------+
| POL-01 | GATE-01 | INV-01 | S1       | test_gate_01_patient_fact_provenance| S-E1, INJ-01, SCEN-19                             |
| POL-02 | GATE-02 | INV-02 | S2       | test_gate_02_criterion_schema_integ | S-E1, INJ-02, SCEN-18                             |
| POL-03 | GATE-05 | INV-03 | S5, S6   | test_gate_05_strict_tri_state       | S-E1, INJ-11, SCEN-04, SCEN-14                    |
| POL-04 | GATE-09 | INV-09 | S7       | test_gate_09_contradiction_escalat  | S-E2, INJ-08, A-S2, SCEN-05, SCEN-13              |
| POL-05 | GATE-10 | INV-02 | S2       | test_gate_10_protocol_discrepancy   | S-E2, SCEN-18                                     |
| POL-06 | GATE-08 | INV-01 | S8       | test_gate_08_negation_integrity     | S-E1, INJ-04, SCEN-03                             |
| POL-07 | GATE-07 | INV-10 | S9       | test_gate_07_temporal_washout       | S-E1, INJ-05, A-S3, SCEN-07                       |
| POL-07 | GATE-04 | INV-10 | S22      | test_gate_04_temporal_validity      | S-E1, SCEN-06                                     |
| POL-08 | GATE-06 | INV-11 | S10      | test_gate_06_numerical_boundary     | S-E1, INJ-06, A-S4, SCEN-08, SCEN-09, SCEN-10     |
| POL-09 | GATE-06 | INV-11 | S11      | test_gate_06_numerical_boundary     | S-E1, INJ-07, SCEN-11                             |
| POL-10 | GATE-14 | INV-06 | S12      | test_gate_14_deterministic_aggregat | S-E1, SCEN-14, SCEN-15                            |
| POL-11 | GATE-12 | INV-05 | S3, S14  | test_gate_12_claim_grounding        | S-E3, INJ-10, SCEN-16                             |
| POL-12 | GATE-09 | INV-09 | S7       | test_gate_09_contradiction_escalat  | S-E2, INJ-08, A-S2, SCEN-05                       |
| POL-13 | GATE-03 | INV-04 | S13      | test_gate_03_retrieval_sufficiency  | S-E1, SCEN-17                                     |
| POL-14 | GATE-14 | INV-06 | S23, S24 | test_gate_14_deterministic_aggregat | S-E1, SCEN-19                                     |
| POL-15 | GATE-15 | INV-09 | S18      | test_gate_15_mandatory_human_escala | S-E2, A-S6, SCEN-04, SCEN-05                     |
| POL-16 | GATE-16 | INV-12 | S19      | test_gate_16_auditable_override     | S-E4, INJ-12, SCEN-21, SCEN-22                    |
| POL-17 | GATE-17 | INV-14 | S15      | test_gate_17_explanation_graph_align| S-E3, INJ-10, A-S7, SCEN-20                       |
| POL-18 | GATE-18 | INV-08 | S16, S17 | test_gate_18_verbatim_provenance    | S-E3, INJ-09, A-S5, SCEN-23                       |
| POL-19 | GATE-19 | INV-15 | S21      | test_gate_19_tenant_isolation       | S-E1, INJ-13, SCEN-24                             |
| POL-20 | GATE-20 | INV-13 | S20      | test_gate_20_fail_closed_audit      | S-E4, INJ-14                                      |
+--------+---------+--------+----------+-------------------------------------+---------------------------------------------------+
```
