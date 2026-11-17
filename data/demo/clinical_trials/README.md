# MedMatch Demo — Clinical Trial PDF Documents

> **Directory:** `data/demo/clinical_trials/`
> **Purpose:** Synthetic demonstration documents for the MedMatch clinical trial matching system demo
> **Classification:** SYNTHETIC DEMO DATA — Not clinical-trial protocols
> **PHI:** None — these documents contain zero patient data
> **Created:** Phase 16 — Reproducibility & Final Hardening

---

## Contents

| File | Trial ID | Condition | Intervention |
|:-----|:---------|:----------|:-------------|
| `trial_A_NCT02484404_osimertinib_demo.pdf` | DEMO-A | Stage IV NSCLC, EGFR-mutant | Osimertinib 80 mg PO daily |
| `trial_B_KRAS_G12C_sotorasib_demo.pdf` | DEMO-B | Stage IV NSCLC, KRAS G12C | Sotorasib 960 mg PO daily |
| `trial_C_PDL1_pembrolizumab_demo.pdf` | DEMO-C | Stage IV NSCLC, PD-L1 TPS ≥ 50% | Pembrolizumab 200 mg IV q3w |

---

## Important Disclaimers

### These are NOT official clinical-trial protocols

Every PDF in this directory is clearly watermarked:

> **WARNING: SYNTHETIC DEMONSTRATION DOCUMENT — NOT AN OFFICIAL CLINICAL-TRIAL PROTOCOL**

- They are **not** regulatory submissions.
- They are **not** sponsor documents.
- They are **not** derived from any proprietary protocol text.
- They contain **no real patient data** and **no PHI**.

### Provenance by Trial

#### Trial A — `trial_A_NCT02484404_osimertinib_demo.pdf`

- **Synthetic ID:** DEMO-A
- **Reference:** NCT02484404 is a real ClinicalTrials.gov identifier (AstraZeneca FLAURA study, Osimertinib Phase 3 NSCLC). The identifier is referenced for traceability only.
- **Eligibility Criteria Source:** Derived from the existing MedMatch project fixture (`data/fixtures/trials.json`, `data/fixtures/criteria.json`). The criteria text in this PDF reflects the same eligibility logic already embedded in the project's annotated ground-truth dataset. No criteria were invented or altered from the fixture.
- **License:** The eligibility criteria text from ClinicalTrials.gov is in the public domain (U.S. government work, 17 U.S.C. § 105). No reproduction of proprietary protocol text.

#### Trial B — `trial_B_KRAS_G12C_sotorasib_demo.pdf`

- **Synthetic ID:** DEMO-B / SYNTH-KRAS-G12C-001
- **Source:** Fully synthetic document. No proprietary text reproduced.
- **Clinical basis:** Eligibility framework based on publicly available KRAS G12C inhibitor programme characteristics (published peer-reviewed literature; class-level eligibility logic). Not derived from any specific sponsor protocol.
- **Purpose:** Provides a biomarker-distinct trial (KRAS G12C vs. EGFR) enabling the MedMatch retrieval system to demonstrate semantic differentiation between biomarker-matched trials. Patient `SYN_P002` (KRAS G12C, EGFR wild-type) — currently ineligible for Trial A — is the intended match candidate for this trial.

#### Trial C — `trial_C_PDL1_pembrolizumab_demo.pdf`

- **Synthetic ID:** DEMO-C / SYNTH-PDL1-IO-001
- **Source:** Fully synthetic document. No proprietary text reproduced.
- **Clinical basis:** Eligibility framework based on publicly available PD-L1/checkpoint inhibitor NSCLC programme characteristics. Not derived from any specific sponsor protocol.
- **Purpose:** Provides an immunotherapy trial that explicitly **excludes** EGFR-mutant patients. This creates a demonstrably clean INELIGIBLE outcome for `SYN_P001`, `SYN_P005`, and `SYN_P006` (all EGFR-positive). It also triggers NEEDS_REVIEW for patients without documented PD-L1 status (`SYN_P003`, `SYN_P004`), demonstrating the missing-information uncertainty pathway.

---

## How These Files Are Used

These PDFs are intended to be **uploaded manually** through the MedMatch production PDF ingestion endpoint:

```
POST /api/ai/trials/upload
Content-Type: multipart/form-data
```

The endpoint validates the PDF, extracts text via `pymupdf`, structures the eligibility criteria via Gemini LLM, computes embeddings via `all-MiniLM-L6-v2`, and persists the trial to PostgreSQL/pgvector.

**Upload order for demo:** Trial A → Trial B → Trial C.

After upload, the six existing synthetic patients (`SYN_P001`–`SYN_P006`) can be matched against the ingested trial corpus.

---

## What Is NOT in This Directory

- No patient medical records
- No real de-identified patient data
- No real sponsor protocol documents
- No official ClinicalTrials.gov PDF downloads
- No journal-published protocol supplements

---

## Git Tracking

These demo PDFs **are** Git-tracked (in `data/demo/clinical_trials/`). This is intentional:

- They are synthetic, contain no PHI, and are safe for repository inclusion.
- They allow a clean repository clone to reproduce the demo without manual PDF creation.
- The runtime `uploads/` directory (where the ingestion pipeline stores processed files) remains Git-ignored as before.

The `.gitignore` pattern `/uploads/` applies only to the root `uploads/` directory and `services/ai-service/uploads/`, not to `data/demo/`.
