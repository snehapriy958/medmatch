# Phase 12 Safety Experiment & Ablation Specification

**Document ID:** SAFETY-EXP-P12  
**Phase:** Phase 12 — Clinical Safety  
**Scope:** Experimental Matrix (S-E0 to S-E4) and Controlled Safety Ablations (A-S1 to A-S7)  
**Status:** DRAFT — RESEARCH SPECIFICATION ONLY  

---

## 1. Executive Summary & Experimental Objectives

The Phase 12 Safety Experiments measure the empirical efficacy of safety gates, conservative reasoning rules, and review routing under adverse, edge-case, and ambiguous clinical conditions.

> [!NOTE]
> **DEVELOPMENT FIXTURE EVALUATION ONLY:**  
> All experiments run against the synthetic 24-scenario clinical safety suite (`data/fixtures/phase12/safety_scenarios.json`).  
> Results demonstrate system verification against formal invariants, NOT clinical performance on human patients.

---

## 2. Controlled Safety Experiment Matrix (S-E0 to S-E4)

```text
+-------------------------------------------------------------------------------------------------------------------------------+
|                                            SAFETY EXPERIMENT MATRIX (S-E0 to S-E4)                                            |
+------+-----------------------------+-----------------------+---------------------+-------------------+------------------------+
| ID   | Experiment Name             | Input Representation  | Safety Gates        | Uncertainty / HR  | Provenance / Expl      |
+------+-----------------------------+-----------------------+---------------------+-------------------+------------------------+
| S-E0 | Baseline Safety Behavior    | Raw Clinical Note     | DISABLED            | DISABLED          | Unchecked Free Text    |
| S-E1 | Deterministic Safety Gates  | PatientClinicalProfile| ENABLED (G1–G11)    | DISABLED          | Basic Offsets          |
| S-E2 | Gates + Uncertainty Routing | PatientClinicalProfile| ENABLED (G1–G11)    | ENABLED (GATE-15) | Basic Offsets          |
| S-E3 | Gates + Grounding Enforced  | PatientClinicalProfile| ENABLED (G1–G12)    | ENABLED (GATE-15) | Strict Graph Grounding |
| S-E4 | Full Safety Pipeline + HR   | PatientClinicalProfile| ENABLED (ALL GATES) | ENABLED + Override| Graph + Fail-Closed Log|
+------+-----------------------------+-----------------------+---------------------+-------------------+------------------------+
```

### S-E0: Baseline Safety Behavior (Unmitigated Baseline)
- **Objective:** Evaluate how the baseline prompt matching pipeline behaves on challenging safety edge cases without safety gates.
- **Configuration:** Raw clinical note; unparsed prompt reasoning; zero deterministic safety gates; zero uncertainty escalation; closed-world bias unmitigated.
- **Expected Failure Modes:** High UNKNOWN-to-PASS violation rate (S5), numerical boundary errors (S10), temporal washout bypass (S9), and missing information treated as negative (S4).

### S-E1: Deterministic Safety Gates Enabled
- **Objective:** Measure the impact of enforcing Layer 2–5 deterministic safety gates (numerical math, temporal duration, tri-state invariants, open-world default).
- **Configuration:** `PatientClinicalProfile`; GATE-01 through GATE-11 active; deterministic mathematical comparators.
- **Expected Impact:** Complete elimination of numerical boundary errors (S10) and temporal washout violations (S9); open-world missing information preserved as `UNKNOWN`.

### S-E2: Safety Gates + Uncertainty Review Routing
- **Objective:** Evaluate conservative escalation of ambiguous, borderline, and missing information cases to human review.
- **Configuration:** S-E1 plus active `HumanReviewPolicy` (GATE-15); priority calculation (P1–P4); automatic queue placement for `unknown_count > 0`.
- **Expected Impact:** Human Review Routing Recall (HRRR) reaches 100%; unresolved uncertainty cases eliminated.

### S-E3: Safety Gates + Grounding & Provenance Enforcement
- **Objective:** Measure suppression of ungrounded inferences, hallucinated rationale, and citation offset drift.
- **Configuration:** S-E2 plus strict claim grounding verification (GATE-12) and verbatim provenance enforcement (GATE-18).
- **Expected Impact:** Provenance validity rate reaches 100%; unsupported claim rate drops to 0.0.

### S-E4: Full Safety Pipeline + Human Review Simulation
- **Objective:** End-to-end evaluation of the complete safety architecture including auditable reviewer overrides and fail-closed audit logging.
- **Configuration:** S-E3 plus immutable override preservation (GATE-16) and fail-closed transaction logging (GATE-20).
- **Expected Impact:** Unsafe Decision Rate strictly equals 0.0000 across all 24 safety scenarios.

---

## 3. Controlled Safety Ablations (A-S1 to A-S7)

```text
+-------------------------------------------------------------------------------------------------------------------------+
|                                              SAFETY ABLATION SUITE (A-S1 to A-S7)                                       |
+------+------------------------------------------+---------------+---------------+---------------------------------------+
| ID   | Ablation Name                            | Baseline (A)  | Treatment (B) | Primary Delta Measured                |
+------+------------------------------------------+---------------+---------------+---------------------------------------+
| A-S1 | Missing-Information Protection           | S-E0 (None)   | S-E1 (G11)    | Delta Missing-to-Negative Violations  |
| A-S2 | Contradiction Escalation                 | S-E1 (Silent) | S-E2 (G09)    | Delta Contradiction Disclosure Rate   |
| A-S3 | Temporal Washout Validation              | S-E0 (None)   | S-E1 (G07)    | Delta Temporal Safety Rate (TSR)      |
| A-S4 | Numerical Boundary Gate                  | S-E0 (Prompt) | S-E1 (G06)    | Delta Numerical Safety Rate (NSR)     |
| A-S5 | Provenance & Citation Enforcement        | S-E2 (Loose)  | S-E3 (G18)    | Delta Provenance Validity Rate (PVR)  |
| A-S6 | Human-Review Routing                     | S-E1 (No HR)  | S-E2 (HR)     | Delta Human Review Routing Recall     |
| A-S7 | Explanation Graph Alignment              | S-E3 (Loose)  | S-E4 (G17)    | Delta Explanation Safety Rate (ESR)   |
+------+------------------------------------------+---------------+---------------+---------------------------------------+
```

### A-S1: Missing-Information Protection
- **Hypothesis:** Enforcing GATE-11 (Open-World Completeness) eliminates false-negative assumptions on unmentioned comorbidities.
- **Comparison:** S-E0 vs S-E1 on Scenarios `SCEN-01` and `SCEN-12`.

### A-S2: Contradiction Escalation
- **Hypothesis:** Enforcing GATE-09 intercepts discordant test modalities and forces `NEEDS_REVIEW` instead of arbitrary tie-breaking.
- **Comparison:** S-E1 (unmitigated conflict) vs S-E2 (escalated conflict) on Scenarios `SCEN-05` and `SCEN-13`.

### A-S3: Temporal Washout Validation
- **Hypothesis:** Enforcing GATE-07 with explicit day subtraction prevents toxic patient enrollment during active drug washout windows.
- **Comparison:** S-E0 (unstructured text) vs S-E1 (deterministic washout) on Scenario `SCEN-07`.

### A-S4: Numerical Boundary Gate
- **Hypothesis:** Replacing generative LLM inequality reasoning with deterministic Python comparator eliminates boundary inversion errors.
- **Comparison:** S-E0 (generative text) vs S-E1 (deterministic math) on Scenarios `SCEN-08` through `SCEN-11`.

### A-S5: Provenance & Citation Enforcement
- **Hypothesis:** Enforcing GATE-18 eliminates fabricated and drifted character citations.
- **Comparison:** S-E2 vs S-E3 on Scenario `SCEN-23`.

### A-S6: Human-Review Routing
- **Hypothesis:** Enforcing GATE-15 guarantees that 100% of ambiguous, borderline, or conflicting cases are escalated to clinical review.
- **Comparison:** S-E1 vs S-E2 across all 24 safety scenarios.

### A-S7: Explanation Graph Alignment
- **Hypothesis:** Enforcing GATE-17 suppresses ungrounded narrative claims from patient-facing explanations.
- **Comparison:** S-E3 vs S-E4 on Scenario `SCEN-20`.
