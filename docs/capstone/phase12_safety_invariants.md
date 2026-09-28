# Phase 12 Machine-Checkable Safety Invariants (INV-01 to INV-15)

**Document ID:** SAFETY-INV-P12  
**Phase:** Phase 12 — Clinical Safety  
**Scope:** Formal Mathematical Definitions, Programmatic Predicates, and Verification Algorithms for Machine-Checkable Safety Invariants  
**Status:** DRAFT — RESEARCH SPECIFICATION ONLY  

---

## 1. Executive Summary & Verification Architecture

The Phase 12 Safety Invariants define fifteen machine-checkable constraints that guarantee conservative reasoning behavior throughout the MedMatch pipeline.

```text
+----------------------------------------------------------------------------------------------------+
|                                    INVARIANT ENFORCEMENT PIPELINE                                  |
+----------------------------------------------------------------------------------------------------+
|                                                                                                    |
|  [Input Stage]           --> INV-01 (No Fact Fab), INV-02 (No Crit Fab), INV-15 (Tenant Boundary)  |
|         │                                                                                          |
|         ▼                                                                                          |
|  [Reasoning Stage]       --> INV-04 (Open-World), INV-08 (Provenance), INV-10 (Temporal),          |
|                              INV-11 (Numerical Math)                                               |
|         │                                                                                          |
|         ▼                                                                                          |
|  [Aggregation Stage]     --> INV-03 (No UNK->PASS), INV-05 (Supported Criteria),                   |
|                              INV-06 (Supported Decisions), INV-07 (Traceability),                   |
|                              INV-09 (Conflict Disclosure)                                          |
|         │                                                                                          |
|         ▼                                                                                          |
|  [Output & Review Stage] --> INV-12 (Override Preservation), INV-13 (Auditable Overrides),          |
|                              INV-14 (Graph-Bounded Explanations)                                   |
|                                                                                                    |
+----------------------------------------------------------------------------------------------------+
```

Every invariant is formulated as a boolean predicate $\mathcal{P}(\cdot) \in \{\text{True}, \text{False}\}$.  
If $\mathcal{P} == \text{False}$, the invariant is **violated**, forcing the system into safe conservative fallback (raising a `SafetyInvariantViolation` or escalating the case to `NEEDS_REVIEW`).

---

## 2. Invariant Specifications (INV-01 to INV-15)

### INV-01: No Fabricated Patient Facts
- **Predicate:**
  $$\forall f \in \text{PatientFacts}, \quad \text{has\_provenance}(f, \text{RawNote}) \land (\text{text\_match}(f.\text{snippet}, \text{RawNote}) \lor f.\text{offset} == -1)$$
- **Logic:** Every patient clinical fact must resolve to a valid text snippet in the clinical note.
- **Enforcement Stage:** Post-fact extraction / Pre-reasoning.
- **Violation Action:** Abort evaluation; raise `SafetyInvariantViolation("INV-01: Fabricated patient fact detected")`.

### INV-02: No Fabricated Trial Criteria
- **Predicate:**
  $$\forall c \in \text{EvaluatedCriteria}, \quad c.\text{criterion\_id} \in \text{ProtocolCriteria}(\text{trial\_id})$$
- **Logic:** Evaluated criteria must belong strictly to the hydrated trial protocol.
- **Enforcement Stage:** Pre-reasoning / Prompt assembly.
- **Violation Action:** Reject criterion evaluation with `SafetyInvariantViolation("INV-02: Unknown criterion evaluated")`.

### INV-03: No UNKNOWN to PASS Conversion Without Evidence
- **Predicate:**
  $$\forall c \in \text{EvaluatedCriteria}, \quad (c.\text{status} == \text{UNKNOWN} \implies \text{TrialDecision} \ne \text{ELIGIBLE}) \land (c.\text{status} == \text{PASS} \implies \text{len}(c.\text{evidence}) > 0)$$
- **Logic:** A trial cannot be marked `ELIGIBLE` if any criterion is `UNKNOWN`. A criterion cannot be `PASS` without supporting evidence.
- **Enforcement Stage:** Aggregation stage.
- **Violation Action:** Force `TrialDecision = NEEDS_REVIEW`.

### INV-04: No Missing Information Treated as Negative Evidence
- **Predicate:**
  $$\forall c \in \text{EvaluatedCriteria}, \quad (\text{evidence\_count}(c) == 0 \implies c.\text{status} == \text{UNKNOWN})$$
- **Logic:** If the patient record has zero mention of a clinical entity, the criterion status must be `UNKNOWN`, never `FAIL` or `PASS`.
- **Enforcement Stage:** Criterion evaluation stage.
- **Violation Action:** Reset criterion status to `UNKNOWN`.

### INV-05: No Unsupported PASS / FAIL Criterion Decisions
- **Predicate:**
  $$\forall c \in \text{EvaluatedCriteria}, \quad c.\text{status} \in \{\text{PASS}, \text{FAIL}\} \implies \forall \text{cl} \in \text{claims}(c), \, \text{cl}.\text{support\_status} == \text{SUPPORTED}$$
- **Logic:** Every definitive criterion evaluation must have 100% verified supporting claims.
- **Enforcement Stage:** Post-reasoning / Validation.
- **Violation Action:** Downgrade criterion status to `UNKNOWN`.

### INV-06: No Unsupported Definitive Eligibility Decision
- **Predicate:**
  $$\text{TrialDecision} \in \{\text{ELIGIBLE}, \text{INELIGIBLE}\} \implies \text{unknown\_count} == 0 \lor (\text{TrialDecision} == \text{INELIGIBLE} \land \text{failed\_count} \ge 1)$$
- **Logic:** An `ELIGIBLE` decision requires 0 unknowns and 0 fails. An `INELIGIBLE` decision requires at least 1 verified fail.
- **Enforcement Stage:** Aggregation stage.
- **Violation Action:** Downgrade decision to `NEEDS_REVIEW`.

### INV-07: Every Definitive Criterion Decision Has Traceable Evidence
- **Predicate:**
  $$\forall c \in \text{EvaluatedCriteria}, \quad c.\text{status} \in \{\text{PASS}, \text{FAIL}\} \implies \text{len}(c.\text{patient\_fact\_references}) > 0 \lor \text{len}(c.\text{evidence\_citations}) > 0$$
- **Logic:** Definitive decisions must cite at least one explicit patient fact node or protocol citation.
- **Enforcement Stage:** Post-reasoning.
- **Violation Action:** Flag `TRACEABILITY_VIOLATION` and downgrade to `UNKNOWN`.

### INV-08: Every Evidence Item Has Valid Provenance
- **Predicate:**
  $$\forall e \in \text{EvidenceNodes}, \quad (e.\text{start\_offset} \ge 0 \land e.\text{end\_offset} > e.\text{start\_offset}) \lor (e.\text{start\_offset} == -1 \land \text{len}(e.\text{source\_field}) > 0)$$
- **Logic:** Evidence coordinates must be valid positive offsets or explicitly indicate unavailable span with field name.
- **Enforcement Stage:** Evidence graph construction.
- **Violation Action:** Reject evidence citation.

### INV-09: Conflicting Evidence Is Formally Disclosed
- **Predicate:**
  $$\text{has\_conflict}(c) \implies c.\text{status} == \text{UNKNOWN} \land \text{TrialDecision} == \text{NEEDS\_REVIEW} \land \text{len}(\text{contradictions}(c)) > 0$$
- **Logic:** Fact discordances cannot be silently resolved; they must be surfaced in reasoning and force review.
- **Enforcement Stage:** Reasoning & Aggregation.
- **Violation Action:** Force `ContradictionNode` synthesis and escalate to `P1_CRITICAL` review.

### INV-10: Temporal Constraints Are Not Silently Ignored
- **Predicate:**
  $$\forall c \in \text{TemporalCriteria}, \quad \text{has\_temporal\_validation}(c) == \text{True}$$
- **Logic:** Every criterion with a time or washout requirement must execute explicit temporal duration math.
- **Enforcement Stage:** Criterion evaluation.
- **Violation Action:** Downgrade criterion to `UNKNOWN` with `reasoning="Temporal washout unverified"`.

### INV-11: Numerical Thresholds Evaluated Deterministically
- **Predicate:**
  $$\forall c \in \text{NumericalCriteria}, \quad c.\text{status} == \text{eval\_math}(c.\text{comparator}, \text{patient\_value}, \text{threshold})$$
- **Logic:** Numerical boundaries must be calculated by deterministic code, not LLM string generation.
- **Enforcement Stage:** Criterion evaluation.
- **Violation Action:** Overwrite LLM evaluation with deterministic comparator result.

### INV-12: Human Overrides Preserve Machine Output
- **Predicate:**
  $$\forall o \in \text{Overrides}, \quad o.\text{original\_machine\_status} == \text{MachineStatus} \land o.\text{original\_machine\_status} \ne \text{None}$$
- **Logic:** Overrides must retain the pre-override machine state immutably.
- **Enforcement Stage:** Human review resolution.
- **Violation Action:** Reject override submission.

### INV-13: Human Overrides Are Auditable
- **Predicate:**
  $$\forall o \in \text{Overrides}, \quad \text{len}(o.\text{reviewer\_id}) > 0 \land \text{len}(o.\text{rationale}) \ge 10 \land \text{has\_timestamp}(o)$$
- **Logic:** Overrides must possess authenticated reviewer identity, timestamp, and minimum 10-character clinical rationale.
- **Enforcement Stage:** Review submission validation.
- **Violation Action:** Reject override with validation error.

### INV-14: Explanations Cannot Exceed the Evidence Graph
- **Predicate:**
  $$\forall \text{claim} \in \text{ExplanationClaims}, \quad \exists n \in \text{EvidenceGraph}.\text{nodes} \text{ s.t. } \text{supports}(n, \text{claim})$$
- **Logic:** Natural language explanations cannot contain claims outside the underlying evidence graph.
- **Enforcement Stage:** Post-explanation generation.
- **Violation Action:** Reject explanation; fall back to structured tabular summary.

### INV-15: Tenant Boundaries Are Preserved
- **Predicate:**
  $$\forall r \in \text{RetrievedItems}, \quad r.\text{hospital\_id} == \text{CurrentUser}.\text{hospital\_id}$$
- **Logic:** Zero cross-tenant data access permitted across queries, retrieval candidates, or cached entries.
- **Enforcement Stage:** Pre-retrieval, Post-retrieval, Pre-cache.
- **Violation Action:** Abort request immediately; raise `TenantIsolationViolationError`.

---

## 3. Summary Invariant Verification Matrix

```text
+--------+-------------------------------------+-----------------------+---------------------+-------------------+
| ID     | Invariant Name                      | Enforcement Stage     | Primary Gate        | Test Scenario     |
+--------+-------------------------------------+-----------------------+---------------------+-------------------+
| INV-01 | No Fabricated Patient Facts         | Post-Extraction       | GATE-01 (Provenance)| SCEN-19           |
| INV-02 | No Fabricated Trial Criteria        | Pre-Reasoning         | GATE-02 (Schema)    | SCEN-18           |
| INV-03 | No UNKNOWN -> PASS Conversion       | Aggregation           | GATE-05 (Tri-State) | SCEN-01, SCEN-14  |
| INV-04 | No Missing -> Negative Conversion   | Evaluation            | GATE-11 (Open-World)| SCEN-01, SCEN-12  |
| INV-05 | No Unsupported Criteria Decisions   | Post-Reasoning        | GATE-12 (Grounding) | SCEN-16           |
| INV-06 | No Unsupported Definitive Decisions | Aggregation           | GATE-14 (Aggregator)| SCEN-19           |
| INV-07 | Traceable Evidence Mandate          | Post-Reasoning        | GATE-12 (Grounding) | SCEN-23           |
| INV-08 | Valid Provenance Offsets            | Graph Construction    | GATE-18 (Offset)    | SCEN-23           |
| INV-09 | Conflict Disclosure Mandate         | Reasoning/Aggregation | GATE-09 (Conflict)  | SCEN-05, SCEN-13  |
| INV-10 | Temporal Constraint Verification    | Evaluation            | GATE-07 (Washout)   | SCEN-07           |
| INV-11 | Deterministic Numerical Math        | Evaluation            | GATE-06 (Numerical) | SCEN-08 to SCEN-11|
| INV-12 | Machine Output Preservation         | Review Resolution     | GATE-16 (Override)  | SCEN-21           |
| INV-13 | Auditable Overrides Mandate         | Review Resolution     | GATE-16 (Override)  | SCEN-22           |
| INV-14 | Graph-Bounded Explanations          | Post-Explanation      | GATE-17 (Alignment) | SCEN-20           |
| INV-15 | Tenant Boundary Preservation        | Pre/Post-Retrieval    | GATE-19 (Tenant)    | SCEN-24           |
+--------+-------------------------------------+-----------------------+---------------------+-------------------+
```
