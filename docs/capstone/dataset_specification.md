# MedMatch Capstone — Dataset & Corpus Specification

> **Status:** Specification Document  
> **Phase:** 1 — Research Problem & Evaluation Design  
> **Author:** MedMatch Research Team  
> **Date:** September 2026  
> **Target System:** MedMatch Clinical Decision-Support Prototype

---

## 1. Directory Structure Specification

The project dataset layout is structured to maintain strict separation between raw public registries, processed intermediate clinical models, human/expert annotations, deterministic splits, and evaluation run artifacts.

```text
data/
├── raw/
│   ├── trials/                       # Original CT.gov JSON exports (unmodified API v2 payloads)
│   └── patients/                     # Raw clinical case descriptions / public TREC case narratives
│
├── processed/
│   ├── trials/                       # Normalized protocol JSON (NCT_ID, conditions, summary, phase)
│   ├── patients/                     # Normalized patient records (narrative, structured attributes)
│   └── criteria/                     # Parsed atomic criteria with domain tags & inclusion/exclusion flags
│
├── annotations/
│   ├── criterion_labels/             # Ground-truth annotations for patient-criterion pairs (PASS/FAIL/UNKNOWN)
│   └── trial_labels/                 # Aggregated trial-level ground truth (ELIGIBLE/INELIGIBLE/NEEDS_REVIEW)
│
├── splits/
│   ├── train.json                    # Development, prompt calibration, and sparse/dense index training (60%)
│   ├── validation.json               # Hyperparameter & similarity threshold tuning, reranker calibration (20%)
│   └── test.json                     # Strictly held-out, untouched final benchmark evaluation (20%)
│
└── evaluation/
    ├── baselines/                    # Serialized outputs from System A (LLM-only) and System B (Current)
    └── runs/                         # Timestamped experiment logs, prediction JSONs, and metric artifacts
```

> **Mandatory Policy:** No fabricated labels or ad-hoc data files will be created in this phase. The directory structure will be initialized and populated in Phase 2 according to verified source acquisitions.

---

## 2. Dataset Sourcing Strategy

Evaluating clinical trial matching requires paired tuples of $\langle \text{Patient}, \text{Trial}, \text{Criteria}, \text{Ground Truth} \rangle$. Public clinical data is constrained by patient privacy (HIPAA/GDPR), while registry data lacks patient-level matches.

### 2.1 Comparative Analysis of Candidate Resources

| Dataset / Resource | Availability | Suitability | License / Access | Patient Data? | Trial Data? | Ground Truth? | Primary Utility |
|---|---|---|---|---|---|---|---|
| **ClinicalTrials.gov (REST API v2)** | Open Public Web API | High for trial corpus; zero for patient matching | Public Domain (U.S. Gov) | No | Yes (480,000+ protocols) | No (No patient records) | Source corpus for clinical trial protocols and criteria extraction |
| **TREC Clinical Trials (2021 & 2022 Tracks)** | Public Academic Benchmark | High for retrieval; moderate for eligibility | Open for research (NIST) | Semi-synthetic clinical case topics ($n=75$ cases) | Yes (Filtered subsets of CT.gov) | Yes (Relevance qrels: 0=irrelevant, 1=excluded, 2=eligible) | Retrieval evaluation benchmark (Recall@K, MRR) and macro eligibility |
| **TrialGPT Benchmark Cohort (Jin et al., 2024)** | Open GitHub / HuggingFace | High for fine-grained criterion evaluation | MIT / CC-BY 4.0 | Semi-synthetic EHR case summaries ($n=184$ patients) | Yes (1,200+ matched trials) | Yes (Criterion-level & trial-level labels verified by clinicians) | Primary gold standard for criterion-level reasoning and grounding |
| **MIMIC-IV / PhysioNet (De-identified EHR)** | Credentialed PhysioNet Access | High for realistic clinical narratives | PhysioNet DUA / CITI Training required | Yes (De-identified real ICU/inpatient EHR) | No | No (No matched trials) | Candidate for realistic clinical text distribution (Phase 3+) |
| **Rule-Derived Synthetic Cohorts** | Procedural Generation | High for boundary cases & ablation testing | Internal Project License | Synthetic only (Rule-derived) | Derived from real CT.gov criteria | Yes (Deterministic ground truth by construction) | Stress testing: numerical boundaries, temporal rules, uncertainty |

### 2.2 Sourcing Strategy Conclusion
1. **Primary Evaluation Benchmark:** A combination of the **TrialGPT benchmark cohort** (for fine-grained criterion-level ground truth and evidence attribution) and **TREC Clinical Trials topics** (for broad candidate retrieval evaluation).
2. **Trial Protocol Corpus:** Directly ingested from **ClinicalTrials.gov API v2** across high-prevalence oncology domains (Non-Small Cell Lung Cancer, Breast Invasive Carcinoma, Colorectal Adenocarcinoma, Cutaneous Melanoma, Glioblastoma).
3. **Targeted Synthetic Cohort:** Generated under strict programmatic constraints to evaluate boundary conditions and clinical uncertainty.

---

## 3. Synthetic Data Policy & Generation Protocol

Where public real-world datasets lack sufficient edge cases for numerical thresholds, temporal constraints, or missing lab tests, rule-derived synthetic patients will be employed.

### 3.1 Strict Limitations and Clinical Warning
> **LIMITATION DISCLOSURE:** Synthetic patient profiles are programmatic constructs designed solely to evaluate deterministic constraint satisfaction and model calibration. They **must never be represented as real clinical evidence** or used to draw real-world epidemiological conclusions.

### 3.2 Controlled Synthetic Cohort Categories

To ensure scientific validity, synthetic profiles must be derived from explicit clinical trial criteria across six distinct functional categories:

```text
                               +-----------------------------+
                               | TRIAL CRITERION DEFINITION  |
                               | Age >= 18                   |
                               | Diagnosis: Stage IV NSCLC   |
                               | EGFR: Exon 19 del or L858R  |
                               | Platelets >= 100,000 / uL   |
                               | Washout: Chemo >= 28 days   |
                               +-----------------------------+
                                              |
                +-----------------------------+-----------------------------+
                |                             |                             |
                v                             v                             v
     [1. Clearly Eligible]        [2. Clearly Ineligible]         [3. Missing Info]
     Age = 58                     Age = 16 (Violates Age)         Platelets not recorded
     Stage IV NSCLC               Stage II NSCLC (Violates Stage) Diagnosis: NSCLC (Stage omitted)
     EGFR Exon 19 del             KRAS G12C (EGFR Wild-type)      EGFR: Pending
     Platelets = 185,000 / uL     Platelets = 62,000 / uL         Expected:
     Chemo: 45 days ago           Chemo: 8 days ago               y = UNKNOWN
     Expected:                    Expected:                       Y = NEEDS_REVIEW
     y_all = PASS                 y_fail >= 1
     Y = ELIGIBLE                 Y = INELIGIBLE
                |                             |                             |
                v                             v                             v
     [4. Conflicting Info]        [5. Boundary Condition]        [6. Temporal Condition]
     Pathology: "EGFR positive"   Platelets = 99,000 / uL        Chemo completed: 27 days ago
     Oncology Note: "EGFR neg"    (Exact threshold edge)         (Washout requirement: >= 28 days)
     Expected:                    Expected:                      Expected:
     Flag conflict                y = FAIL (or calibration test) y = FAIL (Washout period unmet)
     Y = NEEDS_REVIEW             Y = INELIGIBLE                 Y = INELIGIBLE
```

1. **Category 1: Clearly Eligible (Positive Control):**  
   Every inclusion condition is fully met; every exclusion condition is confirmed absent. Expected: $Y = \text{ELIGIBLE}$.
2. **Category 2: Clearly Ineligible (Negative Disqualification Control):**  
   Violates at least one mandatory inclusion or triggers at least one active exclusion. Expected: $Y = \text{INELIGIBLE}$.
3. **Category 3: Missing Information (Uncertainty Control):**  
   One or more critical lab measurements, staging details, or biomarker statuses are omitted from the narrative. Expected: $y_i = \text{UNKNOWN}, Y = \text{NEEDS\_REVIEW}$.
4. **Category 4: Conflicting Clinical Evidence:**  
   The record contains contradictory statements across clinical sections (e.g., biopsy report positive, progress note negative). Expected: Flagged conflict, $Y = \text{NEEDS\_REVIEW}$.
5. **Category 5: Numerical Boundary Condition:**  
   Laboratory values placed exactly on, just above, or just below inclusion thresholds (e.g., threshold $\ge 100 \times 10^9/\text{L}$; patient values at $99$, $100$, and $101$).
6. **Category 6: Temporal / Washout Condition:**  
   Prior therapies or surgeries with precise time intervals relative to screening date (e.g., 27 days vs. 28 days post-chemotherapy).

---

## 4. Train / Validation / Test Split Protocol

### 4.1 Split Proportions and Sizing
The benchmark dataset will be partitioned into three deterministic splits:
- **Train Set (60%):** Used for prompt engineering, few-shot demonstration selection, candidate retrieval index tuning, and sparse/dense vocabulary alignment.
- **Validation Set (20%):** Used for retrieval top-$k$ selection, similarity score threshold calibration, cross-encoder reranker cutoffs, and hyperparameter optimization.
- **Test Set (20%):** **Held-out, untouched evaluation set.** Run strictly once for the final capstone report. Never examined during prompt or parameter tuning.

### 4.2 Leakage Prevention Rules
To avoid optimistic performance bias, splits must adhere to strict orthogonality constraints:
1. **Patient-Level Disjointness:** No patient profile, case narrative, or synthetic patient variant present in the Train or Validation split may appear in the Test split:
   $$\mathcal{P}_{\text{train}} \cap \mathcal{P}_{\text{val}} = \emptyset, \quad \mathcal{P}_{\text{train}} \cap \mathcal{P}_{\text{test}} = \emptyset, \quad \mathcal{P}_{\text{val}} \cap \mathcal{P}_{\text{test}} = \emptyset$$
2. **Trial-Level Grouping:** When synthetic profiles are generated from clinical trials, all patient-trial pairs derived from a single protocol $T$ must be allocated exclusively to either the training set or the test set to evaluate zero-shot protocol generalization.
3. **Deterministic Assignment:** Splitting will use a fixed cryptographic hash of the patient identifier:
   $$\text{hash}(\text{patient\_id} + \text{salt}) \pmod{100}$$
   With fixed global random seed: `SEED = 42`.
4. **Dataset Versioning:** All splits will be frozen under immutable semantic versioning: `DATASET_VERSION = "v1.0.0-capstone"`.
