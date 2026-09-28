# Phase 10: Canonical Explanation Model & Safety Guardrails

## 1. Overview & Objective

The MedMatch Explanation Model provides a **deterministic, evidence-grounded explanation framework** for clinical decision support. Its role is strictly explanatory:
- It translates verified graph paths into structured natural language justifications.
- It **never makes decisions**, alters aggregation logic, or fills missing clinical facts with generative approximations.
- In accordance with research protocol requirements, the canonical explanation path is **100% deterministic rule-based template synthesis**, completely eliminating generative LLM hallucination risks.

---

## 2. Explanation Types

- **`CRITERION_EXPLANATION`**: Explains how an individual inclusion or exclusion criterion was evaluated against patient evidence, detailing matching patient facts, source text fragments, and the resulting `PASS`, `FAIL`, or `UNKNOWN` verdict.
- **`TRIAL_DECISION_EXPLANATION`**: Explains the aggregated trial eligibility determination (`ELIGIBLE`, `INELIGIBLE`, or `NEEDS_REVIEW`) based on Phase 6 deterministic aggregation rules.
- **`UNCERTAINTY_EXPLANATION`**: Explains why an evaluation resulted in an indeterminate state, detailing the specific missing data, conflict, temporal vagueness, or retrieval deficit.
- **`REVIEW_EXPLANATION`**: Explains clinician adjudication actions, detailing reviewer decisions, supporting override evidence, and the immutable original machine output.

---

## 3. The 13 Explanation Safety Guardrails

To prevent hallucinated, misleading, or unsafe explanations, MedMatch enforces thirteen mandatory invariants:

1. **Graph Grounding Invariant**: Every factual claim in an explanation must map to an existing node in the EvidenceGraph.
2. **No Evidence $\implies$ No Definitive Claim**: If an evidence node is absent, the explanation cannot claim the condition was satisfied or refuted.
3. **Missing Evidence Represented as Uncertainty**: The absence of clinical data must be explicitly reported as missing information (`UNKNOWN`), never as a confirmed negative.
4. **Mandatory Contradiction Disclosure**: If the EvidenceGraph contains conflicting or contradicting data, the explanation must explicitly surface the contradiction; hiding conflicts is strictly prohibited.
5. **Non-Alteration of Eligibility**: Explanation generation cannot alter the trial eligibility decision status (`ELIGIBLE`, `INELIGIBLE`, `NEEDS_REVIEW`).
6. **Non-Alteration of Uncertainty**: Explanation generation cannot resolve or dismiss an active `UNCERTAINTY` node.
7. **Non-Alteration of Review Decisions**: Explanation generation cannot alter human reviewer decisions or priority states.
8. **Provenance Preservation**: All citations within an explanation must preserve valid document and fragment identifiers.
9. **Rejection of Unsupported Claims**: Any explanation containing claims with non-resolvable node IDs must be rejected with error `X9_UNSUPPORTED_EXPLANATION_CLAIM`.
10. **Machine vs. Human Distinction**: Explanations must clearly distinguish automated machine reasoning from human reviewer overrides.
11. **No Fabricated Source Locations**: Explanations must never synthesize fake line numbers, character offsets, or note headings.
12. **No Fact Fabrication**: Explanations cannot invent clinical parameters, staging details, or lab assays absent from the input profile.
13. **No Unwarranted Clinical Validation Claims**: Explanations generated during Phase 10 development are strictly development artifacts; no empirical clinical accuracy is claimed without validated benchmark ingestion.

---

## 4. Fine-Grained Explanation Claims

Every `StructuredExplanation` contains an ordered list of `ExplanationClaim` objects:

```json
{
  "claim_id": "CLM-EVAL-01-1",
  "claim_text": "Trial requires inclusion: 'Platelet count >= 100 x 10^9/L'.",
  "claim_type": "CRITERION_REQUIREMENT",
  "referenced_node_ids": ["CRIT-INC-07"],
  "is_supported_by_graph": true
}
```

This fine-grained structure allows automated auditing tools to mathematically verify the claim-level faithfulness and provenance of the generated explanation text.
