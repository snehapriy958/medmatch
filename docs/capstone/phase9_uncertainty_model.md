# Phase 9: Canonical Uncertainty Model Specification

## 1. Purpose

The MedMatch canonical uncertainty model establishes an explicit, strongly typed representation of epistemic uncertainty, data insufficiency, conflicting evidence, temporal ambiguity, and grounding failure across patient records and trial protocols.

Rather than treating uncertainty as a single catch-all flag or relying on probabilistic confidence scores, Phase 9 formalizes uncertainty into structured, verifiable records that link directly to clinical entities, provenance anchors, and downstream eligibility criteria.

---

## 2. Core Ontological Taxonomies

### 2.1 Uncertainty Status (`UncertaintyStatus`)
- **`RESOLVED`**: Deterministically confirmed by sufficient, congruent evidence.
- **`MISSING`**: Required clinical fact is not referenced anywhere in the patient record (`NOT_MENTIONED`).
- **`CONFLICTING`**: Multiple records or passages present incompatible clinical assertions or values.
- **`AMBIGUOUS`**: Vague phrasing, imprecise intervals, borderline thresholds, or qualitative language.
- **`STALE`**: Clinical datum exceeds the allowable temporal recency threshold of the trial protocol.
- **`LOW_CONFIDENCE`**: Documented clinical uncertainty (e.g. "suspected", "differential diagnosis") or retrieval relevance below cutoff.
- **`INSUFFICIENT_EVIDENCE`**: Available context is incomplete, preventing a definitive criterion decision.

### 2.2 Uncertainty Severity (`UncertaintySeverity`)
- **`LOW`**: Peripheral ambiguity that does not alter eligibility determination.
- **`MEDIUM`**: Affects secondary criteria; requires routine chart verification.
- **`HIGH`**: Blocks definitive automated determination of a primary criterion; requires human clinical review (`NEEDS_REVIEW`).
- **`CRITICAL`**: Active safety contradiction, conflicting contraindication, or major factual conflict; requires escalated review (`ESCALATED`).

### 2.3 Uncertainty Type (`UncertaintyType`)
1. `MISSING_PATIENT_FACT`: Unrecorded biomarker, staging, or laboratory measurement.
2. `CONFLICTING_PATIENT_FACTS`: Discordant assertions within the patient chart.
3. `CONFLICTING_DOCUMENTS`: Conflicting findings between disparate institutional documents.
4. `TEMPORAL_AMBIGUITY`: Indeterminate timeline, relative offsets without anchor dates.
5. `NUMERICAL_AMBIGUITY`: Borderline values, missing measurement units, conflicting assay bounds.
6. `UNSUPPORTED_INFERENCE`: Machine hallucination or unsupported speculative conclusion (H5/H8).
7. `GROUNDING_CONTRADICTION`: Machine claim inverting documented evidence (H6).
8. `INSUFFICIENT_RETRIEVAL`: Retriever failed to return required protocol chunks.
9. `STALE_CLINICAL_DATA`: Outdated laboratory or clinical assessment.

---

## 3. Detailed Data Structures

### 3.1 `ConflictEvidenceItem`
Captures each individual competing assertion in a clinical conflict:
```python
class ConflictEvidenceItem(BaseModel):
    source_id: str          # Unique ID of source document or fact
    source_type: str        # e.g., CLINICIAN_NOTE, PATHOLOGY_REPORT
    asserted_value: str     # Specific clinical assertion or measurement
    timestamp: Optional[str] # ISO date or string timestamp
    confidence: Optional[float]
    snippet: Optional[str]  # Verifiable textual excerpt
    start_char: int         # Offset start (-1 if unavailable)
    end_char: int           # Offset end (-1 if unavailable)
```

### 3.2 `UncertaintyRecord`
The primary atomic unit of uncertainty:
- `uncertainty_id`: Unique identifier (e.g., `UNC-001`).
- `subject`: Clinical concept or variable (e.g., `HER2_status`).
- `fact_or_criterion_ref`: Tied directly to a patient `fact_id` or protocol `criterion_id`.
- `status`: One of the 7 `UncertaintyStatus` values.
- `severity`: One of the 4 `UncertaintySeverity` values.
- `review_required`: Boolean flag enforced to `True` for `HIGH` and `CRITICAL`.
- `machine_decision_allowed`: Prohibited (`False`) whenever `HIGH` or `CRITICAL` uncertainty is unresolved.
- `conflict_details`: Required when `status == CONFLICTING` (must contain $\ge 2$ conflicting items).

---

## 4. Architectural Invariants

1. **No Fact Fabrication**: An uncertainty record only references facts, criteria, and spans that exist in the input profile or retrieved evidence pool.
2. **Missing $\neq$ Negative**: An uncertainty record with status `MISSING` preserves missingness; it is never converted into a negative clinical fact.
3. **Audit Immutability**: Once an uncertainty is logged, it cannot be deleted; resolution occurs by logging a corresponding resolution action that transitions status to `RESOLVED` while preserving the original record.
