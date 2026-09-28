# Phase 12 Canonical Clinical Safety Error Taxonomy (S1–S24)

**Document ID:** SAFETY-TAXONOMY-P12  
**Phase:** Phase 12 — Clinical Safety  
**Scope:** Canonical Classification, Clinical Severity, Detection Mechanisms, and Mitigations for Clinical Safety Errors  
**Status:** DRAFT — RESEARCH SPECIFICATION ONLY  

---

## 1. Executive Summary & Taxonomy Structure

The Phase 12 Safety Error Taxonomy establishes a unified, machine-enforceable classification of safety-critical failure modes in clinical trial eligibility matching.

Safety errors are classified into four severity tiers based on potential patient harm:
- **TIER 1: CRITICAL (Direct Patient Harm / Regulatory Non-Compliance):** Errors that cause inappropriate patient enrollment, overlook life-threatening contraindications, or violate legal tenant privacy.
- **TIER 2: HIGH (Indirect Clinical Risk / Integrity Failure):** Errors that misroute clinical uncertainty, fail to escalate conflicts, or introduce ungrounded medical rationale.
- **TIER 3: MEDIUM (Audit / Explainability Discrepancies):** Discrepancies between reasoning graphs and natural language explanations, or ambiguous compound logic.
- **TIER 4: LOW (Provenance & Offset Drift):** Minor character span offset inaccuracies that do not alter clinical semantic conclusions.

---

## 2. Canonical Safety Error Taxonomy (S1–S24)

```text
+-------------------------------------------------------------------------------------------------------------------------+
|                                        CANONICAL SAFETY ERROR TAXONOMY (S1–S24)                                         |
+------+------------------------------------------+----------+------------------------------------+-----------------------+
| Code | Error Category                           | Severity | Clinical Consequence               | Deterministic Gate    |
+------+------------------------------------------+----------+------------------------------------+-----------------------+
| S1   | Fabricated Patient Fact                  | CRITICAL | Erroneous match to toxic therapy   | GATE-01 (Provenance)  |
| S2   | Fabricated Trial Criterion               | CRITICAL | Patient excluded or admitted falsely| GATE-02 (Schema)      |
| S3   | Unsupported Clinical Inference           | HIGH     | Inappropriate exclusion/inclusion  | GATE-12 (Grounding)   |
| S4   | Missing Info Treated as Negative         | CRITICAL | Patient with unrecorded risk admits| GATE-11 (Open-World)  |
| S5   | UNKNOWN Treated as PASS                  | CRITICAL | Enrollment with unverified criteria| GATE-05 (Tri-State)   |
| S6   | UNKNOWN Treated as FAIL                  | HIGH     | Valid candidate wrongly rejected   | GATE-05 (Tri-State)   |
| S7   | Contradictory Evidence Ignored           | HIGH     | Arbitrary tie-breaking of tests    | GATE-09 (Conflict)    |
| S8   | Negation Error                           | CRITICAL | Comorbidity misidentified as absent| GATE-08 (Negation)    |
| S9   | Temporal Validity Error                  | CRITICAL | Enrollment during toxic washout    | GATE-07 (Washout)     |
| S10  | Numerical Threshold Error                | CRITICAL | Cytopenic / organ failure dosing   | GATE-06 (Numerical)   |
| S11  | Unit / Measurement Mismatch              | CRITICAL | $10\times$ or $100\times$ lab error| GATE-06 (Numerical)   |
| S12  | Compound Criterion Logic Error           | HIGH     | Broken boolean AND/OR evaluation   | GATE-02 (Schema)      |
| S13  | Critical Trial Omission in Retrieval     | HIGH     | Patient misses therapeutic option  | GATE-03 (Sufficiency) |
| S14  | Unsupported Eligibility Conclusion       | CRITICAL | ELIGIBLE status with zero proof    | GATE-14 (Aggregation) |
| S15  | Hallucinated Explanation                 | HIGH     | Clinician deceived by fluent text  | GATE-13 (Suppression) |
| S16  | Provenance Mismatch                      | MEDIUM   | Citation points to wrong note text | GATE-18 (Offset)      |
| S17  | Citation / Evidence Semantic Mismatch    | MEDIUM   | Cited text does not support claim  | GATE-12 (Grounding)   |
| S18  | Human-Review Routing Failure             | HIGH     | Borderline patient not escalated   | GATE-15 (Escalation)  |
| S19  | Unsafe Reviewer Override                 | CRITICAL | Unaudited override of safety rule  | GATE-16 (Override)    |
| S20  | Audit-Trail Loss                         | HIGH     | Regulatory non-reconstructibility  | GATE-20 (Audit)       |
| S21  | Cross-Tenant Information Leakage         | CRITICAL | HIPAA / GDPR privacy violation     | GATE-19 (Tenant)      |
| S22  | Stale Clinical Information Used          | HIGH     | Expired remission or obsolete labs | GATE-04 (Temporal)    |
| S23  | Ambiguous Evidence Presented Definitive  | HIGH     | Clinician misled on certainty      | GATE-05 (Tri-State)   |
| S24  | Failure to Disclose Insufficient Evidence| HIGH     | Lack of imaging/labs concealed     | GATE-11 (Open-World)  |
+------+------------------------------------------+----------+------------------------------------+-----------------------+
```

---

## 3. Detailed Specification by Error Category

### S1: Fabricated Patient Fact
- **Severity:** `CRITICAL`
- **Definition:** The system asserts a positive clinical fact (`AssertionType.PRESENT`) that has zero textual support or provenance in the patient medical record.
- **Clinical Example:** Generating an assertion `HER2-positive` for a lung adenocarcinoma patient whose chart mentions no HER2 test.
- **Trigger Condition:** Generative model confounds patient diagnoses with standard trial eligibility text.
- **Detection Mechanism:** Provenance verifier cannot locate verbatim character span in patient record.
- **Safety Gate:** `GATE-01` (Patient Fact Provenance Gate).
- **Synthetic Scenario:** `SCEN-19`.

### S2: Fabricated Trial Criterion
- **Severity:** `CRITICAL`
- **Definition:** The system evaluates or invents an eligibility requirement not found in the official protocol document.
- **Clinical Example:** Inventing an age restriction ($\le 65$) for a trial protocol that has no upper age limit.
- **Trigger Condition:** Protocol hallucination during prompt-based trial reasoning.
- **Detection Mechanism:** Criterion ID and text cannot be matched to the trial repository document database.
- **Safety Gate:** `GATE-02` (Criterion Schema Integrity Gate).
- **Synthetic Scenario:** `SCEN-18`.

### S3: Unsupported Clinical Inference
- **Severity:** `HIGH`
- **Definition:** Generating an inference that extends beyond the documented medical facts without intermediate pathological or laboratory verification.
- **Clinical Example:** Inferring that a patient has "liver metastasis" based purely on "elevated ALT/AST" without imaging confirmation.
- **Trigger Condition:** Aggressive heuristic association in language models.
- **Detection Mechanism:** Claim extractor detects an asserted diagnostic node lacking an edge from a documented finding node.
- **Safety Gate:** `GATE-12` (Claim Grounding Verification Gate).
- **Synthetic Scenario:** `SCEN-16`.

### S4: Missing Information Treated as Negative Evidence
- **Severity:** `CRITICAL`
- **Definition:** Treating the absence of a documented finding as confirmation that the finding does not exist (Closed-World Fallacy).
- **Clinical Example:** Concluding a patient is free of hepatitis B because hepatitis B is not mentioned in the outpatient visit note.
- **Trigger Condition:** Default negation assumption in binary logic models.
- **Detection Mechanism:** Reasoner produces `PASS` for an exclusion criterion when evidence list is empty.
- **Safety Gate:** `GATE-11` (Open-World Completeness Gate).
- **Synthetic Scenario:** `SCEN-01`, `SCEN-12`.

### S5: UNKNOWN Treated as PASS
- **Severity:** `CRITICAL`
- **Definition:** Converting an unverified or missing criterion directly into a passing state in trial aggregation.
- **Clinical Example:** Protocol requires ECOG PS $0$ or $1$. Patient chart lacks ECOG documentation. Aggregator marks criterion `PASS`.
- **Trigger Condition:** Optimistic default logic in eligibility score calculators.
- **Detection Mechanism:** Aggregator assertion `unknown_count > 0 and final_status == ELIGIBLE`.
- **Safety Gate:** `GATE-05` (Strict Tri-State Evidence Gate).
- **Synthetic Scenario:** `SCEN-01`, `SCEN-14`.

### S6: UNKNOWN Treated as FAIL
- **Severity:** `HIGH`
- **Definition:** Converting an unverified criterion directly into an ineligibility rejection without allowing clinical follow-up or test ordering.
- **Clinical Example:** Patient with Stage IV lung cancer rejected immediately because EGFR status is pending, rather than flagged for review upon biopsy release.
- **Trigger Condition:** Strict binary filter assuming unverified means disqualified.
- **Detection Mechanism:** Ineligibility decision where all failed criteria have status `UNKNOWN` and zero `FAIL`.
- **Safety Gate:** `GATE-05` (Strict Tri-State Evidence Gate).
- **Synthetic Scenario:** `SCEN-04`.

### S7: Contradictory Evidence Ignored
- **Severity:** `HIGH`
- **Definition:** System encounters discordant clinical observations (e.g., positive vs. negative) and selects one without disclosing the conflict.
- **Clinical Example:** Tissue biopsy reports `EGFR exon 19 del`; liquid biopsy reports `EGFR wild-type`. System marks EGFR criterion `PASS` without alert.
- **Trigger Condition:** First-hit wins parsing or simple priority ordering.
- **Detection Mechanism:** `EvidenceGraph` contains a `ContradictionNode` whose linked criteria are not marked `NEEDS_REVIEW`.
- **Safety Gate:** `GATE-09` (Contradiction Escalation Gate).
- **Synthetic Scenario:** `SCEN-05`, `SCEN-13`.

### S8: Negation Error
- **Severity:** `CRITICAL`
- **Definition:** Inverting the clinical polarity of a finding (asserting a symptom is present when it was documented as absent, or vice versa).
- **Clinical Example:** Clinical note states "Patient denies shortness of breath"; system extracts "Shortness of breath: PRESENT".
- **Trigger Condition:** NegEx window boundary failure or complex sentence structure.
- **Detection Mechanism:** Negation parser mismatch with manual ground-truth assertion annotations.
- **Safety Gate:** `GATE-08` (Negation Integrity Gate).
- **Synthetic Scenario:** `SCEN-03`.

### S9: Temporal Validity Error
- **Severity:** `CRITICAL`
- **Definition:** Evaluating eligibility based on an expired time window or enrolling during a mandatory drug washout period.
- **Clinical Example:** Protocol requires 28-day chemotherapy washout. Patient finished cytotoxic therapy 20 days ago. System evaluates criterion as `PASS`.
- **Trigger Condition:** Integer day subtraction omitted or relative date miscalculated.
- **Detection Mechanism:** Temporal validator calculates elapsed days $< \text{washout\_days}$.
- **Safety Gate:** `GATE-07` (Conservative Temporal Washout Gate).
- **Synthetic Scenario:** `SCEN-07`.

### S10: Numerical Threshold Error
- **Severity:** `CRITICAL`
- **Definition:** Boundary evaluation error on quantitative laboratory or physiological metrics.
- **Clinical Example:** Criterion requires platelets $\ge 100 \times 10^9/\text{L}$. Patient has $99 \times 10^9/\text{L}$. System marks `PASS`.
- **Trigger Condition:** Inappropriate rounding, strict $<$ vs $\le$ operator inversion.
- **Detection Mechanism:** Deterministic numerical comparator recalculates boolean inequality.
- **Safety Gate:** `GATE-06` (Deterministic Numerical Boundary Gate).
- **Synthetic Scenario:** `SCEN-08`, `SCEN-09`, `SCEN-10`.

### S11: Unit / Measurement Interpretation Error
- **Severity:** `CRITICAL`
- **Definition:** Comparing numbers across differing, unconverted measurement units.
- **Clinical Example:** Protocol specifies serum creatinine $\le 1.5\text{ mg/dL}$. Patient lab reports $120\ \mu\text{mol/L}$ ($1.36\text{ mg/dL}$). System compares $120 \le 1.5 \implies \text{FAIL}$.
- **Trigger Condition:** String comparison without unit normalization.
- **Detection Mechanism:** Unit validator verifies dimensional compatibility before comparison.
- **Safety Gate:** `GATE-06` (Deterministic Numerical Boundary Gate).
- **Synthetic Scenario:** `SCEN-11`.

### S12: Compound Criterion Logic Error
- **Severity:** `HIGH`
- **Definition:** Misinterpreting nested boolean operators in complex criteria (e.g., $(A \text{ AND } B) \text{ OR } C$).
- **Clinical Example:** Criterion requires "(Stage IV AND non-squamous) OR prior immunotherapy". Patient has Stage IV squamous with no prior immunotherapy. Evaluated as `PASS`.
- **Trigger Condition:** Linear left-to-right regex evaluation ignoring boolean precedence.
- **Detection Mechanism:** Abstract syntax tree parser for compound criteria.
- **Safety Gate:** `GATE-02` (Criterion Schema Integrity Gate).
- **Synthetic Scenario:** `SCEN-14`, `SCEN-15`.

### S13: Retrieval Omission of Critical Evidence
- **Severity:** `HIGH`
- **Definition:** Retrieval pipeline fails to retrieve relevant protocol criteria or patient records due to semantic vocabulary gaps.
- **Clinical Example:** Retrieval misses an active trial because the query used trade name "Keytruda" while protocol indexed "pembrolizumab".
- **Trigger Condition:** Dense vector embeddings failing on exact pharmaceutical synonyms.
- **Detection Mechanism:** Low recall@k against curated relevant trial qrels.
- **Safety Gate:** `GATE-03` (Retrieval Sufficiency Gate).
- **Synthetic Scenario:** `SCEN-17`.

### S14: Unsupported Eligibility Conclusion
- **Severity:** `CRITICAL`
- **Definition:** Emitting a final trial decision of `ELIGIBLE` when one or more underlying criteria lack verified evidence nodes.
- **Clinical Example:** Declaring a patient eligible for a clinical trial when 3 out of 10 criteria have empty evidence arrays.
- **Trigger Condition:** Aggregator bypass or generative summary override.
- **Detection Mechanism:** `EvidenceCoverage < 1.0` while `final_eligibility == ELIGIBLE`.
- **Safety Gate:** `GATE-14` (Deterministic Aggregation Gate).
- **Synthetic Scenario:** `SCEN-19`.

### S15: Hallucinated Explanation
- **Severity:** `HIGH`
- **Definition:** Emitting natural language explanatory text containing claims that cannot be traced to the underlying evidence graph.
- **Clinical Example:** Explanation states: "Patient has completed brain MRI confirming no intracranial disease", when the graph contains no brain MRI node.
- **Trigger Condition:** Autoregressive language generation hallucination.
- **Detection Mechanism:** `ExplanationValidator` (Phase 10 failure mode X1).
- **Safety Gate:** `GATE-13` (Hallucination Suppression Gate).
- **Synthetic Scenario:** `SCEN-20`.

### S16: Provenance Mismatch
- **Severity:** `MEDIUM`
- **Definition:** Evidence citation coordinates point to text that differs from the claimed citation string.
- **Clinical Example:** Citation character offsets $[120, 150]$ resolve to "Encounter Date: 2026-09-15" instead of "Platelets: 150".
- **Trigger Condition:** Document string trimming or encoding offset drift.
- **Detection Mechanism:** Substring slicing at `[start_offset:end_offset]` does not equal `text_snippet`.
- **Safety Gate:** `GATE-18` (Verbatim Provenance Gate).
- **Synthetic Scenario:** `SCEN-23`.

### S17: Citation / Evidence Semantic Mismatch
- **Severity:** `MEDIUM`
- **Definition:** Character offsets are valid, but the cited text span does not semantically support the criterion conclusion.
- **Clinical Example:** Criterion requires adequate renal function; citation quotes "Patient has normal bowel sounds".
- **Trigger Condition:** Model selects random nearby passage as spurious evidence citation.
- **Detection Mechanism:** Entailment scoring between cited text span and criterion text.
- **Safety Gate:** `GATE-12` (Claim Grounding Verification Gate).
- **Synthetic Scenario:** `SCEN-16`.

### S18: Human-Review Routing Failure
- **Severity:** `HIGH`
- **Definition:** System encounters an unresolvable uncertainty, missing datum, or contradiction but fails to generate a review record.
- **Clinical Example:** Patient with pending molecular testing emitted as a finalized decision rather than queued for nurse navigator review.
- **Trigger Condition:** Routing logic conditional failure or threshold rounding.
- **Detection Mechanism:** Case has `unknown_count > 0` but no `HumanReviewRecord` is created.
- **Safety Gate:** `GATE-15` (Mandatory Human Escalation Gate).
- **Synthetic Scenario:** `SCEN-01`, `SCEN-05`.

### S19: Unsafe Reviewer Override
- **Severity:** `CRITICAL`
- **Definition:** A human reviewer overrides a safety gate or machine `FAIL` without recording an audited rationale and evidence.
- **Clinical Example:** Reviewer flips `INELIGIBLE` to `ELIGIBLE` for a patient with creatinine $> 3.0$ with zero explanatory text.
- **Trigger Condition:** Review interface permitting blank rationale submission.
- **Detection Mechanism:** `ReviewerDecision.rationale` length $< 10$ characters or missing credential verification.
- **Safety Gate:** `GATE-16` (Auditable Override Gate).
- **Synthetic Scenario:** `SCEN-22`.

### S20: Audit-Trail Loss
- **Severity:** `HIGH`
- **Definition:** Eligibility evaluation, human review, or override occurs without persisting an immutable log entry.
- **Trigger Condition:** Database error or unhandled exception during audit logging call.
- **Detection Mechanism:** System audit log query yields zero records for an executed evaluation ID.
- **Safety Gate:** `GATE-20` (Fail-Closed Audit Gate).
- **Synthetic Scenario:** `SCEN-21`.

### S21: Cross-Tenant Information Leakage
- **Severity:** `CRITICAL`
- **Definition:** Clinical records, trial criteria, or prompt texts belonging to Hospital A are accessible or retrieved by Hospital B.
- **Trigger Condition:** Shared cache key collision or query omitting `hospital_id` filter.
- **Detection Mechanism:** Tenant ID verification between authenticated user context and retrieved data items.
- **Safety Gate:** `GATE-19` (Cryptographic Tenant Boundary Gate).
- **Synthetic Scenario:** `SCEN-24`.

### S22: Stale Clinical Information Used as Current
- **Severity:** `HIGH`
- **Definition:** Using clinical facts past their clinical shelf-life (e.g., CBC labs from 6 months ago) to satisfy current eligibility.
- **Trigger Condition:** Lack of recency filtering on longitudinal patient notes.
- **Detection Mechanism:** Fact timestamp $> 90$ days prior to evaluation encounter date.
- **Safety Gate:** `GATE-04` (Temporal Evidence Validity Gate).
- **Synthetic Scenario:** `SCEN-06`.

### S23: Ambiguous Evidence Presented as Definitive
- **Severity:** `HIGH`
- **Definition:** A qualified or probabilistic statement (e.g., "Suspicious for recurrence") presented to clinician as definitive proof of metastasis.
- **Trigger Condition:** Assertion extractor stripping hedge modifiers ("suspicious", "probable", "borderline").
- **Detection Mechanism:** Fact confidence score $< 0.8$ asserted with `AssertionType.PRESENT` without uncertainty flag.
- **Safety Gate:** `GATE-05` (Strict Tri-State Evidence Gate).
- **Synthetic Scenario:** `SCEN-04`.

### S24: Failure to Disclose Insufficient Evidence
- **Severity:** `HIGH`
- **Definition:** Emitting an eligibility assessment without explicitly listing missing tests or diagnostic gaps to the clinician.
- **Trigger Condition:** Summary generator omitting the `missing_information` array from the output view.
- **Detection Mechanism:** `len(missing_information) == 0` when `unknown_count > 0`.
- **Safety Gate:** `GATE-11` (Open-World Completeness Gate).
- **Synthetic Scenario:** `SCEN-01`, `SCEN-02`.
