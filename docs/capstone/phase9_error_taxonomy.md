# Phase 9: Uncertainty & Human Review Error Taxonomy (U1–U12) & Safety Guardrails

## 1. Safety Guardrails

MedMatch Phase 9 enforces 12 core safety guardrails across the evaluation and adjudication pipeline:

1. **Missing $\neq$ Negative**: The absence of clinical data in a chart (`MISSING` / `NOT_MENTIONED`) must never be interpreted as confirmation of absence.
2. **Unknown $\neq$ FAIL**: An indeterminate or unevidenced criterion status (`UNKNOWN`) must never be collapsed into a definitive `FAIL` without explicit contradictory evidence.
3. **Unknown Must Not Silently Become PASS**: Missing or uncertain data can never satisfy an inclusion or clear an exclusion.
4. **Unsupported Evidence Cannot Become a Definitive Decision**: A machine reasoning statement lacking factual grounding (H1/H8) cannot generate an autonomous `ELIGIBLE` verdict.
5. **Contradicted Evidence Cannot Be Silently Ignored**: When patient or protocol facts conflict with machine claims (H6), the system must flag a contradiction and block automated approval.
6. **Reviewer Decisions Must Not Erase Machine Outputs**: Adjudication records append to the audit history; the original machine output remains immutable in `original_machine_output`.
7. **Reviewer Overrides Require Evidence**: Overriding an `UNKNOWN` to `PASS` or `FAIL` strictly requires cited evidence references.
8. **Automated Decisions Must Remain Deterministic**: Identical patient and protocol inputs must produce identical routing and priority states every time.
9. **Uncertainty Must Be Observable & Measurable**: Every uncertainty must be explicitly instantiated as an `UncertaintyRecord` with verifiable provenance.
10. **Human Review Is Mandatory Under Predefined Conditions**: When uncertainty criteria are satisfied, routing to human review cannot be bypassed by high model confidence.
11. **No Fact Fabrication**: Clinical entities, dates, and values not documented in evidence cannot be synthesized to fill gaps.
12. **No Unwarranted Clinical Validation Claims**: All Phase 9 evaluation is conducted on synthetic development fixtures; no empirical clinical performance is claimed.

---

## 2. Phase 9 Error Taxonomy (U1–U12)

| Error Code | Error Category | Operational Definition | Research Impact | Detection Mechanism |
|:---|:---|:---|:---|:---|
| **U1** | Missing Required Information | A required clinical criterion cannot be evaluated because the patient chart omits the necessary biomarker, stage, or lab. | Prevents automated eligibility determination. | Evaluator detects `NOT_MENTIONED` in patient facts for a mandatory criterion. |
| **U2** | Conflicting Evidence | Two or more clinical records or document sections assert incompatible values or statuses. | Compromises factual integrity of premise. | `UncertaintyStatus == CONFLICTING` detected with $\ge 2$ discrepant items. |
| **U3** | Temporal Ambiguity | Clinical milestone lacks an absolute date or uses imprecise relative phrasing (e.g., "recently"), preventing window verification. | Timeframe eligibility indeterminate. | `TemporalityType == RELATIVE_INTERVAL` or missing anchor date on timed criterion. |
| **U4** | Numerical Ambiguity | Lab measurement is borderline, lacks units, or has mismatched assay reference ranges. | Quantitative threshold satisfaction in doubt. | Value within measurement tolerance or missing unit comparison. |
| **U5** | Insufficient Retrieval Evidence | Retrieval engine returns zero chunks or low similarity scores for a protocol criterion. | Reasoner operates with partial protocol context. | Retriever returns empty chunk list or score $< \tau_{\text{retrieval}}$. |
| **U6** | Unsupported Machine Inference | Automated reasoning extrapolates clinical conclusions without source backing (H5/H8). | Hallucination hazard; invalid eligibility verdict. | Phase 8 claim extractor marks conclusion claim `UNSUPPORTED`. |
| **U7** | Grounding Contradiction | Automated reasoning directly contradicts recorded patient facts or protocol text (H6). | Major factual hallucination. | Phase 8 claim extractor marks claim `CONTRADICTED`. |
| **U8** | Incorrect Automatic Decision Despite Uncertainty | System produces an autonomous `ELIGIBLE` or `INELIGIBLE` verdict while unresolved high-severity uncertainty exists. | Guardrail violation; ungrounded autonomous decision. | Routing validator detects `NOT_REQUIRED` while `unresolved_count > 0`. |
| **U9** | Incorrect Review Routing | System fails to route an uncertain case to `PENDING_REVIEW` or assigns an inappropriate triage priority. | Workflow routing failure. | Routing policy output does not match expected state. |
| **U10** | Incorrect Reviewer Resolution Handling | Reviewer resolution attempts to re-resolve an already completed review or omits mandatory decision rationale. | State machine integrity violation. | State validator rejects invalid transition. |
| **U11** | Lost Audit History | Machine output is overwritten by human decision, or audit event sequence is incomplete. | Regulatory compliance failure; non-reproducibility. | Audit trail validation detects missing initial snapshot or broken event links. |
| **U12** | Unsupported Reviewer Decision | Human reviewer overrides an `UNKNOWN` to `PASS` or `FAIL` without supplying supporting evidence citations. | Subjective / unverified human override. | Resolution manager detects `len(evidence_references) == 0` on override. |
