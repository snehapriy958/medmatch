# Phase 4 Patient Clinical Information Extraction — Development Fixture

## Purpose & Scope

> [!WARNING]
> **CRITICAL CLASSIFICATION:**
> This directory contains a controlled **development fixture** specifically engineered for validating the Phase 4 patient clinical profile schemas, clinical fact models, temporality representation, uncertainty states, negation semantics, provenance tracking, and extraction validation.
>
> **IT IS NOT A CLINICAL RESEARCH BENCHMARK.**
> Do NOT use this fixture to calculate, claim, or report empirical clinical extraction accuracy, precision, recall, or F1 scores. Validating clinical extraction performance requires a dedicated, clinically annotated benchmark corpus (e.g., MIMIC-IV or double-annotated EHR clinical notes from clinical oncology trials).

## Fixture Metadata
- **dataset_layer:** `development_fixture`
- **benchmark_classification:** `TEST FIXTURE ONLY - NOT A RESEARCH BENCHMARK`
- **schema_version:** `0.4.0`

## Fixture Contents

| File | Description | Schema |
| :--- | :--- | :--- |
| `patient_clinical_profile_fixture.json` | Comprehensive patient profile covering all 16 required clinical scenarios | `PatientClinicalProfile` |
| `patient_extraction_contract.json` | Stable downstream extraction contract envelope with extraction metadata | `PatientExtractionContract` |
| `build_fixture.py` | Deterministic script generating and validating the fixture JSON files | Python Generator |

## Covered Canonical Scenarios (16 Required Patterns)

1. **Positive Diagnosis:** Histologically confirmed non-small cell lung cancer adenocarcinoma (`FACT_001`).
2. **Negated Diagnosis:** Active brain or leptomeningeal metastases explicitly ruled out on MRI (`FACT_002`).
3. **Historical Diagnosis:** Childhood asthma resolved 15 years ago (`FACT_003`).
4. **Current Medication:** Amlodipine 5mg daily for blood pressure control (`FACT_004`).
5. **Historical Medication:** Carboplatin/Pemetrexed completed first-line chemotherapy (`FACT_005`).
6. **Laboratory Result with Unit:** Absolute neutrophil count (ANC) 2.1 x 10^9/L (`FACT_006`).
7. **Biomarker Status:** EGFR exon 19 deletion detected (`FACT_007`).
8. **Missing Information:** Explicitly cataloged unmentioned oncology variable (PD-L1 status not stated) (`missing_information`).
9. **Uncertain Information:** Suspicious adrenal nodule, indeterminate on CT (`FACT_008`).
10. **Conflicting Evidence:** Discrepant pleural effusion documentation across reports (`FACT_009`).
11. **Temporal Event:** Definite calendar date for primary resection on 2025-11-10 (`FACT_010`).
12. **Relative Temporal Statement:** Completed stereotactic radiation 27 days ago (`FACT_011`).
13. **Patient-Reported Information:** Patient reports mild penicillin allergy in childhood (`FACT_012`).
14. **Clinician-Documented Information:** Oncologist documented ECOG performance status 1 (`FACT_013`).
15. **Multiple Facts in One Sentence:** Single sentence yielding stage, histology, and smoking status (`FACT_014`, `FACT_015`).
16. **Ambiguous Clinical Statement:** Subjective clinical discretion ("Fair general condition") marked `uncertain` (`FACT_016`).
