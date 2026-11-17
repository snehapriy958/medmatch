# Phase 16 Demo Data Plan

> **Phase:** 16 — Reproducibility & Final Hardening
> **Task:** Demo Data Planning (Tasks 1–5)
> **Audit Date:** 2026-09-30
> **Status:** READ-ONLY ANALYSIS — No files modified, no data created
> **Prerequisite:** DATA-16 audit (`docs/capstone/phase16_clinical_data_audit.md`)

---

## 1. Existing Trial Data

### 1.1 Production Trial Fixture

**One trial** is currently defined across all fixtures, tests, and evaluation data:

| Field | Value |
|:------|:------|
| **Trial ID** | `NCT02484404` |
| **Source** | ClinicalTrials.gov (real public trial identifier; used as fixture template) |
| **Official Title** | "Study of Osimertinib in Patients With Advanced Non-Small Cell Lung Cancer" |
| **Condition** | Non-Small Cell Lung Cancer (NSCLC) — Stage IV, Adenocarcinoma |
| **Intervention** | Osimertinib 80 mg oral daily (third-generation EGFR TKI; brand: TAGRISSO, FLAURA trial) |
| **Phase** | Phase 3 |
| **Fixture File** | `data/fixtures/trials.json` |
| **Source Attribution** | `"source": "clinicaltrials.gov"`, `"source_id": "NCT02484404"` |

#### Inclusion Criteria (8 total atomic criteria)

| Criterion ID | Domain | Criterion Text |
|:-------------|:-------|:---------------|
| `NCT02484404_INC_01` | `diagnosis_stage` | Histologically confirmed locally advanced or metastatic NSCLC (Stage IV) |
| `NCT02484404_INC_02` | `biomarker_genomics` | Documented EGFR sensitizing mutation (Exon 19 deletion or L858R) |
| `NCT02484404_INC_03` | `age` | Age ≥ 18 years |
| `NCT02484404_INC_04` | `performance_status` | ECOG performance status 0 or 1 |
| `NCT02484404_INC_05` | `laboratory_values` | Adequate hematologic function: Platelet count ≥ 100 × 10⁹/L |

#### Exclusion Criteria

| Criterion ID | Domain | Criterion Text |
|:-------------|:-------|:---------------|
| `NCT02484404_EXC_01` | `prior_treatment` | Prior treatment with third-generation EGFR-TKI |
| `NCT02484404_EXC_02` | `comorbidities` | Untreated or symptomatic CNS metastases |
| `NCT02484404_EXC_03` | `prior_treatment` | Cytotoxic chemotherapy completed within 28 days prior to Day 1 |

### 1.2 Synthetic Trials Referenced in Tests Only

The following trial IDs appear in test scaffolding but have **no fixture data** — they are local test mock objects only:

| Trial ID (in tests) | Location | Type |
|:--------------------|:---------|:-----|
| `NCT001`, `NCT002` | `tests/retrieval/test_retrieval_algorithms.py` | Toy pool for retrieval algo tests (NSCLC + Melanoma labels) |
| `NCT01234567` | `tests/eligibility/test_eligibility_schema.py` | Schema validation placeholder |
| `TRIAL-1`, `TRIAL-A`, `TRIAL-Z` | Various eligibility/aggregator tests | Schema/aggregation unit test placeholders |
| `NCT-PH9-001` through `NCT-PH9-003` | `data/fixtures/phase9/human_review_fixtures.json` | Abstract Phase 9 human review test cases |
| `NCT01`, `NCT02`, `NCT03` | `tests/explainability/test_explanation_generator.py` | Explanation generation unit tests |

**None of these are real or usable trial PDFs.** They are schema scaffolding only.

### 1.3 Retrieval Test — Additional Trial Conditions Mentioned

The retrieval test pool (`test_retrieval_algorithms.py`) includes:

- **NCT001:** NSCLC / osimertinib / EGFR-mutant — matches primary fixture condition
- **NCT002:** Cutaneous Melanoma / pembrolizumab — second disease for retrieval contrast
- **NCT003** (inferred from test pool): Prostate cancer — third disease for recall tests

These are **toy vectors** (e.g., `embedding=[0.9, 0.1, 0.0]`) with no eligibility data. They exist only to test that the retrieval engine correctly ranks and filters.

### 1.4 Phase 3 Fixture — Trial Document Schema

`data/fixtures/phase3/trial_document_fixture.json` provides a **richer document-level representation** of `NCT02484404` with:
- 10 canonical section/criterion extraction scenarios
- Multi-page source tracking (`page_start`, `page_end`)
- Character-level provenance (`start_char`, `end_char`)
- Atomic constraint decomposition examples
- Ambiguity and blocking annotations

**This is a schema fixture, not a live ingested trial.** It references a PDF at `protocols/NCT02484404_protocol.pdf` (placeholder path, file does not exist).

### 1.5 Safety Scenarios — Trial Referenced

`data/fixtures/phase12/safety_scenarios.json` references `NCT02484404` for all safety gate scenarios. The safety scenarios add one criterion not in the main fixture:
- `NCT02484404_EXC_04`: "Severe symptomatic dyspnea at rest" (exclusion — appears only in safety fixtures)

---

## 2. Existing Patient Data

### 2.1 Primary Patient Fixture (`data/fixtures/patients.json`)

Six synthetic oncology patients — all `"source": "synthetic"`, all NSCLC-focused, zero PHI:

| Patient ID | Age | Sex | Condition | Key Biomarkers | ECOG | Platelets | Prior Chemo | Scenario Label |
|:-----------|:----|:----|:----------|:---------------|:-----|:----------|:------------|:---------------|
| `SYN_P001` | 62 | F | Stage IV NSCLC (Adenocarcinoma) | EGFR Exon 19 del | 0 | 185 | Carboplatin/Pemetrexed (45 d ago) | **Clearly Eligible** |
| `SYN_P002` | 58 | M | Stage IV NSCLC | KRAS G12C, EGFR wild-type | 2 | (not specified) | None | **Clearly Ineligible** |
| `SYN_P003` | 65 | F | Advanced Lung Cancer | EGFR Pending | 1 | 210 | None | **NEEDS_REVIEW (missing info)** |
| `SYN_P004` | 70 | M | Stage IV NSCLC | EGFR L858R (tissue+) / EGFR neg (liquid biopsy conflict) | 1 | 155 | None | **NEEDS_REVIEW (conflicting evidence)** |
| `SYN_P005` | 54 | F | Metastatic Stage IV NSCLC | EGFR Exon 19 del | 1 | 99 | Chemo 60 d ago | **INELIGIBLE (boundary: platelets 99 < 100)** |
| `SYN_P006` | 61 | M | Stage IV NSCLC | EGFR L858R | 0 | 205 | Carbo/Paclitaxel (27 d ago) | **INELIGIBLE (temporal: 27 d < 28 d washout)** |

### 2.2 Ground Truth Eligibility Labels (`data/fixtures/trial_labels.json`)

All 6 patients evaluated against `NCT02484404`:

| Patient | Trial | Decision | Fail Reason |
|:--------|:------|:---------|:------------|
| `SYN_P001` | NCT02484404 | **ELIGIBLE** | All 8 criteria PASS |
| `SYN_P002` | NCT02484404 | **INELIGIBLE** | Fails EGFR inclusion + ECOG inclusion |
| `SYN_P003` | NCT02484404 | **NEEDS_REVIEW** | EGFR status UNKNOWN + Brain MRI not documented |
| `SYN_P004` | NCT02484404 | **NEEDS_REVIEW** | EGFR contradictory (tissue positive vs. liquid negative) |
| `SYN_P005` | NCT02484404 | **INELIGIBLE** | Platelet count 99 fails ≥ 100 × 10⁹/L |
| `SYN_P006` | NCT02484404 | **INELIGIBLE** | Chemo 27 days ago violates 28-day washout |

### 2.3 Phase 4 Fixture — Richer Patient Profile (`data/fixtures/phase4/patient_clinical_profile_fixture.json`)

`PATIENT_SYNTH_001` (63 M, NSCLC adenocarcinoma, EGFR Exon 19 del) provides the richest patient representation with:
- 16 canonical clinical fact scenarios (negation, temporality, uncertainty, conflicting)
- Character-level provenance into the clinical note
- Active medication: Amlodipine 5mg (anti-hypertensive — tests drug interaction awareness)
- Historical treatment: Carboplatin/Pemetrexed completed
- Brain MRI: No evidence of intracranial metastases (documented ABSENT)
- Missing information: PD-L1 status not stated

### 2.4 Safety Fixture Patients (`data/fixtures/phase12/safety_scenarios.json`)

Named `SYN_SAFE_01` through `SYN_SAFE_12+` — abstract scenario-only patients for testing safety gates. Not intended as demo patients.

### 2.5 Phase 9 Human Review Fixture Patients

Named `PT-PH9-01` through `PT-PH9-xx` — abstract uncertainty/routing test patients. Not demo patients.

### 2.6 Coverage Assessment Against Demo Scenario Types

| Scenario Type | Covered? | Patient(s) | Notes |
|:-------------|:---------|:-----------|:------|
| ✅ Clearly eligible | **Yes** | `SYN_P001` | Full PASS on all 8 criteria |
| ✅ Clearly ineligible (biomarker) | **Yes** | `SYN_P002` | EGFR wild-type + poor ECOG |
| ✅ Uncertain / borderline | **Yes** | `SYN_P003`, `SYN_P004` | Missing info + conflicting evidence |
| ✅ Numerical boundary | **Yes** | `SYN_P005` | Platelets 99 vs ≥ 100 |
| ✅ Temporal boundary | **Yes** | `SYN_P006` | 27-day vs 28-day washout |
| ❌ No suitable trial available | **No** | — | No patient has a non-NSCLC condition for which no trial exists in the corpus |
| ❌ Complex multi-comorbidity | **Partial** | `PATIENT_SYNTH_001` (Phase 4 only) | Richer but not wired into main fixture |
| ❌ Paediatric / rare oncology | **No** | — | All patients are adults with NSCLC |

**Key gap:** The entire current dataset is scoped to NSCLC with EGFR mutations. There is only **one trial** (`NCT02484404`). A retrieval demo requires at least 2–3 trials covering different conditions so that semantic retrieval has multiple candidates to rank.

---

## 3. Trial → Patient Scenario Mapping

### 3.1 Current State (Single Trial)

```
NCT02484404 (Osimertinib / NSCLC / EGFR)
├── SYN_P001 → ELIGIBLE          (Scenario A: clean match, all criteria satisfied)
├── SYN_P002 → INELIGIBLE        (Scenario B: wrong biomarker + poor performance status)
├── SYN_P003 → NEEDS_REVIEW      (Scenario C: missing biomarker data)
├── SYN_P004 → NEEDS_REVIEW      (Scenario D: conflicting EGFR evidence)
├── SYN_P005 → INELIGIBLE        (Scenario E: numeric boundary — platelet count)
└── SYN_P006 → INELIGIBLE        (Scenario F: temporal washout violation)
```

**This single-trial mapping is sufficient for eligibility reasoning demo.** It is NOT sufficient for a retrieval demo, because retrieval requires a corpus of multiple trials to demonstrate ranking, precision, and recall.

### 3.2 Conceptual Mapping — What Additional Trials Would Enable

To demonstrate the **semantic retrieval** and **"no suitable trial"** capabilities, 2–4 additional trials are needed:

```
Trial B (Different condition — e.g., KRAS G12C NSCLC / Sotorasib or AMG-510)
├── SYN_P002 → ELIGIBLE          (SYN_P002 has KRAS G12C — currently ineligible for Trial A, eligible for Trial B)
└── [retrieval correctly surfaces Trial B for SYN_P002, not Trial A]

Trial C (Different condition — e.g., Pembrolizumab / PD-L1+ NSCLC)
├── SYN_P001 → POSSIBLY_ELIGIBLE (if PD-L1 status were added)
└── [demonstrates retrieval contrast between EGFR-targeted vs IO therapy)

Trial D (Unrelated condition — e.g., HER2+ Breast Cancer)
└── [no NSCLC patients match → demonstrates "no suitable trial" scenario]
```

### 3.3 Complete Conceptual Trial→Patient Matrix

| Trial | Condition | SYN_P001 | SYN_P002 | SYN_P003 | SYN_P004 | SYN_P005 | Demo Capability |
|:------|:----------|:--------:|:--------:|:--------:|:--------:|:--------:|:----------------|
| NCT02484404 (EGFR/Osimertinib) | NSCLC | ✅ ELIGIBLE | ❌ INELIG | ❓ REVIEW | ❓ REVIEW | ❌ INELIG | Eligibility reasoning, uncertainty |
| Trial B (KRAS G12C) | NSCLC | ❌ INELIG | ✅ ELIGIBLE | ❓ PENDING | ❌ INELIG | ❓ PENDING | Biomarker specificity, retrieval contrast |
| Trial C (Pembrolizumab/PD-L1) | NSCLC | ❓ PENDING | ❌ INELIG | ❓ PENDING | ❓ PENDING | ❓ PENDING | Missing info scenario, IO vs TKI |
| Trial D (HER2+ Breast) | Breast Cancer | ❌ INELIG | ❌ INELIG | ❌ INELIG | ❌ INELIG | ❌ INELIG | No suitable trial scenario |

> **Note:** ❓ PENDING indicates a patient scenario that would require augmented patient notes to evaluate properly — the current synthetic notes are NSCLC-focused but lack PD-L1, KRAS-specific detail for non-NCT02484404 trials.

---

## 4. Recommended Final Demo Dataset

### 4.1 Recommended Clinical Trial PDFs (3 trials minimum, 4 for full coverage)

#### Trial 1 — PRIMARY (Already In Fixture)
| Field | Value |
|:------|:------|
| **Recommended ID** | NCT02484404 |
| **Condition** | Stage IV NSCLC |
| **Intervention** | Osimertinib (EGFR TKI) |
| **Demo Purpose** | Anchor trial; all 6 existing patients are pre-labeled against this trial; demonstrates full eligibility pipeline including numerical boundaries, temporal washout, conflicting evidence, and uncertainty |
| **Key Inclusion Characteristics** | EGFR Exon 19 del or L858R; ECOG 0–1; Platelets ≥ 100 |
| **Key Exclusion Characteristics** | Prior 3rd-gen EGFR-TKI; active CNS mets; chemo < 28 days |
| **Demonstrates** | Document ingestion, criteria extraction, eligibility reasoning, evidence/explanation, uncertainty, numeric/temporal logic |
| **Patient Scenarios** | SYN_P001 (eligible), SYN_P002 (ineligible), SYN_P003 (uncertain), SYN_P004 (conflicting), SYN_P005 (boundary), SYN_P006 (temporal) |

#### Trial 2 — RETRIEVAL CONTRAST (New — Not Yet In Fixture)
| Field | Value |
|:------|:------|
| **Recommended Condition** | Stage IV NSCLC, KRAS G12C mutation |
| **Candidate Intervention** | Sotorasib (AMG-510) / Adagrasib (MRTX849) |
| **Candidate Real NCT IDs** | NCT03600883 (CodeBreak 100 — Sotorasib Phase 1/2), or NCT03785249 (KRYSTAL-1 — Adagrasib) |
| **Demo Purpose** | Demonstrates that retrieval correctly surfaces a different trial for SYN_P002 (KRAS G12C patient currently INELIGIBLE for Trial 1); demonstrates biomarker-specific retrieval discrimination |
| **Key Inclusion Characteristics** | KRAS G12C mutation; NSCLC; ≥1 prior therapy |
| **Key Exclusion Characteristics** | Prior KRAS G12C inhibitor; active CNS mets |
| **Demonstrates** | Semantic retrieval ranking (EGFR query → Trial 1 ranked higher; KRAS query → Trial 2 ranked higher); specificity of biomarker extraction |
| **Patient Scenarios** | SYN_P002 (eligible for Trial 2, ineligible for Trial 1 — demonstrates retrieval personalization) |

#### Trial 3 — IMMUNOTHERAPY CONTRAST (New — Not Yet In Fixture)
| Field | Value |
|:------|:------|
| **Recommended Condition** | Stage IV NSCLC, PD-L1 high (TPS ≥ 50%) |
| **Candidate Intervention** | Pembrolizumab (KEYNOTE-024 / NCT02142738) |
| **Demo Purpose** | Demonstrates a third therapeutic class (checkpoint inhibitor vs. EGFR-TKI vs. KRAS inhibitor); highlights "missing information" scenario — current patients do not document PD-L1 status, so this trial would trigger NEEDS_REVIEW for multiple patients |
| **Key Inclusion Characteristics** | Histologically confirmed NSCLC; PD-L1 TPS ≥ 50%; no sensitizing EGFR/ALK |
| **Key Exclusion Characteristics** | EGFR/ALK genomic aberrations (excludes SYN_P001, SYN_P005 directly); active autoimmune disease |
| **Demonstrates** | Automatic INELIGIBLE for EGFR-positive patients (exclusion triggered); NEEDS_REVIEW for patients without PD-L1 status documented; multi-trial retrieval where one trial definitively excludes based on biomarker |
| **Patient Scenarios** | SYN_P001/SYN_P005 (excluded due to EGFR+); SYN_P002 (no EGFR — potentially eligible if PD-L1 added); SYN_P003 (missing PD-L1 → NEEDS_REVIEW) |

#### Trial 4 — DIFFERENT DISEASE (New — For "No Suitable Trial" Demo)
| Field | Value |
|:------|:------|
| **Recommended Condition** | HER2-positive Breast Cancer OR Colorectal Cancer BRAF V600E |
| **Candidate Intervention** | Trastuzumab deruxtecan (HER2BC), or Encorafenib + Cetuximab (BRAF CRC) |
| **Demo Purpose** | Provides a trial that is entirely non-overlapping with any current patient profile; retrieval should rank it last for all 5 NSCLC patients; demonstrates the "no suitable trial" path cleanly |
| **Key Inclusion Characteristics** | Unambiguous non-NSCLC condition (HER2+ breast, or CRC BRAF V600E) |
| **Demonstrates** | Zero retrieval match for all current patients; clean "no suitable trial" outcome |
| **Patient Scenarios** | None (intended to return empty/no match for all NSCLC patients) |

### 4.2 Recommended Patient Clinical Notes (5 Scenarios)

The 5 core patient note scenarios needed for the demo are already fully defined in the existing fixtures. No new patients need to be created.

| Scenario | Patient ID | Clinical Purpose | Clinical Characteristics |
|:---------|:-----------|:-----------------|:------------------------|
| **1. Clearly Eligible** | `SYN_P001` | Demonstrates clean ELIGIBLE outcome; all criteria satisfied; grounded explanation | 62F, Stage IV NSCLC, EGFR Exon 19 del, ECOG 0, Platelets 185, chemo 45 d ago, brain MRI clear |
| **2. Clearly Ineligible** | `SYN_P002` | Demonstrates INELIGIBLE due to wrong biomarker AND poor performance status | 58M, Stage IV NSCLC, KRAS G12C, EGFR wild-type, ECOG 2 |
| **3. Uncertain (Missing Data)** | `SYN_P003` | Demonstrates NEEDS_REVIEW when key information is absent (biomarker pending) | 65F, Advanced lung cancer, EGFR Pending, ECOG 1, no prior chemo, no brain MRI |
| **4. Uncertain (Conflicting Evidence)** | `SYN_P004` | Demonstrates NEEDS_REVIEW when evidence contradicts itself | 70M, Stage IV NSCLC, tissue EGFR L858R+ vs liquid biopsy EGFR negative — conflict |
| **5. Complex / Boundary** | `SYN_P005` OR `SYN_P006` | Demonstrates precise numerical/temporal reasoning and INELIGIBLE at the boundary | P005: Platelets 99 (1 below threshold); P006: Chemo 27 days ago (1 below washout window) |

> **Recommendation:** Use **both** SYN_P005 and SYN_P006 — they demonstrate two distinct boundary reasoning types (numerical vs. temporal) and are already annotated. This gives a 6-patient demo set aligned exactly with the existing fixture, with zero new data required.

---

## 5. Data Provenance / Licensing Requirements

### 5.1 Trial 1 — NCT02484404 (Existing Fixture Source)

| Question | Answer |
|:---------|:-------|
| **Real trial?** | Yes — AstraZeneca FLAURA trial (Osimertinib Phase 3 NSCLC) |
| **Eligibility text provenance** | ClinicalTrials.gov API v2 (public domain, U.S. government work) |
| **License** | Public Domain — no restrictions |
| **Redistribution** | Permitted (unrestricted for academic/demo use) |
| **PDF option** | ClinicalTrials.gov provides a structured JSON record, not a PDF protocol. The full FDA/ICH protocol PDF is not publicly available. A publicly accessible ClinicalTrials.gov "study document" or the published FLAURA NEJM paper describes eligibility criteria. |
| **What IS available publicly** | The ClinicalTrials.gov study page, eligibility criteria text — sufficient for demo PDF generation from eligibility text |
| **Risk** | Low — eligibility criteria text is explicitly public domain under U.S. law |

### 5.2 Trials 2, 3, 4 — New Trials

| Source Type | Provenance | License | PDF Availability | Risk |
|:------------|:-----------|:--------|:-----------------|:-----|
| **ClinicalTrials.gov API v2 JSON** | Public domain (NLM/NIH) | Unrestricted | No PDF directly; structured JSON | None |
| **Published clinical trial protocol** (journal supplement) | Copyright publisher (NEJM, Lancet, JAMA) | Requires permission for redistribution | Yes, if open-access; restricted if paywalled | Moderate — must verify OA status per paper |
| **FDA NDA/BLA submission documents** (public) | Public domain once published on FDA.gov | Unrestricted for published docs | Yes (fda.gov/drugs, drugs@FDA) | Low |
| **Synthetic trial document** (generated from eligibility criteria text) | Fully synthetic; no copyright claim | Project license (Apache 2.0) | Generated as needed | None |
| **ClinicalTrials.gov study protocol PDFs** (when uploaded by sponsor) | Uploaded by trial sponsor; no explicit license stated in all cases | Generally permissible for educational/research use | Sometimes available as attachments on CT.gov | Low, but verify per trial |

### 5.3 Recommended Approach for PDFs

> **Important:** The production pipeline accepts any PDF with extractable clinical trial text. The PDF is parsed by `pymupdf`, text extracted, and Gemini structures the eligibility criteria. **The PDF format is a transport container — the legal constraint is on the text content, not the file format.**

**Recommended source type for final demo PDFs:**

**Synthetic trial documents generated from public-domain eligibility criteria text**, in a format that mimics a clinical protocol structure. Specifically:

1. Take the publicly available eligibility criteria text from ClinicalTrials.gov (public domain).
2. Wrap it in a synthetic protocol document with appropriate section headings (Title, Brief Summary, Eligibility Criteria, Inclusion, Exclusion) — no clinical trial sponsor branding.
3. The resulting synthetic document is fully owned by the project, carries no copyright risk, and is legally clean for repository inclusion.

This is the same approach used for `medmatch_test_trial.txt` (in the stash), but applied rigorously and with proper clinical structure for the demo.

**This approach requires:**
- No internet download of proprietary PDFs
- No reproduction of journal-published text
- No use of FDA submission documents
- Only public-domain eligibility criteria from ClinicalTrials.gov, reformatted into a clean synthetic protocol document

### 5.4 Patient Data Provenance

All 6 patient records are `"source": "synthetic"`, generator-derived, zero PHI. No provenance checks needed — fully owned by the project.

---

## 6. What Is Missing

### 6.1 Missing for a Complete Demo

| Gap | Severity | Description |
|:----|:---------|:------------|
| **No Trial PDFs** | 🔴 Critical | Zero clinical trial PDFs exist. The entire PDF ingestion → criteria extraction → embedding → matching pipeline cannot be demonstrated end-to-end without at least one trial PDF uploaded. |
| **Only 1 Trial in Corpus** | 🔴 Critical | Semantic retrieval cannot be meaningfully demonstrated with a single trial — a retrieval demo requires ≥3 trials covering different conditions/biomarkers so the system can differentiate and rank. |
| **No "No Suitable Trial" Patient** | 🟡 Important | No current patient has a non-NSCLC condition. Trial D (different disease) would create this scenario but needs a patient note too — although all NSCLC patients would demonstrate "not matching Trial D." |
| **SYN_P002 not linked to any eligible trial** | 🟡 Important | SYN_P002 (KRAS G12C, EGFR wild-type) is currently INELIGIBLE for the only trial. A KRAS G12C trial (Trial B) would make SYN_P002 eligible and complete the demo story. |
| **No PD-L1 status in existing patient notes** | 🟡 Important | Pembrolizumab (Trial C, PD-L1-based) requires PD-L1 status. None of the 6 patients document it — all would be NEEDS_REVIEW for Trial C, which is itself a valid demo scenario but not a clean ELIGIBLE outcome. |
| **Phase 4 rich patient fixture not wired into runtime** | 🟢 Low | `PATIENT_SYNTH_001` in `data/fixtures/phase4/` has a richer profile but is not in the primary `data/fixtures/patients.json` used by the seed pipeline. |

### 6.2 What Is NOT Missing

| Capability | Status |
|:-----------|:-------|
| PDF ingestion pipeline | ✅ Fully implemented (PDFService + TrialService + Celery) |
| Eligibility reasoning | ✅ Fully implemented (MatchingService + LLM) |
| Patient note submission | ✅ Fully implemented (PatientNoteService API) |
| Embedding + vector retrieval | ✅ Fully implemented (pgvector, all-MiniLM-L6-v2) |
| Uncertainty/NEEDS_REVIEW routing | ✅ Fully implemented |
| 6 annotated patient scenarios | ✅ Complete with character-level evidence |
| 8 atomic criteria for primary trial | ✅ Complete |
| Safety gates | ✅ Implemented and tested |

---

## 7. What Must NOT Be Changed

The following must not be modified under any circumstance as part of demo data preparation:

| Item | Reason |
|:-----|:-------|
| `data/fixtures/patients.json` | Production seed data; all tests and validators depend on exact character offsets in clinical notes |
| `data/fixtures/trials.json` | All criterion labels reference this trial's exact structure |
| `data/fixtures/criteria.json` | 48 criterion evaluations in `criterion_labels.json` reference exact criterion IDs |
| `data/fixtures/criterion_labels.json` | 48 annotated patient-criterion pairs with character-level provenance |
| `data/fixtures/trial_labels.json` | 6 ground-truth trial-level decisions used by automated validators |
| `data/manifests/checksums.sha256` | Must be updated only if fixture content changes (and only with explicit approval) |
| `data/splits/*.jsonl` | Dataset partition structure used by evaluation harness |
| `services/ai-service/app/` (all production code) | No clinical logic modifications permitted |
| Gemini prompts | Not to be modified without explicit approval |
| Eligibility reasoning logic | Not to be modified without explicit approval |
| Database schema / Alembic migrations | Not to be modified |

---

## DEMO DATA STATUS

```
══════════════════════════════════════════════════════════════════════
DEMO DATA STATUS
══════════════════════════════════════════════════════════════════════

TRIAL DATA:              PARTIAL
                         1 trial defined in fixtures (NCT02484404,
                         NSCLC/Osimertinib). Eligibility criteria
                         complete and annotated. ZERO trial PDFs
                         exist. Retrieval demo requires 2–3 additional
                         trials (different conditions/biomarkers).
                         Recommended additions:
                           Trial B: KRAS G12C NSCLC (Sotorasib)
                           Trial C: PD-L1+ NSCLC (Pembrolizumab)
                           Trial D: Different disease (non-NSCLC)

PATIENT DATA:            PARTIAL
                         6 synthetic NSCLC patients fully annotated
                         against Trial A (NCT02484404). Cover 5 of 6
                         required demo scenarios. Missing: a patient
                         with a non-NSCLC condition (for "no suitable
                         trial" scenario). Existing 6 patients are
                         sufficient for eligibility demo; additional
                         trials would unlock SYN_P002 as eligible.

FINAL PDF REQUIREMENT:   YES
                         3–4 clinical trial PDFs required for full
                         end-to-end demo. None currently exist.
                         Recommended source: synthetic documents
                         composed from public-domain eligibility
                         criteria text (ClinicalTrials.gov, public
                         domain). No proprietary text to be used.
                         No downloads from journals/FDA required.

PATIENT PDF REQUIREMENT: NO
                         Patient records enter MedMatch as structured
                         text via POST /patients/{id}/notes. No patient
                         PDF pipeline exists or is needed.

CODE CHANGES:            NONE
══════════════════════════════════════════════════════════════════════
```
