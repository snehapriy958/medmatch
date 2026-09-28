# MedMatch Capstone — Dataset Source Audit & Acquisition Verification

> **Status:** Phase 2 Source Verification Document  
> **Phase:** 2 — Dataset + Ground Truth  
> **Author:** MedMatch Research Team  
> **Date:** September 2026  
> **Target System:** MedMatch Clinical Decision-Support Prototype

---

## 1. Executive Summary & Verification Mandate

To ensure complete transparency and academic integrity, MedMatch conducted a primary-source audit of all candidate datasets, registries, and academic benchmarks. 

This audit establishes:
1. **Current Ingested State:** Only the **Phase 2 development test fixture** (1 trial, 6 synthetic patients, 8 criteria) and the **synthetic stress-test subset** (4 edge cases) are currently implemented and present in the codebase.
2. **External Research Benchmark State:** All external datasets (ClinicalTrials.gov API, TrialGPT, TREC Clinical Trials) are classified as **`SOURCE IDENTIFIED — NOT YET INGESTED`**. They have been audited for licensing, labels, and feasibility, but have not yet been downloaded or committed into the repository.
3. **Exact Label Taxonomy:** Strict boundaries are maintained between retrieval relevance judgments (qrels), patient-trial eligibility labels, and atomic criterion-level tri-state annotations.

---

## 2. Dataset Source Verification Table

| Source | Official Reference | Exact Identifier | Ingestion Status | Labels Contained | Supported Task | License / Terms | Redistribution | Legal Use for Research |
|---|---|---|:---:|---|---|---|:---:|:---:|
| **ClinicalTrials.gov REST API v2** | U.S. National Library of Medicine (NLM / NIH) | `clinicaltrials.gov/api/v2/studies` | `SOURCE IDENTIFIED — NOT YET INGESTED` *(1 protocol template in fixture)* | Protocol text, eligibility criteria blocks, phase, conditions. **Zero patient records, zero eligibility labels.** | Protocol indexing & criteria text parsing | Public Domain (U.S. Gov) | Unrestricted | Yes |
| **TrialGPT Benchmark Cohort** | Qiao Jin et al., *Nature Communications* (2024), DOI: 10.1038/s41467-024-49996-9 | GitHub: `ncbi-nlp/TrialGPT`<br>HF: `ncbi/TrialGPT-Criterion-Annotations` | `SOURCE IDENTIFIED — NOT YET INGESTED` | 184 synthetic EHR case summaries; criterion-level clinician annotations (`meets`, `fails`, `not mentioned`) for ~1,200 pairs (~2.5% of total pairs); aggregated trial-level decisions | Criterion tri-state reasoning (`PASS`/`FAIL`/`UNKNOWN`) and grounding | Public Domain (NIH) / MIT | Unrestricted | Yes |
| **TREC Clinical Trials 2021 Track** | NIST / OHSU (TREC 2021 Proceedings) | `trec-cds.org/2021.html` | `SOURCE IDENTIFIED — NOT YET INGESTED` | 75 synthetic/semi-synthetic case topics; retrieval relevance qrels (0=irrelevant, 1=excluded, 2=eligible). **No criterion-level labels or character text spans.** | Candidate retrieval evaluation (Recall@K, MRR, nDCG@K) | Open Academic (NIST terms) | Permitted | Yes |
| **TREC Clinical Trials 2022 Track** | NIST / OHSU (TREC 2022 Proceedings) | `trec-cds.org/2022.html` | `SOURCE IDENTIFIED — NOT YET INGESTED` | 50 clinical case topics; retrieval relevance qrels (0, 1, 2). **No criterion-level labels.** | Candidate retrieval evaluation (Recall@K, MRR, nDCG@K) | Open Academic (NIST terms) | Permitted | Yes |
| **MIMIC-IV Clinical Database** | MIT / PhysioNet; Johnson et al., *Scientific Data* (2023) | `physionet.org/content/mimiciv/2.2/` | `REJECTED — NOT SUITABLE` | Real de-identified inpatient EHR data. **Zero clinical trial matching labels.** | None | PhysioNet Credentialed DUA | Prohibited in Git | No (DUA restrictions) |
| **MedMatch Development Test Fixture** | MedMatch In-House Generator | `data/fixtures/` (`trials.json`, `patients.json`, etc.) | `LOCAL FIXTURE IMPLEMENTED` | 1 protocol, 6 synthetic patients, 8 criteria, 48 criterion labels (`PASS`/`FAIL`/`UNKNOWN` with text spans), 6 trial decisions | Schema validation, referential integrity testing, CI/CD | Apache 2.0 | Unrestricted | Yes |
| **MedMatch Synthetic Stress-Test Subset** | MedMatch In-House Generator | `data/splits/stress_test.jsonl` | `LOCAL FIXTURE IMPLEMENTED` | 4 synthetic edge-case scenarios (boundary, temporal, missing info, conflicting evidence) | Robustness, numerical boundary, and calibration testing | Apache 2.0 | Unrestricted | Yes |

---

## 3. Detailed Source Audits & Label Capabilities

### 3.1 ClinicalTrials.gov REST API v2
- **Source Authority:** U.S. National Library of Medicine.
- **Data Model:** RESTful JSON responses (`/api/v2/studies/{nctId}`).
- **Labels Analysis:** Contains **NO patient records** and **NO patient-trial labels**. It provides only the protocol text and criteria strings needed to index the clinical trial search space.
- **Role in MedMatch:** Protocol ingestion and atomic criteria parsing.

### 3.2 TrialGPT Benchmark Cohort (Jin et al., 2024)
- **Source Authority:** National Center for Biotechnology Information (NCBI / NLM / NIH).
- **Data Model:** JSON and tabular files containing 184 synthetic EHR case summaries.
- **Labels Analysis:** Contains criterion-level clinician annotations for ~1,200 patient-trial pairs, categorized as:
  - `meets`: Patient explicitly satisfies the criterion ($\approx \text{PASS}$).
  - `fails`: Patient explicitly violates the criterion ($\approx \text{FAIL}$).
  - `not mentioned`: Patient narrative omits relevant information ($\approx \text{UNKNOWN}$).
- **Important Constraint:** Annotations cover only a subset (~2.5%) of all potential patient-trial combinations in the cohort.
- **Role in MedMatch:** Target gold-standard for fine-grained criterion-level evaluation once ingested in future phases.

### 3.3 TREC Clinical Trials (2021 & 2022 Tracks)
- **Source Authority:** NIST and Oregon Health & Science University.
- **Data Model:** XML case topics and standard TREC qrel text files.
- **Labels Analysis:** Evaluates candidate trials on a 3-point relevance scale:
  - `0`: Irrelevant (patient does not have the condition or would not be referred).
  - `1`: Excluded (patient has the condition, but violates at least one exclusion criterion).
  - `2`: Eligible (patient has the condition, satisfies key criteria, and would be referred).
- **Important Constraint:** **Does NOT contain criterion-level labels or character text spans.**
- **Role in MedMatch:** Target benchmark for Stage 1 candidate retrieval evaluation (Recall@K, MRR, nDCG).

### 3.4 MIMIC-IV Clinical Database (PhysioNet)
- **Rejection Finding:** MIMIC-IV is **formally rejected** because it contains no clinical trial screening annotations, and its Data Use Agreement strictly prohibits committing patient records to public version-control systems.

---

## 4. Separation of the Three Dataset Layers

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
| - Status: LOCAL FIXTURE       |   | - Status: SOURCE IDENTIFIED — |   | - Status: LOCAL FIXTURE       |
|   IMPLEMENTED                 |   |   NOT YET INGESTED            |   |   IMPLEMENTED                 |
| - 1 Trial, 6 Patients         |   | - External public benchmarks  |   | - Dedicated edge-case subset  |
| - 48 Criterion Labels         |   |   (TrialGPT, TREC CT 2021/22) |   | - 4 Controlled Scenarios      |
| - Used strictly for schema    |   | - Primary quantitative        |   | - Boundary, temporal, missing |
|   validation & test harness   |   |   evaluation corpus           |   |   info, contradictory data    |
+-------------------------------+   +-------------------------------+   +-------------------------------+
```

---

## 5. Decision Summary & Next Steps

1. **Development Fixture Retained:** The local fixture (`data/fixtures/`) remains in place exclusively for CI/CD, schema validation, and unit tests.
2. **Stress Tests Isolated:** The 4 synthetic edge-case scenarios are isolated into `data/splits/stress_test.jsonl` to ensure they are evaluated separately from primary benchmark distributions.
3. **External Benchmarks Tracked:** TrialGPT and TREC Clinical Trials are verified as open, legally compliant sources for future ingestion.
