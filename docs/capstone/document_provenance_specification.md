# MedMatch Capstone — Document Provenance & Evidence Attribution Specification

> **Status:** Phase 3 Research Specification  
> **Phase:** 3 — Clinical Trial Document Intelligence  
> **Author:** MedMatch Research Team  
> **Date:** September 2026  
> **Target System:** MedMatch Document Intelligence Engine

---

## 1. Provenance Mandate & Research Requirement

In clinical oncology decision support, presenting a criterion determination without verifiable provenance creates severe clinical liability. When an oncologist or research nurse reviews a patient match, they must be able to immediately verify:

> **"Where exactly in the trial protocol does this criterion come from, on what page, in which section, and what was the verbatim wording?"**

The baseline MedMatch pipeline (Phase 0) discarded all pagination and section provenance during PDF extraction. Phase 3 establishes an immutable, bidirectional provenance chain linking every extracted criterion back to its source protocol location.

---

## 2. The Multi-Tier Provenance Architecture

```text
+---------------------------------------------------------------------------------------------------------+
|                                    BIDIRECTIONAL PROVENANCE CHAIN                                       |
+---------------------------------------------------------------------------------------------------------+
                                                     |
                                                     v
                            [Tier 1: Document Level (TrialDocument)]
                            - document_id: "DOC_NCT02484404_001"
                            - trial_id: "NCT02484404"
                            - source_uri: "uploads/protocols/NCT02484404_protocol.pdf"
                            - document_hash: "a4f8c2b918d3..." (SHA-256)
                            - extraction_version: "0.3.0"
                                                     |
                                                     v
                            [Tier 2: Section Level (TrialSection)]
                            - section_id: "SEC_002"
                            - section_type: "INCLUSION_CRITERIA"
                            - heading: "Section 4.1: Subject Inclusion Criteria"
                            - page_start: 14, page_end: 16
                            - source_order: 2
                                                     |
                                                     v
                            [Tier 3: Criterion Level (TrialCriterion)]
                            - criterion_id: "NCT02484404_INC_003"
                            - raw_text: "Age >= 18 years at the time of screening."
                            - normalized_text: "Age >= 18 years"
                            - is_atomic: True
                                                     |
                                                     v
                            [Tier 4: Provenance Object (CriterionProvenance)]
                            - page_number: 14
                            - start_char: 342, end_char: 384
                            - source_text: "Age >= 18 years at the time of screening."
```

---

## 3. Provenance Schema Fields & Verification Rules

Every extracted criterion MUST include a valid `CriterionProvenance` record conforming to `scripts/document_schema.py`:

```json
{
  "document_id": "DOC_NCT02484404_001",
  "trial_id": "NCT02484404",
  "section_id": "SEC_002",
  "page_number": 14,
  "start_char": 342,
  "end_char": 384,
  "source_text": "Age >= 18 years at the time of screening.",
  "extraction_version": "0.3.0"
}
```

### 3.1 Strict Character-Offset Verification Rule
Where character offsets (`start_char`, `end_char`) are provided and non-negative:
$$\text{assert } \text{section\_text}[\text{start\_char}:\text{end\_char}] == \text{source\_text}$$

If text normalization (e.g. whitespace collapsing) occurs between extraction and validation, the validator verifies that `source_text` is an exact substring of the parent section text.

### 3.2 Handling Real-World PDF Extraction Challenges
1. **Multi-Column Formatting:** Clinical trial PDFs frequently switch between single-column introductory text and dual-column criteria lists. Text extraction must group lines by geometric column blocks prior to computing character offsets.
2. **Hyphenation & Line Wraps:** Words split across line breaks (e.g. *"chemo-\ntherapy"*) are normalized while retaining the raw un-joined span in `source_text`.
3. **Scanned Documents & OCR Fallback:** For scanned PDFs lacking text streams, `page_number` remains authoritative while `start_char`/`end_char` are marked `-1` unless optical bounding boxes are computed.
4. **Header/Footer Bleed:** Running headers (e.g., *"Protocol AstraZeneca D4190C00006 - Page 14"*) must be stripped during section parsing to avoid contaminating criterion text spans.

---

## 4. Downstream Utilization in Later Phases

- **Phase 4 (Patient Intelligence):** Mirrors this provenance standard for clinical notes, extracting character spans from patient narratives.
- **Phase 5 (Reasoning & Grounding):** Downstream LLM matching generates bidirectional citations:
  $$\text{Match Result} \longrightarrow \langle \text{Patient Span: } N_P[120:165], \, \text{Protocol Span: } T_{\text{crit}}[342:384] \rangle$$
  Enabling instant, verifiable human clinical audit in the MedMatch UI.
