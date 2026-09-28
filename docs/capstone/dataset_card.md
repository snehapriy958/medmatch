# MedMatch Dataset Card

> **Dataset Name:** MedMatch Development Test Fixture & Evaluation Foundation  
> **Dataset Version:** `0.1.0-fixture`  
> **Dataset Classification:** **DEVELOPMENT / TEST FIXTURE ONLY — NOT A RESEARCH EVALUATION BENCHMARK**  
> **Domain:** Clinical Trial Matching / Oncology Decision Support  
> **Release Date:** September 2026  
> **Maintained by:** MedMatch Research Team

---

## 1. Dataset Classification & Purpose

> [!IMPORTANT]
> **DEVELOPMENT FIXTURE STATUS:**  
> The data currently present in this repository is strictly a **Phase 2 development/test fixture** designed to validate schemas, referential integrity, automated validators, and CI/CD pipelines.  
> **It is NOT a research evaluation benchmark** and must not be used to claim clinical matching efficacy.

### 1.1 Evaluated Dimensions
The dataset foundation specifies three complementary evaluation capabilities:
1. **Candidate Retrieval ($R_k$):** Recall@K, Precision@K, and MRR (to be evaluated over public TREC qrels once ingested).
2. **Criterion-Level Tri-State Reasoning ($g(P, c_i)$):** Accuracy, macro-$F_1$, and per-class metrics across `PASS`, `FAIL`, and `UNKNOWN` (to be evaluated on public TrialGPT annotations once ingested).
3. **Robustness & Uncertainty Stress Testing:** Calibration and handling of numerical boundaries, temporal intervals, missing data, and contradictory evidence (evaluated on the local `stress_test` subset).

---

## 2. Three Distinct Dataset Layers

```text
+---------------------------------------------------------------------------------------------------------+
|                                    THREE DATASET ARCHITECTURAL LAYERS                                   |
+----------------------+------------------------------------+-----------------------+---------------------+
| Layer Name           | Scope / Description                | Ingestion Status      | Ingested Count      |
+----------------------+------------------------------------+-----------------------+---------------------+
| development_fixture  | Tiny deterministic synthetic       | LOCAL FIXTURE         | 1 trial, 6 patients |
|                      | fixture for CI/CD & testing        | IMPLEMENTED           | 48 criterion labels |
|                      |                                    |                       | 6 trial labels      |
| research_benchmark   | External public benchmark corpus   | SOURCE IDENTIFIED —   | 0 patients ingested |
|                      | (TrialGPT, TREC Clinical Trials)   | NOT YET INGESTED      | 0 trials ingested   |
| stress_test          | Dedicated synthetic edge cases     | LOCAL FIXTURE         | 4 stress scenarios  |
|                      | (boundary, temporal, missing, etc.)| IMPLEMENTED           | (data/splits/)      |
+----------------------+------------------------------------+-----------------------+---------------------+
```

---

## 3. External Source Verification & Status

Every external dataset candidate evaluated in Phase 2 has been audited against primary publications, official repositories, and licensing frameworks:

### 3.1 ClinicalTrials.gov REST API v2
- **Official Source:** U.S. National Library of Medicine (NLM / NIH); [clinicaltrials.gov](https://clinicaltrials.gov/data-api/about-api).
- **Exact Identifier:** REST API v2 (`clinicaltrials.gov/api/v2/studies`).
- **Acquisition Status:** `SOURCE IDENTIFIED — NOT YET INGESTED` *(1 protocol manually extracted into fixture)*.
- **Labels Actually Contained:** Protocol descriptions, brief titles, conditions, interventions, phase, eligibility criteria text blocks. **Zero patient records, zero eligibility labels, zero relevance qrels.**
- **Task Supported:** Candidate protocol indexing and criteria text extraction.
- **License / Terms:** Public Domain (U.S. Government work). Unrestricted redistribution and academic use.

### 3.2 TrialGPT Benchmark Cohort
- **Official Source:** Qiao Jin et al., *Nature Communications* 15, Article 5772 (2024), DOI: 10.1038/s41467-024-49996-9.
- **Exact Identifiers:** GitHub: [ncbi-nlp/TrialGPT](https://github.com/ncbi-nlp/TrialGPT) | Hugging Face: [ncbi/TrialGPT-Criterion-Annotations](https://huggingface.co/datasets/ncbi/TrialGPT-Criterion-Annotations).
- **Acquisition Status:** `SOURCE IDENTIFIED — NOT YET INGESTED`.
- **Data & Labels Actually Contained:** 184 synthetic EHR clinical narratives; clinician-curated criterion-level tri-state annotations (`meets`, `fails`, `not mentioned`) covering ~1,200 patient-trial pairs (~2.5% of total pairs); aggregated trial-level eligibility decisions.
- **Task Supported:** Criterion-level tri-state reasoning (`PASS`, `FAIL`, `UNKNOWN`) and grounded decision attribution.
- **License / Terms:** Public Domain (NIH software) / MIT License on GitHub. Unrestricted academic reuse.

### 3.3 TREC Clinical Trials (2021 & 2022 Tracks)
- **Official Source:** National Institute of Standards and Technology (NIST) / Oregon Health & Science University (OHSU).
- **Exact Identifiers:** [trec-cds.org/2021.html](https://www.trec-cds.org/2021.html) and [trec-cds.org/2022.html](https://www.trec-cds.org/2022.html).
- **Acquisition Status:** `SOURCE IDENTIFIED — NOT YET INGESTED`.
- **Labels Actually Contained:** 75 (2021) and 50 (2022) clinical case topics; retrieval relevance judgments (qrels) evaluated on a 3-point scale (`0`=irrelevant, `1`=excluded, `2`=eligible). **Contains retrieval relevance qrels only; DOES NOT contain fine-grained criterion-level labels or character text spans.**
- **Task Supported:** Candidate retrieval evaluation (Recall@K, Precision@K, MRR, nDCG@K).
- **License / Terms:** Open Academic Research Use under NIST TREC guidelines.

### 3.4 MIMIC-IV Clinical Database
- **Official Source:** MIT Laboratory for Computational Physiology; [physionet.org/content/mimiciv](https://physionet.org/content/mimiciv/).
- **Acquisition Status:** `REJECTED — NOT SUITABLE`.
- **Labels Contained:** Real de-identified inpatient EHR data. **Zero trial screening ground truth.**
- **Rationale for Rejection:** No clinical trial matching labels; PhysioNet Data Use Agreements prohibit committing data to public code repositories.

---

## 4. Current Development Fixture Composition

The local fixture under `data/fixtures/` contains:
- **Trials ($n=1$):** Curated NSCLC Phase 3 protocol (NCT02484404) with 8 decomposed criteria (5 inclusion, 3 exclusion).
- **Patients ($n=6$):** 6 canonical synthetic encounters (`SYN_P001` to `SYN_P006`).
- **Criterion Ground Truth ($N=48$):** 40 `PASS`, 5 `FAIL`, 3 `UNKNOWN` with character-level verbatim text spans.
- **Trial Ground Truth ($n=6$):** 1 `ELIGIBLE`, 3 `INELIGIBLE`, 2 `NEEDS_REVIEW`.
- **Classification:** `DEVELOPMENT/TEST FIXTURE ONLY`.

---

## 5. Separation of the Synthetic Stress-Test Subset

The 4 synthetic stress-test scenarios are cataloged in `data/splits/stress_test.jsonl` as an independent evaluation layer:
- `SYN_P003`: Missing information (EGFR pending, brain MRI omitted) $\implies$ tests conservative uncertainty (`NEEDS_REVIEW`).
- `SYN_P004`: Conflicting evidence (tissue positive vs. liquid negative) $\implies$ tests contradiction detection (`NEEDS_REVIEW`).
- `SYN_P005`: Numerical boundary condition (Platelets = 99 vs. $\ge 100 \times 10^9/\text{L}$) $\implies$ tests numerical inequality comparison (`INELIGIBLE`).
- `SYN_P006`: Temporal washout condition (Chemo completed 27 days vs. $\ge 28$ days required) $\implies$ tests temporal interval arithmetic (`INELIGIBLE`).

*Policy:* Stress tests are evaluated separately and are not combined with standard benchmark distributions.

---

## 6. Split Methodology (TEST FIXTURE ONLY)

The fixture splits in `data/splits/` (`train.jsonl`, `validation.jsonl`, `test.jsonl`) are **structural test partitions** for verifying split loading and zero-leakage validator logic:
- All records are explicitly labeled: `benchmark_classification: "TEST FIXTURE ONLY - NOT A RESEARCH BENCHMARK"`.
- Mutual disjointness is strictly verified: $\mathcal{P}_{\text{train}} \cap \mathcal{P}_{\text{val}} = \emptyset$, $\mathcal{P}_{\text{train}} \cap \mathcal{P}_{\text{test}} = \emptyset$, $\mathcal{P}_{\text{val}} \cap \mathcal{P}_{\text{test}} = \emptyset$.
- A true 60/20/20 research split will be formed only when the external research benchmark (Layer B) is ingested with sufficient sample size.

---

## 7. Privacy, Ethics & Regulatory Compliance

- **Zero Protected Health Information (PHI):** The repository contains zero real patient health records.
- **HIPAA Safe Harbor Compliance:** All patient identifiers are synthetic alphanumeric hashes (e.g., `SYN_P001`). All dates are standardized reference offsets.
- **GDPR Compliance:** No personal data of European citizens is collected, stored, or processed.
