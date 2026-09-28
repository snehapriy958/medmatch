# Phase 9 Development Test Fixtures

## 1. Overview & Guardrails

This directory contains synthetic development test fixtures for validating the MedMatch Phase 9 Uncertainty Representation, Review-Routing Policy, Review Prioritizer, Audit Trail, and Human Adjudication State Machine.

> [!WARNING]
> **DEVELOPMENT TEST FIXTURES ONLY**
> The records in `human_review_fixtures.json` are synthetic test cases created specifically for software verification and algorithmic edge-case testing. They **do NOT** represent real clinical records, patient outcomes, or empirical performance validation. No empirical clinical claims are made based on these test fixtures.

---

## 2. Test Case Manifest (18 Scenarios)

| Case ID | Category | Scenario Description | Expected Trial Status | Expected Review Routing |
|:---|:---|:---|:---|:---|
| `case-01` | Automatic Eligible | Complete evidence with zero uncertainties | `ELIGIBLE` | `NOT_REQUIRED` (`ROUTINE`) |
| `case-02` | Automatic Ineligible | Disqualifying criterion with verified evidence | `INELIGIBLE` | `NOT_REQUIRED` (`ROUTINE`) |
| `case-03` | Missing Patient Fact | Missing required biomarker (HER2 status) | `NEEDS_REVIEW` | `PENDING_REVIEW` (`PRIORITY`) |
| `case-04` | Conflicting Facts | Conflicting drug allergy across EHR encounters | `NEEDS_REVIEW` | `ESCALATED` (`ESCALATED`) |
| `case-05` | Conflicting Documents | Pathology vs surgical report discordance | `NEEDS_REVIEW` | `PENDING_REVIEW` (`PRIORITY`) |
| `case-06` | Temporal Ambiguity | "Recent" chemotherapy without calendar anchor | `NEEDS_REVIEW` | `PENDING_REVIEW` (`PRIORITY`) |
| `case-07` | Numerical Ambiguity | Borderline approximated lab value (~8% HbA1c) | `NEEDS_REVIEW` | `PENDING_REVIEW` (`PRIORITY`) |
| `case-08` | Insufficient Retrieval | Retrieval engine failed to return protocol chunks | `NEEDS_REVIEW` | `PENDING_REVIEW` (`PRIORITY`) |
| `case-09` | Grounding Unsupported | Machine asserted surgical completion without evidence | `ELIGIBLE` | `PENDING_REVIEW` (`PRIORITY`) |
| `case-10` | Grounding Contradicted | Machine asserted non-smoker despite positive tobacco fact | `ELIGIBLE` | `ESCALATED` (`ESCALATED`) |
| `case-11` | Reviewer Resolves Unknown | Human reviewer resolves missing biomarker with external report | `NEEDS_REVIEW` $\rightarrow$ `RESOLVED` | `RESOLVED` |
| `case-12` | Reviewer Confirms Fail | Human reviewer verifies cardiac ejection fraction disqualification | `INELIGIBLE` $\rightarrow$ `RESOLVED` | `RESOLVED` |
| `case-13` | Reviewer Resolves to Eligible | Reviewer resolves sole unknown criterion with verified note | `NEEDS_REVIEW` $\rightarrow$ `RESOLVED` | `RESOLVED` |
| `case-14` | Reviewer Escalates | Reviewer refers complex autoimmune condition to PI | `NEEDS_REVIEW` $\rightarrow$ `ESCALATED` | `ESCALATED` |
| `case-15` | Multiple Uncertainties | Accumulation of 4 unrecorded labs triggers high triage priority | `NEEDS_REVIEW` | `PENDING_REVIEW` (`PRIORITY`) |
| `case-16` | Audit Trail Preservation | Resolved review preserves original machine reasoning immutably | `NEEDS_REVIEW` $\rightarrow$ `RESOLVED` | `RESOLVED` |
| `case-17` | Missing $\neq$ Negative | Absence of diabetes mention cannot be treated as negative fact | `NEEDS_REVIEW` | `PENDING_REVIEW` (`PRIORITY`) |
| `case-18` | Evidence Required | Reviewer override without evidence references is rejected | `NEEDS_REVIEW` | Rejected (`ValueError`) |
