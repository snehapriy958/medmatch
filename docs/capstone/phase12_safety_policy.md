# Phase 12 Clinical Safety Policy: Canonical Conservative Reasoning Rules

**Document ID:** SAFETY-POLICY-P12  
**Phase:** Phase 12 — Clinical Safety  
**Scope:** Canonical Behavioral Rules Across 18 Safety-Critical Reasoning Dimensions  
**Status:** DRAFT — RESEARCH SPECIFICATION ONLY  

---

## 1. Executive Summary & Policy Foundations

The MedMatch Clinical Safety Policy establishes the authoritative rules governing automated reasoning under clinical uncertainty.

> [!CRITICAL]
> **POLICY GOVERNING PRINCIPLE:**  
> In all clinical eligibility evaluations, **conservative failure takes precedence over false certainty**.  
> The system must NEVER convert absence of evidence into presence of compliance.  
> Every rule in this policy either:
> 1. Directly enforces an existing MedMatch upstream contract (Phases 2–11),
> 2. Represents an explicit conservative research safety rule, or
> 3. Implements standard good clinical practice (GCP) and multi-tenant data governance.

---

## 2. Canonical Safety Policies Across 18 Clinical Dimensions

```text
+-------------------------------------------------------------------------------------------------------------------------+
|                                        CANONICAL SAFETY POLICY SUMMARY (POL-01 to POL-18)                               |
+--------+------------------------------------+------------------------------------------+--------------------------------+
| Rule   | Policy Dimension                   | Mandatory Safe Behavior                  | Strictly Prohibited Behavior   |
+--------+------------------------------------+------------------------------------------+--------------------------------+
| POL-01 | Missing Patient Information        | Default to UNKNOWN / Open-World Assumption| Never treat absence as negative|
| POL-02 | Missing Trial Criteria             | Invalidate evaluation / Incomplete trial | Never evaluate partial protocol|
| POL-03 | UNKNOWN Criterion Status           | Forces NEEDS_REVIEW in aggregation       | Never treat UNKNOWN as PASS/FAIL|
| POL-04 | Conflicting Patient Facts          | Escalate to UNKNOWN + Review Queue       | Never apply arbitrary heuristic|
| POL-05 | Conflicting Trial Clauses          | Flag Protocol Discrepancy + Review       | Never pick one clause silently |
| POL-06 | Negated Clinical Findings          | Assertion=ABSENT; Exclusion=PASS         | Never invert polarity          |
| POL-07 | Temporal Ambiguity & Washout       | Enforce strict duration or default UNK   | Never ignore relative washout  |
| POL-08 | Numerical Boundary Values          | Strict inequality; exact boundary check  | Never round favorably to admit |
| POL-09 | Measurement Unit Mismatch          | Explicit conversion or UNKNOWN if incompt| Never compare raw strings      |
| POL-10 | Compound Criterion Logic           | Full boolean AST evaluation              | Never evaluate partial clauses |
| POL-11 | Unsupported Evidence               | Strip claim; tag UNSUPPORTED             | Never permit fabricated proof  |
| POL-12 | Contradicted Evidence              | Disclose conflict; force UNKNOWN status  | Never suppress contradiction   |
| POL-13 | Insufficient Retrieval Evidence    | Return INSUFFICIENT_RETRIEVAL_DATA       | Never return POSSIBLY_ELIGIBLE |
| POL-14 | Low-Confidence / Hedged Reasoning  | Confidence < 0.8 forces UNCERTAIN status | Never present guess as fact    |
| POL-15 | Human Review Escalation            | Automatically place in priority queue    | Never bypass clinical oversight|
| POL-16 | Human Reviewer Override            | Preserve machine state; require rationale| Never allow blank overrides    |
| POL-17 | Explanation Faithfulness           | Strictly bounded by Evidence Graph nodes | Never introduce ungrounded text|
| POL-18 | Provenance Integrity Failure       | Reject citation; flag PROVENANCE_ERROR   | Never use phantom citations    |
+--------+------------------------------------+------------------------------------------+--------------------------------+
```

---

## 3. Detailed Specification by Policy Dimension

### POL-01: Missing Patient Information
- **Scope:** Patient medical record makes no mention of a required biomarker, diagnostic test, or clinical history item.
- **Mandatory Safe Behavior:** The criterion must evaluate strictly to `CriterionEvaluationStatus.UNKNOWN`. The missing item must be added to the trial evaluation's `missing_information` array.
- **Prohibited Behavior:** Treating absence of documentation as absence of disease (Closed-World Assumption).
- **Escalation Path:** Trigger `UncertaintyDimension.MISSING_INFORMATION` and route case to `NEEDS_REVIEW`.

### POL-02: Missing Trial Criteria Information
- **Scope:** Trial protocol in database lacks complete criteria definitions (e.g., inclusion criteria present but exclusion criteria missing).
- **Mandatory Safe Behavior:** The system must reject the trial evaluation with `IncompleteProtocolError`. Eligibility evaluation must be halted for that trial until the full protocol is hydrated.
- **Prohibited Behavior:** Evaluating eligibility against an incomplete subset of criteria.
- **Escalation Path:** Log protocol ingestion warning; emit `INSUFFICIENT_PROTOCOL_DATA`.

### POL-03: UNKNOWN Criterion Status
- **Scope:** Any criterion where evidence is absent, ambiguous, pending, or conflicting.
- **Mandatory Safe Behavior:** In trial-level aggregation, if `failed_count == 0` and `unknown_count >= 1`, the final trial eligibility status MUST evaluate strictly to `EligibilityStatus.NEEDS_REVIEW`.
- **Prohibited Behavior:** Converting `UNKNOWN` to `PASS` (false optimism) or `FAIL` (premature rejection).
- **Escalation Path:** Add to clinician review queue with priority proportional to the clinical criticality of the criterion.

### POL-04: Conflicting Patient Facts
- **Scope:** Patient chart contains discordant observations from different modalities or dates (e.g., positive tissue vs negative cfDNA).
- **Mandatory Safe Behavior:** The criterion must evaluate to `UNKNOWN` with `reasoning` explicitly noting the discordance. A `ContradictionNode` must be synthesized in the evidence graph.
- **Prohibited Behavior:** Silently selecting the most recent, most favorable, or first-parsed fact without clinical review.
- **Escalation Path:** Trigger `UncertaintyDimension.CONFLICTING_EVIDENCE` with `ReviewPriority.P1_CRITICAL`.

### POL-05: Conflicting Trial Criteria Clauses
- **Scope:** Protocol contains contradictory text (e.g., synopsis lists ECOG 0–1; body text permits ECOG 0–2).
- **Mandatory Safe Behavior:** Apply the most conservative interpretation (strict subset) and flag the protocol discrepancy in the explanation.
- **Prohibited Behavior:** Selecting the permissive clause to maximize enrollment without sponsor clarification.
- **Escalation Path:** Escalate to study coordinator for protocol amendment verification.

### POL-06: Negated Clinical Findings
- **Scope:** Medical narrative containing linguistic negation ("patient denies fever", "negative for intracranial lesions", "no prior immunotherapy").
- **Mandatory Safe Behavior:** Fact assertion must be recorded as `AssertionType.ABSENT`. For an exclusion criterion ("Excludes prior immunotherapy"), `ABSENT` results in criterion `PASS`. For an inclusion criterion ("Requires prior immunotherapy"), `ABSENT` results in criterion `FAIL`.
- **Prohibited Behavior:** Ignoring negation cues or mistaking negated historical conditions for active comorbidities.
- **Escalation Path:** Ambiguous negation (double negatives, hedging) defaults to `AssertionType.UNKNOWN`.

### POL-07: Temporal Ambiguity, Washout & Staleness
- **Scope:** Patient completed prior therapy subject to a protocol washout window ($\ge 28$ days, $\ge 14$ days) or possesses historical diagnostic findings.
- **Mandatory Safe Behavior:**
  1. **Criterion-Dependent Validity:** Temporal validity is strictly criterion-dependent. If a trial protocol defines a time window (e.g., "washout $\ge 28$ days" or "laboratory tests within 14 days of enrollment"), that protocol-specified duration is enforced.
  2. **Synthetic Research Fixture Parameter:** A generic threshold (such as 90 days for dynamic laboratory results) is strictly a synthetic research fixture test parameter and must NOT be presented as a universal medical standard.
  3. **Ambiguity Handling:** If elapsed duration cannot be determined, dates are relative ("a few weeks ago"), or temporal semantics are unsupported, status MUST evaluate to `UNKNOWN` and escalate to clinician review.
- **Prohibited Behavior:** Enrolling a patient without calculating the exact day difference; silently converting temporal ambiguity into compliance.
- **Escalation Path:** Route temporal ambiguity to research nurse to confirm exact infusion or biopsy dates.

### POL-08: Numerical Boundary Values
- **Scope:** Quantitative laboratory and physiological thresholds (platelets, ANC, creatinine clearance, ejection fraction, age).
- **Mandatory Safe Behavior:** Evaluate exact mathematical inequalities deterministically in Python using float representation:
  - Strict: $x > T$ or $x < T$
  - Inclusive: $x \ge T$ or $x \le T$
  A value of $99.9$ against a threshold of $\ge 100.0$ MUST evaluate to `FAIL` (or `FAIL` on inclusion $\implies$ ineligibility).
- **Prohibited Behavior:** Rounding up near-boundary values ($99 \rightarrow 100$) to force eligibility.
- **Escalation Path:** Borderline values within standard lab margin of error ($1\%$) flagged for repeat test recommendation.

### POL-09: Measurement Unit Mismatch & Ontology Scope
- **Scope:** Patient lab value reported in units differing from protocol specification ($\text{g/dL}$ vs $\text{g/L}$; $\text{mg/dL}$ vs $\mu\text{mol/L}$).
- **Mandatory Safe Behavior:**
  1. **Supported Research Conversions:** The system supports validated mathematical conversions for tested oncology research fixture units:
     - Creatinine: $\mu\text{mol/L} \leftrightarrow \text{mg/dL}$ (conversion factor $88.42$)
     - Platelets / Leukocytes: $10^9/\text{L} \leftrightarrow \text{K}/\mu\text{L}$ (equivalence)
  2. **Unsupported Units:** Any units outside the tested research domain (e.g. arbitrary enzyme activity units U/L vs mg/dL, mass vs volume without analyte density) MUST NOT be silently converted. They must produce an explicit unsupported-unit condition (`SafetyTaxonomyCode.S11`) and default to `UNKNOWN` / human review.
  3. **Ontology Limitation Disclosure:** The unit conversion framework represents research fixture coverage, NOT an exhaustive clinical unit ontology (such as Unified Code for Units of Measure / UCUM).
- **Prohibited Behavior:** Comparing raw numerical values without unit verification; silently coercing unsupported units.
- **Escalation Path:** Flag `UNIT_MISMATCH_ERROR` and request clinical laboratory clarification.

### POL-10: Compound Criteria Logic
- **Scope:** Complex criteria containing nested boolean operators (AND, OR, NOT).
- **Mandatory Safe Behavior:** Parse into an explicit boolean abstract syntax tree (AST):
  - For $A \text{ AND } B$: Both must be `PASS` for criterion `PASS`. If either is `FAIL`, criterion is `FAIL`. If one is `PASS` and one `UNKNOWN`, criterion is `UNKNOWN`.
  - For $A \text{ OR } B$: If either is `PASS`, criterion is `PASS`. If both are `FAIL`, criterion is `FAIL`.
- **Prohibited Behavior:** Evaluating only the first clause and ignoring remaining conjunctions.
- **Escalation Path:** Compound ambiguity routes to `NEEDS_REVIEW`.

### POL-11: Unsupported Evidence Claims
- **Scope:** Natural language rationale or criterion conclusion asserting a clinical fact not grounded in the patient profile.
- **Mandatory Safe Behavior:** Strip unsupported claims from the output. Invalidate any criterion conclusion that relies on an ungrounded claim (`ClaimSupportStatus.UNSUPPORTED`).
- **Prohibited Behavior:** Emitting an unverified generative statement as clinical evidence.
- **Escalation Path:** Flag `UNSUPPORTED_CLAIM_ERROR` (Taxonomy S3/S14) and force `UNKNOWN`.

### POL-12: Contradicted Evidence Handling
- **Scope:** Model reasoning asserts a fact directly contradicted by patient record (e.g., claiming patient is ECOG 0 when chart documents ECOG 2).
- **Mandatory Safe Behavior:** Intercept and reject reasoning; emit explicit contradiction disclosure; force status to `FAIL` or `UNKNOWN`.
- **Prohibited Behavior:** Silently suppressing the contradictory patient record passage.
- **Escalation Path:** Record `ContradictionDisclosureRate` violation and trigger clinician alert.

### POL-13: Insufficient Retrieval Evidence
- **Scope:** Retrieval query returns zero candidate trial criteria meeting the similarity threshold.
- **Mandatory Safe Behavior:** Return an explicit status of `INSUFFICIENT_RETRIEVAL_DATA` with message: *"No matching clinical trial criteria were retrieved. Eligibility cannot be determined."*
- **Prohibited Behavior:** Returning `POSSIBLY_ELIGIBLE` with zero retrieved trials (remedying production risk `R-RET-01`).
- **Escalation Path:** Suggest broader search terms or alternate clinical disease synonyms.

### POL-14: Low-Confidence / Uncertain Reasoning
- **Scope:** Extracted fact confidence score or model reasoning confidence falls below safety threshold ($\text{confidence} < 0.80$).
- **Mandatory Safe Behavior:** Downgrade decision to `NEEDS_REVIEW` and disclose the low confidence score.
- **Prohibited Behavior:** Masking uncertainty by omitting the confidence metric.
- **Escalation Path:** Route case to senior clinical investigator.

### POL-15: Mandatory Human Review Escalation
- **Scope:** Any trial evaluation where `unknown_count > 0`, `conflicts > 0`, or final status is `NEEDS_REVIEW`.
- **Mandatory Safe Behavior:** Create a structured `HumanReviewRecord` with calculated `ReviewPriority` (`P1_CRITICAL` to `P4_INFORMATIONAL`), placing the case in the active review queue.
- **Prohibited Behavior:** Allowing an automated matching session to finalize without queuing unresolved uncertainties.
- **Escalation Path:** Track time-to-review; alert study coordinator if critical review is pending $> 24$ hours.

### POL-16: Human Reviewer Override Semantics
- **Scope:** A credentialed clinical reviewer modifies an automated criterion status or trial eligibility decision.
- **Mandatory Safe Behavior:**
  1. The original machine evaluation MUST be preserved immutably.
  2. The reviewer decision MUST record `reviewer_id`, `timestamp`, `rationale` ($\ge 10$ characters), and `supporting_evidence`.
  3. The final combined record must clearly identify that an override occurred.
- **Prohibited Behavior:** Overwriting or deleting the machine evaluation; permitting overrides without entered rationale.
- **Escalation Path:** Persist override to the immutable audit trail.

### POL-17: Explanation Graph Alignment
- **Scope:** Generating natural language explanations for patients and clinicians.
- **Mandatory Safe Behavior:** Every asserted sentence in an explanation must map to at least one valid node in the `EvidenceGraph`. No clinical facts, trials, or conclusions may appear in text that do not exist in the graph.
- **Prohibited Behavior:** Producing persuasive or conversational summaries containing non-graph statements.
- **Escalation Path:** Run `ExplanationValidator`; if ungrounded claims appear, reject explanation and fall back to tabular criterion summary.

### POL-18: Provenance Verification & Offset Integrity
- **Scope:** Citations linking patient facts or trial criteria to source document character spans.
- **Mandatory Safe Behavior:** Character offsets $[start, end]$ must resolve to the exact text snippet in the source document. If exact offsets are not computable, the system must explicitly set offset to `-1` and record the document/field identifier.
- **Prohibited Behavior:** Fabricating bogus positive offsets that point to unrelated text.
- **Escalation Path:** Flag `PROVENANCE_ERROR` and log citation validation failure.

### POL-19: Multi-Tenant Data Isolation
- **Scope:** Clinical trial and patient matching transactions across distinct hospital systems.
- **Mandatory Safe Behavior:** Strict tenant boundary enforcement (`GATE-19`). Matching requests, candidate trial retrieval, and caching must strictly match `user.hospital_id == request.hospital_id`. Any cross-tenant data access attempt must be immediately aborted with `TenantIsolationViolationError`.
- **Prohibited Behavior:** Permitting foreign hospital candidate records to leak into retrieval or reasoning.
- **Escalation Path:** Security audit alert; immediate session invalidation.

### POL-20: Fail-Closed Audit Logging
- **Scope:** Persistence of clinical matching decisions and audit trails.
- **Mandatory Safe Behavior:** Audit trail persistence must fail closed (`GATE-20`). If the audit log fails to write to the persistent store, the matching transaction must abort rather than emit an untracked clinical recommendation.
- **Prohibited Behavior:** Swallowing audit logging exceptions and continuing execution.
- **Escalation Path:** System administrator alert; transaction rollback.
