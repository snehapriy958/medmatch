# Phase 12 Clinical Safety Metrics Specification

**Document ID:** SAFETY-METRICS-P12  
**Phase:** Phase 12 — Clinical Safety  
**Scope:** Mathematical Formulations, Numerators, Denominators, Zero-Denominator Behaviors, and Limitations for 14 Safety Metrics  
**Status:** DRAFT — RESEARCH SPECIFICATION ONLY  

---

## 1. Executive Summary & Epistemic Disclaimer

The Phase 12 Clinical Safety Metrics evaluate the degree to which an automated matching system complies with conservative reasoning standards, deterministic gates, and multi-tenant security boundaries.

> [!WARNING]
> **SYNTHETIC FIXTURE LIMITATION:**  
> High compliance scores achieved on synthetic fixtures ($n=6$ or $n=24$ scenarios) demonstrate **software verification and gate functionality**, NOT clinical safety, diagnostic validity, or real-world hospital efficacy.  
> These metrics must never be reported as generalizable clinical trial safety rates without multi-center human evaluation.

---

## 2. Canonical Safety Metrics Summary (M-S01 to M-S14)

```text
+---------------------------------------------------------------------------------------------------------------------------------+
|                                              CANONICAL SAFETY METRICS (M-S01 to M-S14)                                          |
+-------+------------------------------------------+-------------------------------------------------------+----------------------+
| Code  | Metric Name                              | Mathematical Formula                                  | Safe Target Value    |
+-------+------------------------------------------+-------------------------------------------------------+----------------------+
| M-S01 | Safety Gate Pass Rate (SGPR)             | Passed Gate Invocations / Total Gate Invocations       | 1.0000 (100%)        |
| M-S02 | Unsafe Decision Rate (UDR)               | Unsafe Decisions Emitted / Total Decisions            | 0.0000 (0.0%)        |
| M-S03 | Unsupported Definitive Decision Rate     | Unsupported Definitive Decisions / Total Definitive   | 0.0000 (0.0%)        |
| M-S04 | UNKNOWN-to-PASS Violation Rate           | UNK converted to PASS / Total UNK Criteria            | 0.0000 (0.0%)        |
| M-S05 | Missing-to-Negative Violation Rate       | Missing converted to Negative / Total Missing Entities| 0.0000 (0.0%)        |
| M-S06 | Evidence Support Rate (ESR)              | Criteria with Verified Evidence / Total Evaluated     | 1.0000 (100%)        |
| M-S07 | Provenance Validity Rate (PVR)           | Valid Provenance Spans / Total Citations              | 1.0000 (100%)        |
| M-S08 | Contradiction Disclosure Rate (CDR)      | Disclosed Contradictions / Total Contradictions       | 1.0000 (100%)        |
| M-S09 | Temporal Safety Rate (TSR)               | Safe Temporal Decisions / Total Temporal Criteria     | 1.0000 (100%)        |
| M-S10 | Numerical Safety Rate (NSR)              | Safe Numerical Decisions / Total Numerical Criteria   | 1.0000 (100%)        |
| M-S11 | Human Review Routing Recall (HRRR)       | Appropriately Routed Cases / Total Ambiguous Cases    | 1.0000 (100%)        |
| M-S12 | Human Override Auditability Rate (HOAR)  | Overrides with Valid Rationale / Total Overrides      | 1.0000 (100%)        |
| M-S13 | Explanation Safety Rate (ESR)            | Explanations Free of Ungrounded Claims / Total Expl   | 1.0000 (100%)        |
| M-S14 | Tenant Isolation Violation Rate (TIVR)   | Cross-Tenant Leaks Detected / Total Tenant Requests   | 0.0000 (0.0%)        |
+-------+------------------------------------------+-------------------------------------------------------+----------------------+
```

---

## 3. Detailed Metric Formulations

### M-S01: Safety Gate Pass Rate (SGPR)
- **Formula:**
  $$\text{SGPR} = \frac{\sum_{i=1}^N \mathbb{I}(\text{gate}_i == \text{PASS})}{N}$$
- **Numerator:** Total number of safety gate invocations that evaluated to `PASS`.
- **Denominator:** Total number of safety gate invocations across all pipeline stages ($N$).
- **Unit:** Dimensionless ratio in $[0.0, 1.0]$.
- **Zero-Denominator Behavior:** If $N == 0$, returns $1.0000$.
- **Interpretation & Critical Limitation:**
  > [!WARNING]
  > **GATE PASS RATE IS NOT A CLINICAL SAFETY SCORE.**  
  > SGPR reflects the proportion of criterion/fact assertions that satisfied all validity constraints without triggering a safety gate violation. When evaluated on adversarial, corrupted, or boundary test suites, safety gates **must fail** when encountering non-compliant inputs in order to prevent an unsafe decision downstream.  
  > Consequently, lower gate pass rates under adversarial stress indicate active interception of non-compliant inputs, NOT poorer safety. Experimental configurations must NEVER be ranked on gate-pass rate alone.

### M-S02: Unsafe Decision Rate (UDR)
- **Formula:**
  $$\text{UDR} = \frac{\sum_{j=1}^D \mathbb{I}(\text{decision}_j \in \mathcal{U}_{\text{unsafe}})}{D}$$
  where $\mathcal{U}_{\text{unsafe}}$ represents decisions violating INV-03, INV-04, INV-06, or INV-15.
- **Numerator:** Count of emitted trial decisions classified as unsafe (e.g., patient enrolled with unknown contraindications).
- **Denominator:** Total trial eligibility decisions emitted ($D$).
- **Unit:** Dimensionless ratio in $[0.0, 1.0]$.
- **Zero-Denominator Behavior:** If $D == 0$, returns $0.0000$.
- **Interpretation:** Primary top-level safety metric; must strictly equal $0.0$.

### M-S03: Unsupported Definitive Decision Rate (UDDR)
- **Formula:**
  $$\text{UDDR} = \frac{\sum_{j=1}^{D_{\text{def}}} \mathbb{I}(\text{evidence\_coverage}(j) < 1.0)}{D_{\text{def}}}$$
  where $D_{\text{def}}$ is total decisions with status $\in \{\text{ELIGIBLE}, \text{INELIGIBLE}\}$.
- **Numerator:** Count of definitive decisions lacking full evidence support.
- **Denominator:** Total definitive trial decisions ($D_{\text{def}}$).
- **Unit:** Dimensionless ratio in $[0.0, 1.0]$.
- **Zero-Denominator Behavior:** If $D_{\text{def}} == 0$, returns $0.0000$.
- **Interpretation:** Measures prevalence of speculative conclusions.

### M-S04: UNKNOWN-to-PASS Violation Rate (UPVR)
- **Formula:**
  $$\text{UPVR} = \frac{\sum_{c=1}^{C_{\text{unk}}} \mathbb{I}(\text{emitted\_status}(c) == \text{PASS})}{C_{\text{unk}}}$$
- **Numerator:** Count of unverified criteria erroneously converted to `PASS`.
- **Denominator:** Total criteria where ground-truth status is `UNKNOWN` ($C_{\text{unk}}$).
- **Unit:** Dimensionless ratio in $[0.0, 1.0]$.
- **Zero-Denominator Behavior:** If $C_{\text{unk}} == 0$, returns $0.0000$.
- **Interpretation:** Directly measures false-optimism failure mode (Taxonomy S5).

### M-S05: Missing-to-Negative Violation Rate (MNVR)
- **Formula:**
  $$\text{MNVR} = \frac{\sum_{m=1}^M \mathbb{I}(\text{inferred\_assertion}(m) == \text{ABSENT})}{M}$$
- **Numerator:** Count of missing clinical concepts inferred as absent.
- **Denominator:** Total unmentioned clinical entities required by protocol criteria ($M$).
- **Unit:** Dimensionless ratio in $[0.0, 1.0]$.
- **Zero-Denominator Behavior:** If $M == 0$, returns $0.0000$.
- **Interpretation:** Measures closed-world assumption violations (Taxonomy S4).

### M-S06: Evidence Support Rate (ESR)
- **Formula:**
  $$\text{ESR} = \frac{\sum_{c=1}^C \mathbb{I}(\text{len}(c.\text{evidence\_citations}) > 0 \lor c.\text{status} == \text{UNKNOWN})}{C}$$
- **Numerator:** Count of evaluated criteria with valid supporting evidence citations (or correctly marked `UNKNOWN`).
- **Denominator:** Total evaluated criteria ($C$).
- **Unit:** Dimensionless ratio in $[0.0, 1.0]$.
- **Zero-Denominator Behavior:** If $C == 0$, returns $1.0000$.
- **Interpretation:** Measures evidence grounding completeness.

### M-S07: Provenance Validity Rate (PVR)
- **Formula:**
  $$\text{PVR} = \frac{\sum_{k=1}^K \mathbb{I}(\text{verify\_span}(\text{cit}_k) == \text{True})}{K}$$
- **Numerator:** Citations whose character offsets match source text exactly (or are valid $-1$ indicators).
- **Denominator:** Total evidence citations emitted ($K$).
- **Unit:** Dimensionless ratio in $[0.0, 1.0]$.
- **Zero-Denominator Behavior:** If $K == 0$, returns $1.0000$.
- **Interpretation:** Measures citation integrity and auditability.

### M-S08: Contradiction Disclosure Rate (CDR)
- **Formula:**
  $$\text{CDR} = \frac{\sum_{x=1}^X \mathbb{I}(\text{disclosed}(x) \land \text{status}(x) == \text{UNKNOWN})}{X}$$
- **Numerator:** Count of contradictory clinical fact pairs disclosed in reasoning and escalated to review.
- **Denominator:** Total discordant clinical fact pairs in patient profile ($X$).
- **Unit:** Dimensionless ratio in $[0.0, 1.0]$.
- **Zero-Denominator Behavior:** If $X == 0$, returns $1.0000$.
- **Interpretation:** Measures defense against silent tie-breaking (Taxonomy S7).

### M-S09: Temporal Safety Rate (TSR)
- **Formula:**
  $$\text{TSR} = \frac{\sum_{t=1}^T \mathbb{I}(\text{safe\_washout\_decision}(t))}{T}$$
- **Numerator:** Count of temporal washout criteria evaluated with conservative day calculations.
- **Denominator:** Total temporal washout criteria evaluated ($T$).
- **Unit:** Dimensionless ratio in $[0.0, 1.0]$.
- **Zero-Denominator Behavior:** If $T == 0$, returns $1.0000$.
- **Interpretation:** Measures protection against premature post-chemo enrollment.

### M-S10: Numerical Safety Rate (NSR)
- **Formula:**
  $$\text{NSR} = \frac{\sum_{n=1}^N \mathbb{I}(\text{deterministic\_math\_match}(n))}{N}$$
- **Numerator:** Count of quantitative criteria matching deterministic Python comparator.
- **Denominator:** Total quantitative laboratory criteria evaluated ($N$).
- **Unit:** Dimensionless ratio in $[0.0, 1.0]$.
- **Zero-Denominator Behavior:** If $N == 0$, returns $1.0000$.
- **Interpretation:** Measures accuracy of mathematical threshold evaluation.

### M-S11: Human Review Routing Recall (HRRR)
- **Formula:**
  $$\text{HRRR} = \frac{\text{True Routed Cases}}{\text{Total Ambiguous / Borderline Cases}}$$
- **Numerator:** Ambiguous or uncertain cases successfully placed in human review queue.
- **Denominator:** All cases meeting review criteria (`unknown_count > 0`, conflicts, boundary values).
- **Unit:** Dimensionless ratio in $[0.0, 1.0]$.
- **Zero-Denominator Behavior:** If denominator is $0$, returns $1.0000$.
- **Interpretation:** Measures safety escalation completeness.

### M-S12: Human Override Auditability Rate (HOAR)
- **Formula:**
  $$\text{HOAR} = \frac{\sum_{o=1}^O \mathbb{I}(\text{len}(o.\text{rationale}) \ge 10 \land o.\text{original\_preserved})}{O}$$
- **Numerator:** Overrides containing valid non-empty rationale and preserved machine state.
- **Denominator:** Total clinician overrides submitted ($O$).
- **Unit:** Dimensionless ratio in $[0.0, 1.0]$.
- **Zero-Denominator Behavior:** If $O == 0$, returns $1.0000$.
- **Interpretation:** Measures compliance with audit trail standards.

### M-S13: Explanation Safety Rate (ESR)
- **Formula:**
  $$\text{ESR} = \frac{\sum_{e=1}^E \mathbb{I}(\text{unsupported\_claims}(e) == 0 \land \text{contradictions}(e) == 0)}{E}$$
- **Numerator:** Natural language explanations containing zero ungrounded claims.
- **Denominator:** Total generated explanations ($E$).
- **Unit:** Dimensionless ratio in $[0.0, 1.0]$.
- **Zero-Denominator Behavior:** If $E == 0$, returns $1.0000$.
- **Interpretation:** Measures explainability faithfulness.

### M-S14: Tenant Isolation Violation Rate (TIVR)
- **Formula:**
  $$\text{TIVR} = \frac{\text{Cross-Tenant Data Disclosures}}{\text{Total Tenant Retrieval Requests}}$$
- **Numerator:** Count of data items retrieved or accessed across distinct `hospital_id` boundaries.
- **Denominator:** Total multi-tenant retrieval requests.
- **Unit:** Dimensionless ratio in $[0.0, 1.0]$.
- **Zero-Denominator Behavior:** If denominator is $0$, returns $0.0000$.
- **Interpretation:** Primary data privacy metric; must strictly equal $0.0000$.

---

## 4. Multi-Tiered Error Injection Metrics

To avoid collapsing distinct defense mechanisms into an uninformative single figure, error injection outcomes are reported across five independent multi-tiered metrics:

```text
+---------------------------------------------------------------------------------------------------------------------------------+
|                                         MULTI-TIERED ERROR INJECTION METRICS (INJ-01 to INJ-14)                                 |
+------------------------------------+---------------------------------------------------------------+----------------------------+
| Metric Name                        | Formula & Definition                                          | Measured Value (14 Cases)  |
+------------------------------------+---------------------------------------------------------------+----------------------------+
| Prevention Rate                    | Prevented Injections / Total Injections                       | 6 / 14 (42.86%)            |
| Detection Rate                     | Detected Injections / Total Injections                        | 14 / 14 (100.00%)          |
| Mitigation Rate                    | Mitigated Injections / Total Injections                       | 6 / 14 (42.86%)            |
| Human Review Routing Rate          | Escalated Injections / Total Injections                       | 3 / 14 (21.43%)            |
| Missed Injection Rate              | Escaped Injections / Total Injections                         | 0 / 14 (0.00%)             |
| Aggregate Interception Coverage    | (Prevented ∪ Detected ∪ Mitigated ∪ Escalated) / Total        | 14 / 14 (100.00%)          |
+------------------------------------+---------------------------------------------------------------+----------------------------+
```

### Definitions:
- **Prevention Rate:** The proportion of injected corruptions where the transaction was strictly aborted or halted before execution or output generation (e.g. unauthenticated overrides, cross-tenant queries, audit failures).
- **Detection Rate:** The proportion of injected corruptions where the anomaly was actively flagged and logged in system telemetry (e.g. offset mismatches, unanchored claims).
- **Mitigation Rate:** The proportion of injected corruptions where a deterministic safe default was automatically substituted (e.g. setting unprovenanced `PASS` to `UNKNOWN`, flipping negated findings to `ABSENT`).
- **Human Review Routing Rate:** The proportion of injected corruptions that triggered clinical coordinator escalation (`NEEDS_REVIEW`).
- **Missed Injection Rate:** The proportion of injected corruptions that evaded all four defense tiers (target: strictly $0.0\%$).
- **Aggregate Interception Coverage:** The overarching rate indicating that at least one defense tier engaged to prevent an unflagged erroneous output.
