# MedMatch Capstone — Phase 3: Clinical Trial Document Pipeline Audit

> **Status:** Phase 3 Baseline Audit Document  
> **Phase:** 3 — Clinical Trial Document Intelligence  
> **Author:** MedMatch Research Team  
> **Date:** September 2026  
> **Target System:** MedMatch Clinical Trial Ingestion & Intelligence Pipeline

---

## 1. Executive Summary

This audit assesses the existing clinical-trial document ingestion architecture in MedMatch (`services/ai-service`). The current production implementation provides basic end-to-end functionality—uploading a PDF, extracting raw text using PyMuPDF, querying Google Gemini for structured metadata and criteria lists, and persisting basic trial and criteria records in PostgreSQL with pgvector embeddings.

However, from a clinical informatics and research perspective, the current document pipeline contains critical structural deficiencies:
1. **Provenance Obliteration:** Page numbers, section boundaries, and character spans are discarded during text extraction and cleaning.
2. **Unstructured Criterion Descriptions:** Criteria are treated as monolithic free-text strings without atomic decomposition, domain categorization, or numerical/temporal constraint extraction.
3. **Compound Criterion Entanglement:** Multi-intent criteria (e.g., combining age, performance status, and organ function into one sentence) are preserved as single unparsed strings, obstructing fine-grained downstream matching.
4. **Lack of Section Disambiguation:** Extraction relies entirely on generative LLM attention without deterministic section-header detection or validation of ambiguous criteria.
5. **No Extraction Quality Verification:** Extraction outputs bypass programmatic validation; malformed or ungrounded criteria enter the database without schema constraint checking.

---

## 2. End-to-End Current Pipeline Architecture

```text
+---------------------------------------------------------------------------------------------------------+
|                                    CURRENT DOCUMENT PIPELINE FLOW                                       |
+---------------------------------------------------------------------------------------------------------+
                                                     |
                                                     v
                                       [1. PDF Upload Endpoint]
                                       POST /api/trials/upload
                                       (services/ai-service/app/api/routes/trial.py)
                                                     |
                                                     v
                                       [2. PDF File Storage & Magic Check]
                                       PDFService.save_pdf() -> uploads/{uuid}.pdf
                                       Validates %PDF- signature and page_count > 0
                                                     |
                                                     v
                                       [3. Asynchronous Celery Dispatch]
                                       process_trial.delay(file_path, hospital_id)
                                       (services/ai-service/app/celery/tasks.py)
                                                     |
                                                     v
                                       [4. Text Extraction via PyMuPDF]
                                       PDFService.extract_text()
                                       pages = [page.get_text() for page in doc]
                                       text = "\n".join(pages).strip()
                                       * Page boundaries discarded *
                                                     |
                                                     v
                                       [5. Text Cleaning]
                                       TextCleaner.clean()
                                       Strips whitespace and page headers:
                                       re.sub(r"(?im)^page\s+\d+\s*$", "", text)
                                       * Destroys remaining pagination markers *
                                                     |
                                                     v
                                       [6. Generative LLM Extraction]
                                       LLMService.extract_trial_information()
                                       TRIAL_EXTRACTION_PROMPT -> Gemini 2.5 Flash
                                       Outputs Pydantic TrialExtraction:
                                       - title, phase, condition, sponsor, status
                                       - inclusion_criteria: list[str]
                                       - exclusion_criteria: list[str]
                                                     |
                                                     v
                                       [7. Deduplication & Persistence]
                                       TrialService.process_pdf()
                                       - Trial entity created in PostgreSQL
                                       - TrialCriteria entities created (description: str)
                                       - sentence-transformers/all-MiniLM-L6-v2 embeddings
                                       - Temp PDF deleted: _remove_temp_pdf()
```

---

## 3. Detailed Component Audit & Code Locations

### 3.1 PDF Storage and Validation (`app/services/pdf_service.py`)
- **Location:** `services/ai-service/app/services/pdf_service.py`
- **Mechanism:** Inspects file extension (`.pdf`), verifies `%PDF-` magic header, ensures file size $\le 50\text{MB}$, opens document via `pymupdf.open()`, and asserts `document.page_count > 0`.
- **Extraction Method:**
  ```python
  pages = [page.get_text() for page in document]
  text = "\n".join(pages).strip()
  ```
- **Audit Evaluation:** Fast and robust against malformed files, but discards page numbering, bounding boxes, font attributes, and per-page character offsets.

### 3.2 Text Cleaning (`app/services/text_cleaner.py`)
- **Location:** `services/ai-service/app/services/text_cleaner.py`
- **Regex Patterns:**
  ```python
  _PAGE_NUMBER_PATTERN = re.compile(r"(?im)^page\s+\d+\s*$")
  _MULTIPLE_BLANK_LINES_PATTERN = re.compile(r"\n{2,}")
  _MULTIPLE_SPACES_PATTERN = re.compile(r"[ \t]+")
  ```
- **Audit Evaluation:** Normalizes whitespace effectively, but explicitly strips page numbers, permanently preventing downstream components from identifying which page an extracted criterion originated from.

### 3.3 LLM Extraction Schema (`app/schemas/trial_extraction.py`)
- **Location:** `services/ai-service/app/schemas/trial_extraction.py`
- **Data Model:**
  ```python
  class TrialExtraction(BaseModel):
      title: str
      phase: str
      condition: str
      sponsor: str
      recruitment_status: str
      inclusion_criteria: list[Annotated[str, StringConstraints(min_length=1, max_length=2000)]]
      exclusion_criteria: list[Annotated[str, StringConstraints(min_length=1, max_length=2000)]]
  ```
- **Audit Evaluation:** Highly generic. Criteria are strings without domain tags, numerical boundaries, temporal constraints, or source citations.

### 3.4 LLM Extraction Prompt (`app/prompts/trial_extraction_prompt.py`)
- **Location:** `services/ai-service/app/prompts/trial_extraction_prompt.py`
- **Structure:** 42 lines. Instructs Gemini to return JSON with `inclusion_criteria` and `exclusion_criteria` lists.
- **Audit Evaluation:** Lacks instructions for atomic decomposition, handling compound sentences, preserving exact verbatim quotes, or tagging clinical uncertainty/ambiguity.

### 3.5 Database Entities & Persistence (`app/models/trial.py`, `app/models/trial_criteria.py`)
- **Database Tables:** `trials`, `trial_criteria`, `trial_criteria_embeddings`, `trial_embeddings`.
- **Columns in `trial_criteria`:** `id`, `trial_id`, `criteria_type` (`INCLUSION`/`EXCLUSION`), `description` (`Text`), `created_at`, `updated_at`.
- **Audit Evaluation:** No database columns exist for:
  - `section_id` or section header
  - `page_number` or page span
  - `start_char` or `end_char` offset
  - `domain` (e.g., genomics, labs, performance status)
  - `is_atomic` or decomposed sub-criteria relations
  - `extraction_confidence`

---

## 4. Current Failure Modes & Limitations

| Failure Mode ID | Failure Category | Root Cause in Current Architecture | Impact on Downstream System |
|---|---|---|---|
| **FM-1** | Provenance Amnesia | `extract_text` concatenates pages; `TextCleaner` removes page markers. | Unable to show clinicians the exact PDF page or paragraph backing a criterion. |
| **FM-2** | Compound Rule Entanglement | Prompt asks for lists of criteria; does not instruct atomic decomposition. | "Age $\ge 18$, ECOG 0-1, ANC $\ge 1.5$" is stored as one string. Failure on ANC fails entire rule without granular attribution. |
| **FM-3** | Section Misattribution | Pure generative grouping without deterministic section detection. | Narrative preamble or study overview text occasionally hallucinated as an inclusion rule. |
| **FM-4** | Numerical & Temporal Blindness | No structured extraction of comparators, values, units, or washout days. | Downstream matcher must repeatedly re-parse text strings with generative LLM, risking arithmetic errors. |
| **FM-5** | Ambiguity Suppression | Model forced to classify every rule as strictly inclusion or exclusion. | Ambiguous subjective criteria ("at investigator's discretion") cannot be flagged for manual review. |
| **FM-6** | Silent Validation Failure | Extraction schema only checks string length $\le 2000$ chars. | Malformed, duplicate, or hallucinated criteria enter PostgreSQL without validation alarms. |

---

## 5. Scope & Additions for Phase 3

To resolve these architectural limitations without breaking existing production routes, Phase 3 implements:
1. **Canonical Trial Document Schema:** Strongly typed representations of `TrialDocument`, `TrialSection`, and `TrialCriterion` preserving multi-page hierarchy and provenance.
2. **Atomic Criterion Representation:** A structured research data model capturing concepts, comparators (`>=`, `<=`, `==`), values, units, and temporal constraints, with explicit rules for when decomposition is NOT safe.
3. **Deterministic Section Normalizer:** Rule-based detection and taxonomic normalization of common protocol eligibility headings.
4. **Stable Extraction Output Contract:** Strongly typed contract decoupling document extraction from downstream retrieval and reasoning.
5. **Deterministic Extraction Validator:** Automated validation suite detecting orphan sections, duplicate IDs, invalid offsets, unsupported operators, and malformed criteria.
6. **Controlled Development Fixtures:** Multi-scenario fixture illustrating all 10 canonical document extraction patterns.
