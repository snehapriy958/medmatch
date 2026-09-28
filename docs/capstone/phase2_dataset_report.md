# MedMatch Capstone — Phase 2: Dataset + Ground Truth Report (Revised)

> **Phase Status:** IN PROGRESS (Corrections Applied & Verified)  
> **Phase:** 2 — Dataset + Ground Truth  
> **Dataset Classification:** **DEVELOPMENT / TEST FIXTURE ONLY — NOT A RESEARCH EVALUATION BENCHMARK**  
> **Dataset Version:** `0.1.0-fixture`  
> **Date:** September 2026  
> **Target System:** MedMatch Clinical Decision-Support Prototype

---

## 1. Summary of Corrections Applied

In response to capstone review requirements, the Phase 2 data architecture was refined to ensure complete scientific transparency, rigorous layer separation, and precise source attribution:

1. **Clarified Fixture vs. Final Benchmark:** The current local dataset (1 trial, 6 synthetic patients, 8 criteria, 6 decisions) is explicitly classified as a **Phase 2 development/test fixture** for testing schemas, referential integrity, and automated validators. It is explicitly **NOT the final research evaluation benchmark**.
2. **Separated Three Distinct Dataset Layers:** Formally distinguished between:
   - `development_fixture` (tiny deterministic synthetic fixture for testing)
   - `research_benchmark` (external public benchmarks; status: `SOURCE IDENTIFIED — NOT YET INGESTED`)
   - `stress_test` (synthetic edge-case subset for boundary, temporal, missing info, and contradiction testing)
3. **Corrected Split Methodology:** The 6-patient partition is explicitly labeled `TEST FIXTURE ONLY` across `data/splits/train.jsonl`, `validation.jsonl`, and `test.jsonl`. It is documented as a structural test partition for validator verification, not a statistically meaningful 60/20/20 research split.
4. **Separated Stress Tests from Primary Test Set:** The 4 synthetic edge-case scenarios (`missing_information`, `conflicting_evidence`, `boundary_condition`, `temporal_washout`) are isolated into a dedicated evaluation file `data/splits/stress_test.jsonl` rather than conflated with standard benchmark distributions.
5. **Verified External Source Status:** All external datasets (ClinicalTrials.gov API, TrialGPT, TREC Clinical Trials) are explicitly marked as **`SOURCE IDENTIFIED — NOT YET INGESTED`**.
6. **Clarified Label Capabilities:** Explicitly documented that TREC Clinical Trials provides retrieval relevance qrels only (no criterion labels or text spans), TrialGPT provides criterion-level annotations for a subset (~2.5%) of pairs, and ClinicalTrials.gov contains zero patient data.
7. **Preserved All Test Suites:** Verified that 100% of dataset tests (17 tests) and all production AI-service regression tests (45 tests) pass.
8. **Phase 2 Maintained:** Phase 2 remains the active phase; Phase 3 has not been started.

---

## 2. Exact External Datasets Investigated & Ingestion Status

| Dataset / Source | Official Authority & Identifier | Ingestion Status | Labels Actually Contained | Supported Task | License / Access Terms | Redistribution Permitted? |
|---|---|:---:|---|---|---|:---:|
| **ClinicalTrials.gov REST API v2** | NLM / NIH; `clinicaltrials.gov/api/v2/studies` | `SOURCE IDENTIFIED — NOT YET INGESTED` *(1 protocol template in fixture)* | Protocol text, eligibility criteria blocks, phase, conditions. **Zero patient records, zero eligibility labels.** | Protocol indexing & criteria text parsing | Public Domain (U.S. Gov) | Yes (Unrestricted) |
| **TrialGPT Benchmark Cohort** | Qiao Jin et al., *Nature Communications* (2024); GitHub: `ncbi-nlp/TrialGPT`, HF: `ncbi/TrialGPT-Criterion-Annotations` | `SOURCE IDENTIFIED — NOT YET INGESTED` | 184 synthetic EHR case summaries; criterion-level clinician annotations (`meets`, `fails`, `not mentioned`) for ~1,200 pairs (~2.5% of total pairs); aggregated trial-level decisions | Criterion tri-state reasoning (`PASS`/`FAIL`/`UNKNOWN`) and grounding | Public Domain (NIH) / MIT | Yes (Unrestricted academic reuse) |
| **TREC Clinical Trials 2021 Track** | NIST / OHSU; `trec-cds.org/2021.html` | `SOURCE IDENTIFIED — NOT YET INGESTED` | 75 synthetic/semi-synthetic case topics; retrieval relevance qrels (0, 1, 2). **No criterion-level labels or character text spans.** | Candidate retrieval evaluation (Recall@K, MRR, nDCG@K) | Open Academic (NIST terms) | Yes (Permitted for research) |
| **TREC Clinical Trials 2022 Track** | NIST / OHSU; `trec-cds.org/2022.html` | `SOURCE IDENTIFIED — NOT YET INGESTED` | 50 case topics; retrieval relevance qrels (0, 1, 2). **No criterion-level labels.** | Candidate retrieval evaluation | Open Academic (NIST terms) | Yes (Permitted for research) |
| **MIMIC-IV Clinical Database** | MIT / PhysioNet; `physionet.org/content/mimiciv` | `REJECTED — NOT SUITABLE` | Real de-identified inpatient EHR data. **Zero trial screening ground truth.** | None | PhysioNet Credentialed DUA | No (Prohibited in Git) |

---

## 3. Exact Current Fixture Size (`development_fixture`)

The local development test fixture under `data/fixtures/` contains:
- **Clinical Trials:** 1 Protocol (Curated NSCLC Phase 3 Benchmark, NCT02484404)
- **Patient Encounters:** 6 Canonical Synthetic Encounters (`SYN_P001` through `SYN_P006`)
- **Protocol Criteria:** 8 Atomic Criteria (5 Inclusion, 3 Exclusion)
- **Criterion-Level Ground Truth:** 48 Evaluated Pairs (40 `PASS`, 5 `FAIL`, 3 `UNKNOWN` with character-level text spans)
- **Trial-Level Ground Truth:** 6 Aggregated Decisions (1 `ELIGIBLE`, 3 `INELIGIBLE`, 2 `NEEDS_REVIEW`)

---

## 4. Exact Research Benchmark Status (`research_benchmark`)

- **Current Status:** `SOURCE IDENTIFIED — NOT YET INGESTED`
- **Ingested Records:** 0 external patient records, 0 external trial protocols committed.
- **Next Steps for Research Benchmark:** Ingestion scripts will be implemented in subsequent phases to download and normalize the verified TrialGPT HuggingFace dataset and TREC Clinical Trials topics into canonical schemas.

---

## 5. Exact Stress-Test Status (`stress_test`)

- **Current Status:** `LOCAL FIXTURE IMPLEMENTED`
- **Location:** `data/splits/stress_test.jsonl`
- **Composition (4 Scenarios):**
  1. `SYN_P003`: Missing information (EGFR pending, brain MRI omitted) $\implies \text{NEEDS\_REVIEW}$ (tests conservative uncertainty).
  2. `SYN_P004`: Conflicting evidence (tissue positive vs. liquid negative) $\implies \text{NEEDS\_REVIEW}$ (tests contradiction detection).
  3. `SYN_P005`: Boundary condition (Platelets = 99 vs. $\ge 100 \times 10^9/\text{L}$) $\implies \text{INELIGIBLE}$ (tests numerical inequality reasoning).
  4. `SYN_P006`: Temporal washout condition (Chemo completed 27 days vs. $\ge 28$ days required) $\implies \text{INELIGIBLE}$ (tests temporal arithmetic).

---

## 6. Validation Results

Execution of `python scripts/validate_dataset.py --data-dir data`:

```text
--> Validating fixtures in data\fixtures...
--> Validating splits in data\splits...

==================================================
VALIDATION SUMMARY: 0 errors, 0 warnings
==================================================
[PASS] All dataset integrity and schema validations succeeded.
```

- Referential integrity: 100% verified (no orphan foreign keys).
- Character offsets: 100% verified against verbatim patient notes.
- Deterministic clinical aggregation: 100% verified against clinical rules.
- Split disjointness: 100% verified (zero patient leakage across train, validation, and test).

---

## 7. Test Results

### 7.1 Dataset Test Suite (`tests/dataset/`)
Command: `python -m pytest tests/dataset -v`
- **Total Tests:** 17
- **Passed:** 17 (100%)
- **Failed:** 0
- **Duration:** 0.25 seconds

### 7.2 Production AI-Service Test Suite (`services/ai-service/tests/`)
Command: `python -m pytest tests -v` (in `services/ai-service`)
- **Total Tests:** 45
- **Passed:** 45 (100%)
- **Failed:** 0
- **Duration:** 54.81 seconds
- **Production Integrity:** Production matching service and routes remain completely untouched.

---

## 8. Files Modified and Created

### Documentation Files Updated
- `docs/capstone/dataset_source_audit.md` (Updated with explicit source acquisition statuses and label capability breakdowns)
- `docs/capstone/dataset_card.md` (Updated with layer classifications, fixture disclaimers, and external source statuses)
- `docs/capstone/dataset_statistics.md` (Updated with development fixture notices and stress-test separation)
- `docs/capstone/phase2_dataset_report.md` (This comprehensive revision report)
- `docs/capstone/PHASE_STATUS.md` (Kept at Phase 2; Phase 3 not started)

### Data Infrastructure & Split Files
- `data/README.md` (Updated with layer distinctions and split methodology clarifications)
- `data/manifests/dataset_manifest.json` (Updated with 3-layer architecture and source acquisition statuses)
- `data/manifests/checksums.sha256` (Recomputed SHA-256 checksums across all 10 tracked data files)
- `data/splits/train.jsonl` (Updated with `TEST FIXTURE ONLY` classification)
- `data/splits/validation.jsonl` (Updated with `TEST FIXTURE ONLY` classification)
- `data/splits/test.jsonl` (Updated with `TEST FIXTURE ONLY` classification)
- `data/splits/stress_test.jsonl` (Created dedicated stress-test evaluation subset)

### Scripts and Tests
- `scripts/dataset_schema.py` (Canonical Pydantic models and deterministic clinical aggregation logic)
- `scripts/validate_dataset.py` (Automated quality and integrity validator)
- `scripts/data_generation/generate_synthetic_patients.py` (Procedural generator for controlled scenarios)
- `tests/dataset/test_schema.py` (Unit tests for schemas and aggregation)
- `tests/dataset/test_integrity.py` (Unit tests for referential integrity and character spans)
- `tests/dataset/test_splits.py` (Unit tests for split disjointness, stress-test isolation, and classification labels)
- `tests/dataset/test_fixture.py` (Unit tests for scenario representation and checksum integrity)

---

## 9. Current Phase Status

```text
PHASE 0 — CURRENT SYSTEM AUDIT
STATUS: COMPLETE

PHASE 1 — RESEARCH PROBLEM + EVALUATION DESIGN
STATUS: COMPLETE

PHASE 2 — DATASET + GROUND TRUTH
STATUS: CORRECTIONS COMPLETE — AWAITING USER ACCEPTANCE

Next phase:
PHASE 3 — CLINICAL TRIAL DOCUMENT INTELLIGENCE (Not started)
```
