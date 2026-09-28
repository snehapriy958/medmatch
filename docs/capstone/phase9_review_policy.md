# Phase 9: Review-Routing Policy & Uncertainty Propagation

## 1. Overview

The MedMatch Review-Routing Policy dictates when automated eligibility reasoning may proceed autonomously and when cases **must** be intercepted and routed to human clinical review.

The policy strictly prevents automated decision-making when:
1. Patient information is missing.
2. Clinical records conflict.
3. Temporal or numerical bounds are ambiguous.
4. Retrieval evidence is incomplete.
5. Automated reasoning generates ungrounded or contradicted claims.
6. Unsupported certainty is expressed.

---

## 2. Uncertainty Propagation Flow

Uncertainty propagates deterministically from atomic patient and protocol evidence up to the human review decision:

```text
  [Patient Fact Uncertainty (Phase 4)]
  (MISSING, CONFLICTING, AMBIGUOUS, STALE)
                  │
                  ▼
  [Retrieved Evidence Uncertainty (Phase 5)]
  (INSUFFICIENT_RETRIEVAL, LOW_CONFIDENCE)
                  │
                  ▼
  [Criterion-Level Reasoning (Phase 6)]
  (PASS, FAIL, UNKNOWN)
                  │
                  ▼
  [Grounding & Faithfulness Auditing (Phase 8)]
  (SUPPORTED, UNSUPPORTED, CONTRADICTED)
                  │
                  ▼
  [Trial-Level Aggregation (Phase 6 / 9)]
  (ELIGIBLE, INELIGIBLE, NEEDS_REVIEW)
                  │
                  ▼
  [Review Routing & Triage (Phase 9)]
  (NOT_REQUIRED, PENDING_REVIEW, ESCALATED)
```

---

## 3. Decision Matrix

| Trial Machine Verdict | Uncertainty State | Grounding State | Routed Status | Priority | Permitted Automated Action |
|:---|:---|:---|:---|:---|:---|
| `ELIGIBLE` | Zero unresolved | All `SUPPORTED` | `NOT_REQUIRED` | `ROUTINE` | **Autonomous Enrollment Permitted** |
| `ELIGIBLE` | $\ge 1$ unresolved | Any status | `PENDING_REVIEW` | `PRIORITY` | **Blocked**: Requires clinician confirmation |
| `ELIGIBLE` | Any | $\ge 1$ `UNSUPPORTED` / `CONTRADICTED` | `PENDING_REVIEW` / `ESCALATED` | `PRIORITY` / `ESCALATED` | **Blocked**: Machine hallucination intercepted |
| `INELIGIBLE` | Zero conflicting on failing criterion | Failing criterion `SUPPORTED` | `NOT_REQUIRED` | `ROUTINE` | **Autonomous Ineligibility Permitted** |
| `INELIGIBLE` | Failing criterion has conflict/ambiguity | Disputed evidence | `PENDING_REVIEW` | `PRIORITY` | **Blocked**: Disqualification in doubt |
| `NEEDS_REVIEW` | $\ge 1$ `UNKNOWN` criterion | Any status | `PENDING_REVIEW` | `ROUTINE` or `PRIORITY` | **Blocked**: Requires human review |
| Any | Critical safety conflict | Any status | `ESCALATED` | `ESCALATED` | **Blocked**: Escalated to specialist review |
| Any | Any | $\ge 1$ `CONTRADICTED` claim (H6) | `ESCALATED` | `ESCALATED` | **Blocked**: Contradiction alert |

---

## 4. Guardrail Rules

1. **Missing $\neq$ Negative**: The absence of a mention in a chart (`MISSING` / `NOT_MENTIONED`) can never be treated as negative evidence to pass an exclusion or fail an inclusion.
2. **Confidence Cannot Override Evidence**: A high model confidence value (e.g. 0.99) cannot bypass routing if required facts are unrecorded.
3. **No Overwrite**: Routing to human review creates a `HumanReviewRecord` containing an immutable copy of the machine output.
