# Phase 12 Deterministic Error-Injection Specification

**Document ID:** SAFETY-INJ-P12  
**Phase:** Phase 12 — Clinical Safety  
**Scope:** Deterministic Fault Injection, Defense Tiers (Detection, Prevention, Mitigation, Human Review), and Test Specifications  
**Status:** DRAFT — RESEARCH SPECIFICATION ONLY  

---

## 1. Executive Summary & Defense Tiers

To prove that the safety architecture does not merely passively observe safe inputs, Phase 12 introduces a systematic, deterministic **Error-Injection Framework**.

The framework injects deliberate synthetic corruptions across inputs, intermediate reasoning states, and reviewer decisions, verifying system defense across four distinct tiers:
1. **PREVENTION (Interception):** The gate intercepts the invalid state and rejects the transaction before calculation can proceed (e.g., rejecting an override missing a rationale).
2. **DETECTION (Identification):** The system flags and categorizes the anomaly using the S1–S24 taxonomy (e.g., flagging ungrounded claims in explanation text).
3. **MITIGATION (Safe Conservative Correction):** The system automatically overwrites the corrupt state with a safe conservative default (e.g., converting an ungrounded `PASS` into `UNKNOWN`).
4. **HUMAN REVIEW (Escalation):** The system packages the anomaly into a priority incident and routes it to clinical oversight (e.g., routing conflicting biopsy records to `P1_CRITICAL` review).

---

## 2. Deterministic Error-Injection Matrix

```text
+-------------------------------------------------------------------------------------------------------------------------------+
|                                            DETERMINISTIC ERROR-INJECTION MATRIX                                               |
+----------+-----------------------------+-------------------------------+-----------------------+---------------------+--------+
| InjectID | Corruption Type             | Injected Fault Description    | Target Gate           | Defense Tier        | Taxon  |
+----------+-----------------------------+-------------------------------+-----------------------+---------------------+--------+
| INJ-01   | Fabricated Patient Fact     | Insert phantom HER2+ fact     | GATE-01 (Provenance)  | PREVENTION          | S1     |
| INJ-02   | Fabricated Trial Criterion  | Add non-existent age limit    | GATE-02 (Schema)      | PREVENTION          | S2     |
| INJ-03   | Evidence Removal            | Delete brain MRI normal scan  | GATE-11 (Open-World)  | MITIGATION (-> UNK) | S4     |
| INJ-04   | Negation Inversion          | Flip "denies dyspnea" to POS  | GATE-08 (Negation)    | DETECTION/MITIGATE  | S8     |
| INJ-05   | Temporal Date Shift         | Shift chemo end to 10d ago    | GATE-07 (Washout)     | MITIGATION (-> FAIL)| S9     |
| INJ-06   | Numerical Threshold Alter   | Alter platelet lab to 99k     | GATE-06 (Numerical)   | MITIGATION (-> FAIL)| S10    |
| INJ-07   | Measurement Unit Alteration | Alter creatinine unit to umol | GATE-06 (Numerical)   | PREVENTION/MITIGATE | S11    |
| INJ-08   | Contradictory Evidence      | Inject discordant cfDNA test  | GATE-09 (Conflict)    | HUMAN REVIEW (P1)   | S7     |
| INJ-09   | Provenance Offset Deletion  | Corrupt character offsets     | GATE-18 (Offset)      | DETECTION/PREVENT   | S16    |
| INJ-10   | Spurious Citation Injection | Link unrelated text passage   | GATE-12 (Grounding)   | MITIGATION (Strip)  | S17    |
| INJ-11   | Forced UNKNOWN -> PASS      | Forcibly flip UNK to PASS     | GATE-05 (Tri-State)   | PREVENTION/OVERWRITE| S5     |
| INJ-12   | Blank Reviewer Override     | Submit override with no text  | GATE-16 (Override)    | PREVENTION (Reject) | S19    |
| INJ-13   | Cross-Tenant Injection      | Inject Hospital B data in A   | GATE-19 (Tenant)      | PREVENTION (Abort)  | S21    |
| INJ-14   | Audit Failure Simulation    | Trigger database write fault  | GATE-20 (Audit)       | PREVENTION (Fail-Cl)| S20    |
+----------+-----------------------------+-------------------------------+-----------------------+---------------------+--------+
```

---

## 3. Detailed Fault Injection Behaviors

### INJ-01: Fabricated Patient Fact Injection
- **Injection:** A synthetic clinical fact node `HER2_AMPLIFIED` is injected into `PatientClinicalProfile` without character offsets in the patient note.
- **Expected Defense:** `GATE-01` intercepts the node during ingestion; rejects the fact node; raises `FactProvenanceError`.
- **Classification:** `PREVENTION` (S1).

### INJ-03: Evidence Removal (Missing Information Test)
- **Injection:** The normal brain MRI finding is removed from `SYN_P001`'s record, leaving central nervous system status unmentioned.
- **Expected Defense:** `GATE-11` detects zero evidence for exclusion criterion `NCT02484404_EXC_02`; prevents closed-world assumption; sets criterion status to `UNKNOWN`; trial status changes from `ELIGIBLE` to `NEEDS_REVIEW`.
- **Classification:** `MITIGATION` (S4).

### INJ-05: Temporal Date Shift (Washout Violation Test)
- **Injection:** The completion timestamp of carboplatin/paclitaxel is shifted from 45 days ago to 20 days ago (violating the 28-day washout).
- **Expected Defense:** `GATE-07` computes $\Delta t = 20 < 28$; marks exclusion criterion `NCT02484404_EXC_03` as `FAIL`; trial status drops to `INELIGIBLE`.
- **Classification:** `MITIGATION` (S9).

### INJ-06: Numerical Boundary Alteration
- **Injection:** The patient's platelet count is modified from $150 \times 10^9/\text{L}$ to $99.9 \times 10^9/\text{L}$ (threshold is $\ge 100.0$).
- **Expected Defense:** `GATE-06` executes deterministic float inequality $99.9 \ge 100.0 \implies \text{False}$; marks inclusion criterion `NCT02484404_INC_05` as `FAIL`; trial status drops to `INELIGIBLE`.
- **Classification:** `MITIGATION` (S10).

### INJ-08: Contradictory Evidence Injection
- **Injection:** A liquid biopsy record asserting `EGFR wild-type` is added alongside a tissue biopsy record asserting `EGFR L858R`.
- **Expected Defense:** `GATE-09` intercepts the conflicting assertions; synthesizes a `ContradictionNode`; sets criterion `NCT02484404_INC_02` to `UNKNOWN`; routes case to `HumanReviewRecord` with `ReviewPriority.P1_CRITICAL`.
- **Classification:** `HUMAN REVIEW` (S7).

### INJ-11: Forced UNKNOWN-to-PASS Flip (Integrity Test)
- **Injection:** An adversary or buggy module manually assigns `CriterionEvaluationRecord.status = PASS` while `evidence_citations = []`.
- **Expected Defense:** `GATE-05` asserts invariant INV-03; detects empty evidence array; overwrites status to `UNKNOWN`; forces trial status to `NEEDS_REVIEW`.
- **Classification:** `PREVENTION & OVERWRITE` (S5).

### INJ-12: Blank Reviewer Override Submission
- **Injection:** An authenticated reviewer attempts to override a machine `INELIGIBLE` status with an empty string rationale (`rationale = ""`).
- **Expected Defense:** `GATE-16` Pydantic validator asserts $\text{len}(\text{rationale}) \ge 10$; raises `ValidationError`; aborts override; original machine decision remains intact.
- **Classification:** `PREVENTION` (S19).

### INJ-13: Cross-Tenant Data Injection
- **Injection:** A retrieval request for Hospital A is injected with a candidate trial record belonging exclusively to Hospital B (`hospital_id = 9999`).
- **Expected Defense:** `GATE-19` asserts tenant match; raises `TenantIsolationViolationError`; purges foreign record from reasoning context.
- **Classification:** `PREVENTION` (S21).
