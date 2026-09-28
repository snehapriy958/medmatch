# MedMatch Dataset & Ground Truth Infrastructure

> **Dataset Name:** MedMatch Development Test Fixture & Evaluation Foundation  
> **Version:** `0.1.0-fixture`  
> **Status:** Phase 2 Data Foundation & Development Fixture  
> **Classification:** **DEVELOPMENT / TEST FIXTURE ONLY — NOT A RESEARCH EVALUATION BENCHMARK**  
> **License:** Mixed Open Academic (Public Domain / MIT / CC-BY 4.0 / Apache 2.0)  
> **Release Date:** September 2026

---

## 1. Critical Distinction: Fixture vs. Research Benchmark

> [!IMPORTANT]
> **DEVELOPMENT FIXTURE STATUS:**  
> The data currently present in this repository consists solely of a **Phase 2 development/test fixture** (1 trial, 6 synthetic patients, 8 criteria, 48 criterion evaluations, and 6 trial-level decisions).  
> **It is NOT a research evaluation benchmark** and must **NEVER** be presented as a statistically sufficient dataset for validating MedMatch matching performance. Its sole purpose is to test schemas, referential integrity, automated validators, and CI/CD pipelines.

---

## 2. Three Distinct Dataset Layers

To maintain scientific integrity and prevent conflating synthetic edge cases with real-world clinical distributions, MedMatch formally partitions data into three distinct architectural layers:

```text
+---------------------------------------------------------------------------------------------------------+
|                                    THREE DATASET ARCHITECTURAL LAYERS                                   |
+---------------------------------------------------------------------------------------------------------+
                                                     |
         +-------------------------------------------+-------------------------------------------+
         |                                           |                                           |
         v                                           v                                           v
+-------------------------------+   +-------------------------------+   +-------------------------------+
|            LAYER A            |   |            LAYER B            |   |            LAYER C            |
|     development_fixture       |   |      research_benchmark       |   |          stress_test          |
|-------------------------------|   |-------------------------------|   |-------------------------------|
| - Status: IMPLEMENTED         |   | - Status: IDENTIFIED —        |   | - Status: IMPLEMENTED         |
| - Tiny deterministic fixture  |   |   NOT YET INGESTED            |   | - Dedicated edge-case subset  |
| - 1 Trial (NCT02484404)       |   | - External public benchmarks  |   | - Boundary conditions (lab)   |
| - 6 Synthetic Patients        |   |   (TrialGPT, TREC CT 2021/22) |   | - Temporal washout intervals  |
| - Used strictly for schema    |   | - Primary quantitative        |   | - Missing data (uncertainty)  |
|   validation & test harness   |   |   capstone evaluation corpus  |   | - Contradictory evidence      |
+-------------------------------+   +-------------------------------+   +-------------------------------+
```

### Layer A: `development_fixture` (Implemented)
- **Purpose:** Fast, offline, deterministic unit and integration testing.
- **Contents:** `data/fixtures/` (trials.json, patients.json, criteria.json, criterion_labels.json, trial_labels.json).
- **Scope:** 1 trial, 6 patients, 8 criteria.

### Layer B: `research_benchmark` (`SOURCE IDENTIFIED — NOT YET INGESTED`)
- **Purpose:** Primary quantitative research evaluation of retrieval recall and eligibility classification.
- **External Candidates:**
  - *ClinicalTrials.gov API v2:* Full multi-protocol oncology corpus.
  - *TrialGPT Benchmark Cohort:* 184 synthetic EHR summaries with clinician-curated criterion annotations.
  - *TREC Clinical Trials (2021 & 2022):* Standardized retrieval case topics and relevance qrels.
- **Current Status:** Not yet ingested or committed into the repository.

### Layer C: `stress_test` (Implemented Subset)
- **Purpose:** Targeted robustness, calibration, and edge-case testing.
- **Contents:** `data/splits/stress_test.jsonl` (4 synthetic patient scenarios: `SYN_P003`, `SYN_P004`, `SYN_P005`, `SYN_P006`).
- **Scope:** Evaluates mathematical boundary logic, temporal washout calculations, conservative missing-data handling (`NEEDS_REVIEW`), and contradiction detection.
- **Policy:** Kept strictly separate from primary benchmark evaluations.

---

## 3. Directory Layout

```text
data/
├── README.md                         # This specification and reproduction guide
│
├── raw/                              # Original, unmodified source downloads (Git-ignored)
│   ├── trials/                       # Raw ClinicalTrials.gov API v2 study JSON payloads
│   ├── patients/                     # Raw TREC CT topic XMLs and TrialGPT patient narratives
│   └── external/                     # Third-party benchmark artifacts and qrels
│
├── processed/                        # Canonical normalized records (Git-ignored)
│   ├── trials/                       # Normalized CanonicalTrial JSON records
│   ├── patients/                     # Normalized CanonicalPatient JSON records
│   └── criteria/                     # Parsed atomic CanonicalCriterion records
│
├── annotations/                      # Ground-truth labels (Git-ignored for large sets)
│   ├── criterion_labels/             # CriterionGroundTruth annotations (PASS/FAIL/UNKNOWN)
│   └── trial_labels/                 # Aggregated TrialGroundTruth annotations
│
├── splits/                           # Evaluation partitions & subsets
│   ├── train.jsonl                   # Development fixture train split (TEST FIXTURE ONLY)
│   ├── validation.jsonl              # Development fixture validation split (TEST FIXTURE ONLY)
│   ├── test.jsonl                    # Development fixture test split (TEST FIXTURE ONLY)
│   └── stress_test.jsonl             # Dedicated stress-test subset (SYNTHETIC STRESS TEST ONLY)
│
├── manifests/                        # Versioned audit manifests & cryptographic signatures
│   ├── dataset_manifest.json         # Master metadata, layer classifications, and source statuses
│   └── checksums.sha256              # SHA-256 hashes for all tracked data files
│
├── evaluation/                       # Evaluation harness outputs and baselines
│   └── README.md                     # Directory guide for experiment outputs and runs
│
└── fixtures/                         # Deterministic test fixtures for CI/CD and validator testing
    ├── trials.json                   # Curated canonical oncology trials
    ├── patients.json                 # Curated canonical patient profiles
    ├── criteria.json                 # Decomposed atomic criteria
    ├── criterion_labels.json         # Criterion-level ground truth with character spans
    └── trial_labels.json             # Aggregated trial-level ground truth
```

---

## 4. Split Methodology & Clarifications

### 4.1 Development Test Fixture Splits
The partition files `data/splits/train.jsonl` (3 cases), `data/splits/validation.jsonl` (1 case), and `data/splits/test.jsonl` (2 cases) are **strictly structural test partitions** created to verify that the split validator and leakage detection logic function correctly.

> [!WARNING]
> The 6-case split is **NOT a statistically meaningful 60/20/20 research split**. All lines in these files are explicitly marked:
> `benchmark_classification: "TEST FIXTURE ONLY - NOT A RESEARCH BENCHMARK"`

### 4.2 Research Benchmark Splits (Future Protocol)
Once Layer B (`research_benchmark`) is ingested from public sources, a true 60/20/20 train/validation/test split will be constructed **only if the final sample size provides sufficient statistical power**:
- **Train (60%):** Prompt tuning, few-shot demonstration selection, retrieval vocabulary alignment.
- **Validation (20%):** Hyperparameter optimization, similarity threshold selection, reranker calibration.
- **Test (20%):** Held-out, untouched benchmark evaluation.

### 4.3 Separation of Stress-Test Subset
The stress-test scenarios (`missing_information`, `conflicting_evidence`, `boundary_condition`, `temporal_washout`) are cataloged separately in `data/splits/stress_test.jsonl`. They are evaluated independently from primary benchmark test sets to ensure that artificial edge-case frequencies do not distort standard classification metrics.

---

## 5. Status and Verification of External Data Sources

| Source Entity | Official Reference / Repository | Ingestion Status | Labels Actually Contained | Supported Task | License / Terms | Redistribution / Legal Use |
|---|---|:---:|---|---|---|:---:|
| **ClinicalTrials.gov REST API v2** | NLM / NIH; `clinicaltrials.gov/api/v2/studies` | `SOURCE IDENTIFIED — NOT YET INGESTED` *(1 protocol manually extracted into fixture)* | Protocol text, eligibility criteria blocks, phase, conditions. **Zero patient records, zero eligibility labels.** | Protocol ingestion & criteria parsing | Public Domain (U.S. Gov) | Unrestricted |
| **TrialGPT Benchmark Cohort** | Qiao Jin et al., *Nature Communications* (2024); GitHub: `ncbi-nlp/TrialGPT`, HuggingFace: `ncbi/TrialGPT-Criterion-Annotations` | `SOURCE IDENTIFIED — NOT YET INGESTED` | 184 synthetic EHR case summaries; criterion-level clinician annotations (`meets`, `fails`, `not mentioned`) for ~1,200 pairs; trial-level decisions | Criterion tri-state reasoning & provenance grounding | Public Domain (NIH) / MIT | Unrestricted academic reuse |
| **TREC Clinical Trials 2021 Track** | NIST / OHSU; `trec-cds.org/2021.html` | `SOURCE IDENTIFIED — NOT YET INGESTED` | 75 synthetic/semi-synthetic case topics; retrieval relevance qrels (0, 1, 2). **No criterion-level labels or text spans.** | Candidate retrieval evaluation (Recall@K, MRR) | Open Academic (NIST terms) | Permitted for research |
| **TREC Clinical Trials 2022 Track** | NIST / OHSU; `trec-cds.org/2022.html` | `SOURCE IDENTIFIED — NOT YET INGESTED` | 50 case topics; retrieval relevance qrels (0, 1, 2). **No criterion-level labels.** | Candidate retrieval evaluation | Open Academic (NIST terms) | Permitted for research |
| **MIMIC-IV** | MIT / PhysioNet; `physionet.org/content/mimiciv` | `REJECTED — NOT SUITABLE` | Real de-identified inpatient records. **Zero trial screening ground truth.** DUA prohibits redistribution. | None | PhysioNet Credentialed DUA | Not permitted in Git |

---

## 6. Automated Validation

To verify the integrity and consistency of the dataset, run:

```bash
python scripts/validate_dataset.py --data-dir data
python -m pytest tests/dataset -v
```

The validator verifies:
- Schema conformance for all trials, patients, criteria, and annotations.
- Referential integrity (no orphan foreign keys).
- Verbatim character-offset match for all cited patient evidence text spans.
- Deterministic clinical aggregation consistency ($|\text{FAIL}| > 0 \iff \text{INELIGIBLE}$).
- Zero patient leakage across splits.
