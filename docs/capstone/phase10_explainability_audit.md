# Phase 10: Explainability & Evidence Graph Foundation Audit

## 1. Executive Summary & Objective

Phase 10 addresses the fundamental clinical requirement for **interpretability, auditability, and end-to-end provenance** in the MedMatch clinical decision support system. Prior phases established:
- High-fidelity clinical trial document intelligence (Phase 3)
- Patient clinical profile extraction with provenance (Phase 4)
- Multi-method candidate trial retrieval (Phase 5)
- Three-valued criterion reasoning and deterministic trial aggregation (Phase 6)
- RAG vs. Non-RAG experimental evaluations (Phase 7)
- Evidence grounding, citation verification, and hallucination evaluation (Phase 8)
- Formal uncertainty models and human-in-the-loop review routing (Phase 9)

Despite these strong foundations, prior representations remained **siloed across distinct data structures**. An auditor or clinician attempting to verify why a patient was deemed ineligible, or why a case was routed to human review, had to manually correlate fragmented records across clinical notes, retrieval runs, reasoning logs, claim extraction records, and review audit trails.

The objective of Phase 10 is to build a **canonical, typed Evidence Graph and deterministic Explanation Framework** that unifies the entire decision pathway into an unbroken, auditable chain of evidence:

$$\text{Patient Fact} \longrightarrow \text{Source Fragment} \longrightarrow \text{Retrieved Criterion} \longrightarrow \text{Criterion Evaluation} \longrightarrow \text{Eligibility Decision} \longrightarrow \text{Explanation}$$

$$\text{Machine Decision} \longrightarrow \text{Uncertainty} \longrightarrow \text{Review Request} \longrightarrow \text{Reviewer Evidence} \longrightarrow \text{Resolution} \longrightarrow \text{Final State}$$

---

## 2. Upstream Phase Audit & Provenance Surface

| Phase | Core Abstraction | Provenance Captured | Formats & Conventions | Traceability Gaps Prior to Phase 10 |
|:---|:---|:---|:---|:---|
| **Phase 3** | `TrialCriterion`, `CriterionProvenance` | `document_id`, `trial_id`, `section_id`, `page_number`, `start_char`, `end_char`, `source_text`, `extraction_version`. | 0-based character offsets; `-1` for unlocatable spans; 1-based page numbers. | Criterion records existed independently of patient facts; no direct link to patient records. |
| **Phase 4** | `ClinicalFact`, `FactProvenance` | `note_id`, `patient_id`, `source_text`, `start_char`, `end_char`, `source_section`, `extraction_timestamp`, `model_identifier`. | 0-based offsets; `-1` for missing; assertion status (`PRESENT`, `ABSENT`, `UNCERTAIN`, `NOT_MENTIONED`). | Patient facts did not reference the trial criteria they were evaluated against. |
| **Phase 5** | `RetrievalResult`, `RetrievalResponse` | `trial_id`, `criterion_id`, `rank`, `score`, `method` (`dense`, `bm25`, `hybrid_rrf`, `hybrid_reranked`), `tenant_id`. | Ranks 1 to $k$; normalized scores $[0, 1]$; strategy enums. | Retrieval candidate scores were detached from downstream reasoning justifications. |
| **Phase 6** | `CriterionEvaluationRecord`, `TrialEligibilityEvaluation` | `criterion_id`, `trial_id`, `status` (`PASS`, `FAIL`, `UNKNOWN`), `evidence_citations`, `patient_fact_references`, `reasoning`. | Three-valued logic; deterministic aggregation (`ELIGIBLE`, `INELIGIBLE`, `NEEDS_REVIEW`). | Citations and fact IDs were stored as flat string lists rather than navigable graph relations. |
| **Phase 7** | `NonRAGExperimentRunner`, `RAGExperimentRunner` | Information boundary: E5 (no retrieved passages) vs E6/E7/E8 (dense, hybrid, reranked passages). | Controlled ablation comparisons; provenance metadata attached to experiment runs. | Ablation results measured batch metrics without an explorable per-instance evidence path. |
| **Phase 8** | `GroundingEvaluation`, `GroundingClaim`, `CitationValidationRecord` | `claim_id`, `claim_text`, `claim_type`, `support_status` (`SUPPORTED`, `UNSUPPORTED`, `CONTRADICTED`), `hallucination_category` (H1–H10). | Fine-grained token/sentence propositions; citation resolution checks. | Verified claims and hallucination flags were diagnostic reports, not integrated into the final explanation graph. |
| **Phase 9** | `UncertaintyRecord`, `HumanReviewRecord`, `ReviewAuditTrail` | `uncertainty_id`, `severity`, `uncertainty_type`, `review_id`, `reviewer_decision`, `evidence_references`, `original_machine_output`. | Append-only event history; immutability of machine decisions; strict override evidence citations. | Reviewer overrides and machine baseline states were recorded in audit logs but lacked explicit graph edges connecting review decisions to the specific criteria and trial conclusions they modified. |

---

## 3. Key Identification of Traceability Gaps

1. **Disconnected Reference Chains**:
   In Phase 6, `CriterionEvaluationRecord.patient_fact_references` references strings like `"fact_001"`, while `evidence_citations` contains inline text. Neither was validated against a graph schema to guarantee referential integrity.
2. **Missing Bi-directional Traversal**:
   Given a final `INELIGIBLE` verdict, a clinician cannot traverse backwards through an API to immediately answer: "Which specific snippet of which clinical note caused this exclusion, which retrieval method found the exclusion criterion, and did any other note contradict it?"
3. **Black-box Natural Language Reasoning**:
   The `reasoning` field in `CriterionEvaluationRecord` was freeform text generated by rules or prompts. Without a formal explanation model, explanations could assert facts not present in either the patient record or the protocol.
4. **Human Review Disconnection**:
   Phase 9 recorded human overrides and cited evidence in `HumanReviewRecord.evidence_references`, but there was no explicit graph structure representing how human evidence supersedes or supplements machine evidence while keeping the machine graph immutable.

---

## 4. Architectural Requirements for Phase 10

To solve these gaps, Phase 10 establishes:
1. **Canonical Evidence Graph Schema (`scripts/evidence_graph_schema.py`)**:
   - 13 strongly-typed node types (`PATIENT`, `PATIENT_FACT`, `SOURCE_DOCUMENT`, `SOURCE_FRAGMENT`, `TRIAL`, `TRIAL_CRITERION`, `RETRIEVAL_RESULT`, `CRITERION_EVALUATION`, `ELIGIBILITY_DECISION`, `UNCERTAINTY`, `REVIEW`, `REVIEW_RESOLUTION`, `EXPLANATION`).
   - 16 strongly-typed edge relations (`HAS_FACT`, `DERIVED_FROM`, `BELONGS_TO`, `HAS_CRITERION`, `SUPPORTS`, `CONTRADICTS`, `CONTEXTUALIZES`, `EVALUATED_BY`, `RETRIEVED_CRITERION`, `RETRIEVED_FROM`, `CONTRIBUTES_TO`, `HAS_UNCERTAINTY`, `TRIGGERS`, `RESOLVED_BY`, `SUPPORTED_BY`, `EXPLAINS`).
2. **Graph Construction Engine (`scripts/evidence_graph_builder.py`)**:
   - Deterministic assembly from Phase 3–9 canonical outputs.
3. **Graph Integrity Validator (`scripts/evidence_graph_validator.py`)**:
   - Enforces 12 graph invariants (G1–G12) and categorizes structural/referential failures (X1–X14).
4. **Deterministic Explanation Generator (`scripts/explanation_generator.py`)**:
   - Generates structured, evidence-grounded explanations directly from graph facts with zero LLM hallucination risk.
5. **Explanation Validator (`scripts/explanation_validator.py`)**:
   - Validates that every explanation claim maps to graph evidence, discloses contradictions, and preserves machine decisions.
6. **Explainability Metrics Engine (`scripts/explainability_metrics.py`)**:
   - Formal mathematical metrics (EC, DTR, CTR, PVR, ESR, UECR, CDR, GIR) with strict zero-denominator safeguards.
7. **Empirical Benchmark Guardrail**:
   - Strict `has_validated_benchmark() == False` enforcement; research validation only.
