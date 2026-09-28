# MedMatch Capstone — Dataset Statistics & Layer Distribution

> **Status:** Phase 2 Development/Test Fixture Audit  
> **Phase:** 2 — Dataset + Ground Truth  
> **Dataset Classification:** **DEVELOPMENT / TEST FIXTURE ONLY — NOT A RESEARCH EVALUATION BENCHMARK**  
> **Dataset Version:** `0.1.0-fixture`  
> **Date:** September 2026  
> **Target System:** MedMatch Clinical Decision-Support Prototype

---

## 1. Scope Disclaimer: Development Fixture vs. Research Benchmark

> [!WARNING]
> **DEVELOPMENT FIXTURE STATUS:**  
> The statistics presented below describe the **Phase 2 development/test fixture** (1 trial, 6 synthetic patients, 8 criteria, 48 criterion-level evaluations, and 6 trial decisions).  
> **This fixture is NOT the final research evaluation benchmark.** It is designed exclusively for testing data schemas, validating referential integrity, and running automated regression suites. It does not provide statistical power for measuring clinical matching performance.

---

## 2. Three Dataset Layers Breakdown

```text
+---------------------------------------------------------------------------------------------------------+
|                                      DATASET LAYER STATUS & COUNTS                                      |
+----------------------+------------------------------------+-----------------------+---------------------+
| Layer Name           | Scope / Description                | Current Status        | Ingested Count      |
+----------------------+------------------------------------+-----------------------+---------------------+
| development_fixture  | Tiny deterministic synthetic       | IMPLEMENTED           | 1 trial, 6 patients |
|                      | fixture for CI/CD & testing        |                       | 48 criterion labels |
|                      |                                    |                       | 6 trial labels      |
| research_benchmark   | External public benchmark corpus   | SOURCE IDENTIFIED —   | 0 patients ingested |
|                      | (TrialGPT, TREC Clinical Trials)   | NOT YET INGESTED      | 0 trials ingested   |
| stress_test          | Dedicated synthetic edge cases     | IMPLEMENTED SUBSET    | 4 stress scenarios  |
|                      | (boundary, temporal, missing, etc.)|                       | (data/splits/)      |
+----------------------+------------------------------------+-----------------------+---------------------+
```

---

## 3. Development Test Fixture Statistics

### 3.1 Overall Corpus Composition
- **Total Clinical Trials:** 1 Protocol (Curated NSCLC Phase 3 Benchmark, NCT02484404)
- **Total Patient Profiles:** 6 Canonical Synthetic Encounters (`SYN_P001` to `SYN_P006`)
- **Total Evaluated Pairs:** 6 Patient-Trial Pairs
- **Total Decomposed Criteria:** 8 Atomic Protocol Criteria (5 Inclusion, 3 Exclusion)
- **Total Criterion-Level Evaluations:** 48 Labeled Pairs ($6 \times 8$)
- **Total Trial-Level Decisions:** 6 Decisions

### 3.2 Criteria Clinical Domain Breakdown

| Domain Category | Count | Percentage | Source Criterion Text |
|---|:---:|:---:|---|
| `diagnosis_stage` | 1 | 12.5% | "Histologically confirmed locally advanced or metastatic NSCLC (Stage IV)." |
| `biomarker_genomics` | 1 | 12.5% | "Documented EGFR sensitizing mutation (Exon 19 deletion or L858R)." |
| `age` | 1 | 12.5% | "Age >= 18 years." |
| `performance_status` | 1 | 12.5% | "ECOG performance status 0 or 1." |
| `laboratory_values` | 1 | 12.5% | "Adequate hematologic function: Platelet count >= 100 x 10^9/L." |
| `prior_treatment` | 2 | 25.0% | "Prior treatment with third-generation EGFR-TKI." / "Chemo within 28 days." |
| `comorbidities` | 1 | 12.5% | "Untreated or symptomatic central nervous system (CNS) metastases." |

### 3.3 Fixture Ground-Truth Class Breakdown
- **Trial-Level Decisions ($n=6$):**
  - `ELIGIBLE`: 1 (16.7%) — Scenario A (Positive Control)
  - `INELIGIBLE`: 3 (50.0%) — Scenarios B, E, F
  - `NEEDS_REVIEW`: 2 (33.3%) — Scenarios C, D
- **Criterion-Level Verdicts ($N=48$):**
  - `PASS`: 40 (83.3%)
  - `FAIL`: 5 (10.4%)
  - `UNKNOWN`: 3 (6.25%)

---

## 4. Separation of the Synthetic Stress-Test Subset

The 4 synthetic stress-test scenarios are cataloged in `data/splits/stress_test.jsonl` as an independent evaluation layer:

```text
+---------------------------------------------------------------------------------+
|                         STRESS-TEST EVALUATION SUBSET                           |
+-------------+-----------------------+---------------------+---------------------+
| Case ID     | Stress Category       | Expected Verdict    | Evaluated Dimension |
+-------------+-----------------------+---------------------+---------------------+
| SYN_P003    | missing_information   | NEEDS_REVIEW        | Conservative        |
|             |                       |                     | uncertainty         |
| SYN_P004    | conflicting_evidence  | NEEDS_REVIEW        | Contradiction       |
|             |                       |                     | detection           |
| SYN_P005    | boundary_condition    | INELIGIBLE          | Numerical cutoff    |
|             |                       |                     | (99 vs. 100)        |
| SYN_P006    | temporal_washout      | INELIGIBLE          | Washout interval    |
|             |                       |                     | (27 vs. 28 days)    |
+-------------+-----------------------+---------------------+---------------------+
```

> [!NOTE]
> The stress-test subset evaluates specific algorithmic failure modes (E6 numerical error, E7 temporal error, E9 missing evidence handling). It is explicitly **NOT representative of real-world clinical patient distributions**.

---

## 5. Development Partition Splits (TEST FIXTURE ONLY)

The fixture splits in `data/splits/` are structural test partitions for verifying the split validator:

| Partition File | Cases | Classification | Purpose |
|---|:---:|:---:|---|
| `data/splits/train.jsonl` | 3 | `TEST FIXTURE ONLY` | Tests split loading & training harness interfaces |
| `data/splits/validation.jsonl` | 1 | `TEST FIXTURE ONLY` | Tests validation pipeline & metric computation |
| `data/splits/test.jsonl` | 2 | `TEST FIXTURE ONLY` | Tests test evaluation pipeline & leakage checks |
| `data/splits/stress_test.jsonl` | 4 | `SYNTHETIC STRESS TEST` | Tests robustness and calibration logic |

- **Leakage Verification:** All 3 partition sets are mutually disjoint ($\mathcal{P}_{\text{train}} \cap \mathcal{P}_{\text{val}} = \emptyset$, $\mathcal{P}_{\text{train}} \cap \mathcal{P}_{\text{test}} = \emptyset$, $\mathcal{P}_{\text{val}} \cap \mathcal{P}_{\text{test}} = \emptyset$).
- **Methodology Notice:** A true 60/20/20 research split will be formed only when the external research benchmark (Layer B) is ingested with sufficient sample size.
