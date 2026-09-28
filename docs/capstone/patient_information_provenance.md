# MedMatch Capstone — Patient Information Provenance Specification

## 1. Executive Summary & Regulatory Context

In medical software and clinical trial matching, every extracted clinical fact must answer the foundational question:

> **"Where exactly in the patient record did this clinical information originate?"**

Under FDA Good Clinical Practice (GCP) and 21 CFR Part 11 guidance, clinical trial eligibility decisions require complete auditability and end-to-end source data verification (SDV). Black-box extraction models that output structured patient attributes without provenance links cannot be validated or trusted in clinical environments.

---

## 2. Provenance Architecture (`FactProvenance`)

Every `ClinicalFact` extracted by MedMatch must be accompanied by an immutable `FactProvenance` record:

```python
class FactProvenance(BaseModel):
    note_id: str = Field(..., description="Unique identifier of source note or document")
    patient_id: str = Field(..., description="Parent patient identifier")
    source_text: str = Field(..., min_length=1, description="Verbatim text span supporting the fact")
    start_char: Optional[int] = Field(
        default=None, ge=-1, description="0-based start character offset in source text (-1 if unavailable)"
    )
    end_char: Optional[int] = Field(
        default=None, ge=-1, description="0-based end character offset in source text (-1 if unavailable)"
    )
    source_section: Optional[str] = Field(
        default=None, description="Section heading in source note, e.g., 'Past Medical History'"
    )
    extraction_version: str = Field(default="0.4.0", description="Extraction engine software version")
    extraction_timestamp: str = Field(..., description="ISO-8601 UTC timestamp of extraction")
    model_identifier: Optional[str] = Field(
        default=None, description="Model ID or rule engine version that performed extraction"
    )
```

---

## 3. Strict Character Offset Rules

> [!CAUTION]
> **PROHIBITION AGAINST OFFSET FABRICATION**
> Extraction pipelines must **NEVER** fabricate character offsets. If text preprocessing, PDF extraction, or EHR summarization destroys exact character alignment, `start_char` and `end_char` must be explicitly set to `-1` (unmapped), while preserving the verbatim `source_text`.

### Validation Requirements
1. **Span Bounds Verification:** When `start_char >= 0` and `end_char > start_char`, the character span in the source note at `source_note.text[start_char:end_char]` must match `source_text` (allowing minor leading/trailing whitespace variations).
2. **Span Inversion Error:** Any fact where `start_char > end_char` constitutes a fatal structural error (`INVALID_CHARACTER_OFFSET_RANGE`).
3. **Multi-Note Aggregation:** When a patient clinical profile aggregates facts from multiple clinical encounters, each fact's `note_id` uniquely identifies the originating document.
