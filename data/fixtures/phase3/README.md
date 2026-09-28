# Phase 3 Clinical Trial Document Intelligence — Development Fixture

## Purpose & Scope

> [!WARNING]
> **CRITICAL CLASSIFICATION:**
> This directory contains a synthetic **development fixture** specifically engineered for validating the Phase 3 clinical trial document intelligence schema, section normalization, atomic criteria models, provenance tracking, and extraction validation.
>
> **IT IS NOT A CLINICAL RESEARCH BENCHMARK.**
> Do NOT use this fixture to calculate, claim, or report empirical extraction accuracy, precision, recall, or F1 scores. Empirical benchmarking requires a fully annotated gold-standard corpus (e.g., from ClinicalTrials.gov protocols annotated by double-blind clinical experts).

## Fixture Contents

| File | Description | Schema |
| :--- | :--- | :--- |
| `trial_document_fixture.json` | Complete canonical representation of a multi-page trial protocol document with 10 canonical extraction edge-cases | `TrialDocument` |
| `document_extraction_contract.json` | Downstream output contract envelope wrapping the processed document with extraction metadata | `DocumentExtractionContract` |

## Covered Canonical Scenarios (10 Required Patterns)

1. **Normal Inclusion Criterion:** Histologically confirmed Stage IV non-small cell lung cancer (`NCT02484404_INC_001`).
2. **Normal Exclusion Criterion:** Untreated or symptomatic central nervous system metastases (`NCT02484404_EXC_001`).
3. **Compound Criteria in One Sentence:** Multi-intent criterion ("Age >= 18 years and ECOG <= 1") decomposed into atomic constraints (`NCT02484404_INC_002`).
4. **Numeric Threshold:** Absolute neutrophil count >= 1.5 x 10^9/L with standard units (`NCT02484404_INC_003`).
5. **Temporal Requirement:** Washout window ("No chemotherapy within 28 days prior to Day 1") with `temporal_window_days=28` and `temporal_anchor="prior_to_day_1"` (`NCT02484404_EXC_002`).
6. **Categorical Requirement:** Pregnancy and lactation exclusion with contraceptive compliance (`NCT02484404_EXC_003`).
7. **Criterion with Clinical Ambiguity:** Subjective clinical discretion ("Adequate organ reserve in the opinion of the investigator") marked as `ambiguous` with domain `organ_function` (`NCT02484404_INC_004`).
8. **Criterion Blocked from Decomposition:** Complex conditional clinical logic ("LVEF >= 50% only in patients with prior doxorubicin > 300 mg/m2; otherwise cardiac evaluation not required") marked `can_decompose=False` with explicit clinical rationale (`NCT02484404_INC_005`).
9. **Multi-Page Source Text:** Sections spanning page 1 and page 2 (`page_start=1`, `page_end=2`) with accurate cross-page criterion provenance.
10. **Preserved Character Offsets:** Verifiable `start_char` and `end_char` matching exact substrings of section text.
