# MedMatch Phase 10 Development Fixtures

## Non-Clinical Validation Notice

> [!IMPORTANT]
> The fixtures in this directory are **synthetic, non-PHI development and regression test artifacts** constructed exclusively for validating the Phase 10 Evidence Graph, Explanation Generator, and Explainability Validator.
>
> They do **not** represent real hospital patient records, real clinical trial protocols, or clinically validated decision rules.
>
> In accordance with the MedMatch Capstone Research Protocol, empirical clinical performance claims are strictly prohibited until a validated external research benchmark with clinical ground-truth labels is formally ingested (`has_validated_benchmark() == False`).

---

## Fixture Catalog (18 Canonical Scenarios)

1. `case-01-pass-criterion-direct-evidence`: Single inclusion criterion evaluated as `PASS` with direct supporting patient fact and note fragment.
2. `case-02-fail-criterion-direct-evidence`: Disqualifying exclusion criterion evaluated as `FAIL` with direct contradictory clinical evidence.
3. `case-03-unknown-missing-information`: Criterion evaluated as `UNKNOWN` due to unrecorded biomarker, linked to `MISSING_PATIENT_FACT` uncertainty.
4. `case-04-multiple-evidence-fragments`: Criterion supported by multiple concurrent source fragments across different clinical notes.
5. `case-05-contradictory-evidence`: Criterion with conflicting clinical evidence across separate pathology and clinical intake records.
6. `case-06-temporal-criterion-explicit-date`: Criterion with explicit temporal constraint (washout window) verified by dated clinical note.
7. `case-07-numerical-criterion-source-evidence`: Lab criterion evaluated against quantitative assay value and unit from laboratory report.
8. `case-08-retrieval-result-linked`: Candidate trial retrieval result (rank, similarity score, method) linked to retrieved protocol criterion.
9. `case-09-trial-decision-linked-all-evals`: Complete trial-level aggregation (`ELIGIBLE`) linked to all contributing criterion evaluations via `CONTRIBUTES_TO`.
10. `case-10-uncertainty-linked-to-criterion`: High-severity uncertainty linked to criterion evaluation via `HAS_UNCERTAINTY`.
11. `case-11-human-review-linked-uncertainty`: Review case queued for clinician review (`PENDING_REVIEW`) triggered by uncertainty.
12. `case-12-reviewer-resolution-linked-evidence`: Human reviewer resolution overriding machine `UNKNOWN` to `PASS` supported by cited outside pathology.
13. `case-13-complete-end-to-end-graph`: Complete unbroken graph traversing from Patient -> Notes -> Fragments -> Facts -> Criteria -> Retrieval -> Evaluations -> Uncertainty -> Review -> Decision -> Explanation.
14. `case-14-invalid-dangling-reference`: Intentionally corrupted graph containing an edge with a dangling non-existent target ID (tests G9 / X3).
15. `case-15-invalid-fabricated-provenance`: Intentionally corrupted graph containing fabricated character offsets (`start_char > end_char` and `< -1`) (tests G3 / G10 / X2 / X13).
16. `case-16-invalid-unsupported-explanation-claim`: Valid graph paired with an explanation asserting an ungrounded hallucinated fact not present in the graph (tests X9).
17. `case-17-multiple-retrieval-methods`: Graph demonstrating candidate criteria retrieved across multiple distinct retrieval algorithms (Dense, BM25, Hybrid RRF).
18. `case-18-machine-output-preserved-after-review`: Graph verifying that a reviewer override preserves the original machine output immutably in `original_machine_output` (tests G8 / X11).
