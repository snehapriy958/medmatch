# Phase 10: Canonical Evidence Graph Specification

## 1. Objective & Scope

The MedMatch Evidence Graph provides a **canonical, typed, and navigable graph representation** uniting patient clinical data, clinical trial protocols, retrieval provenance, criterion-level evaluations, trial-level eligibility aggregations, epistemic uncertainties, and human review decisions.

Its purpose is to make automated clinical trial matching **fully transparent, reconstructible, and auditable** by clinicians and regulatory oversight bodies.

---

## 2. Graph Invariants (G1–G12)

Every compliant MedMatch Evidence Graph must strictly satisfy twelve structural and semantic invariants:

- **G1: Criterion Referential Integrity**: Every `CRITERION_EVALUATION` node must reference a valid `TRIAL_CRITERION` node via an incoming `EVALUATED_BY` edge.
- **G2: Evidence Requirement for Definite Verdicts**: Every `CRITERION_EVALUATION` with status `PASS` or `FAIL` must have at least one incoming `SUPPORTS` or `CONTRADICTS` edge from a `PATIENT_FACT` or `SOURCE_FRAGMENT`.
- **G3: Source Provenance**: Every evidence-bearing node (`SOURCE_FRAGMENT`, `PATIENT_FACT`) must possess valid provenance (`source_id`, `document_id`, offsets $\ge -1$, and $start \le end$ when offsets are locatable).
- **G4: Decision Traceability**: Every `ELIGIBILITY_DECISION` node must be linked from all contributing `CRITERION_EVALUATION` nodes via incoming `CONTRIBUTES_TO` edges.
- **G5: Uncertainty Attribution**: Every `UNCERTAINTY` node must be connected from the affected `CRITERION_EVALUATION` or `PATIENT_FACT` via an incoming `HAS_UNCERTAINTY` edge.
- **G6: Review Trigger Traceability**: Every `REVIEW` node must be triggered by an `UNCERTAINTY` node via an incoming `TRIGGERS` edge.
- **G7: Review Resolution Integrity**: Every `REVIEW_RESOLUTION` node must be linked from a `REVIEW` node via an incoming `RESOLVED_BY` edge.
- **G8: Immutability of Machine Reasoning**: Every `REVIEW_RESOLUTION` node must preserve the original automated reasoning state in its `original_machine_output` property. Overrides cannot erase the machine baseline.
- **G9: No Dangling References**: All edge `source_id` and `target_id` references must resolve to existing nodes within the graph.
- **G10: Non-Fabrication of Source Locations**: Character offsets must represent actual substring coordinates or explicitly use `-1` when unlocatable. Arbitrary or negative values $< -1$ are strictly prohibited.
- **G11: Unique Node and Edge Identifiers**: All `node_id` and `edge_id` values within a graph instance must be unique.
- **G12: Semantic Round-Trip Equivalence**: Serializing an EvidenceGraph to JSON and deserializing it must yield identical nodes, edges, properties, and provenance metadata.

---

## 3. Node Taxonomy (13 Canonical Node Types)

| Node Type | Canonical Prefix | Semantic Scope | Key Properties |
|:---|:---|:---|:---|
| `PATIENT` | `PAT-` | Root patient identity | `patient_id` |
| `PATIENT_FACT` | `FACT-` | Atomic extracted clinical fact | `fact_id`, `concept`, `value`, `assertion`, `temporality` |
| `SOURCE_DOCUMENT` | `DOC-` | Original medical record or protocol | `document_id`, `document_type` |
| `SOURCE_FRAGMENT` | `FRAG-` | Verbatim text span in source document | `text`, `provenance` (`document_id`, `start_char`, `end_char`, `page_number`) |
| `TRIAL` | `TRIAL-` | Clinical trial protocol root | `trial_id` |
| `TRIAL_CRITERION` | `CRIT-` | Individual eligibility criterion | `criterion_id`, `criterion_type`, `criterion_text`, `domain` |
| `RETRIEVAL_RESULT` | `RET-` | Candidate passage or trial retrieval | `retrieval_id`, `rank`, `score`, `method` |
| `CRITERION_EVALUATION` | `EVAL-` | Atomic evaluation of a single criterion | `evaluation_id`, `criterion_id`, `status` (`PASS`, `FAIL`, `UNKNOWN`), `reasoning` |
| `ELIGIBILITY_DECISION` | `DEC-` | Aggregated trial eligibility status | `decision_id`, `status` (`ELIGIBLE`, `INELIGIBLE`, `NEEDS_REVIEW`), `clinical_summary` |
| `UNCERTAINTY` | `UNC-` | Formal clinical/epistemic uncertainty | `uncertainty_id`, `uncertainty_type`, `severity`, `description` |
| `REVIEW` | `REV-` | Clinical human review workflow record | `review_id`, `status`, `priority` |
| `REVIEW_RESOLUTION` | `RES-` | Adjudicated human decision & override | `resolution_id`, `reviewer_id`, `decision`, `rationale`, `original_machine_output` |
| `EXPLANATION` | `EXP-` | Structured natural language explanation | `explanation_id`, `explanation_type`, `decision_reference`, `claims` |

---

## 4. Edge Taxonomy (16 Canonical Relational Links)

```text
PATIENT
  └── HAS_FACT ───────────────> PATIENT_FACT
                                    │
                                    ├── DERIVED_FROM ──────────> SOURCE_FRAGMENT ──> BELONGS_TO ──> SOURCE_DOCUMENT
                                    │
                                    ├── SUPPORTS / CONTRADICTS
                                    │         │
                                    │         ▼
TRIAL ──> HAS_CRITERION ──> TRIAL_CRITERION ──> EVALUATED_BY ──> CRITERION_EVALUATION ──> CONTRIBUTES_TO ──> ELIGIBILITY_DECISION
                                 ▲                                    │
                                 │                                    ├── HAS_UNCERTAINTY ──> UNCERTAINTY ──> TRIGGERS ──> REVIEW
RETRIEVAL_RESULT ────────────────┘                                    │                                                      │
        │                                                             │                                                      ▼
        └── RETRIEVED_FROM ──> TRIAL / DOC                            │                                              REVIEW_RESOLUTION
                                                                      │                                                      │
                                                                      ▼                                                      ├── SUPPORTED_BY ──> FRAG / FACT
                                                                 EXPLANATION <───────────────────────────────────────────────┘
```

---

## 5. Provenance Representation Rules

1. **Character Offsets**:
   - `start_char` and `end_char` are 0-based character offsets into the verbatim text of `document_id`.
   - If offsets cannot be reliably extracted (e.g. from structured tables or scanned summaries), both must be set to `-1`.
   - Never fabricate or guess offsets.
2. **Page Numbers**:
   - 1-based page numbers are recorded when the source document is paginated (e.g. protocol PDFs).
3. **Retrieval Provenance**:
   - Every `RETRIEVAL_RESULT` node must record `retrieval_method` (`dense`, `lexical_bm25`, `hybrid_rrf`, `hybrid_reranked`), `retrieval_rank` ($\ge 1$), and `retrieval_score`.
