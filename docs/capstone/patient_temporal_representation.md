# MedMatch Capstone — Patient Temporal Representation Specification

## 1. Executive Summary & Clinical Rationale

In clinical trial eligibility matching, **temporality is safety-critical**. Many eligibility criteria depend not just on whether an event occurred, but on **when** it occurred relative to trial initiation.

Key clinical scenarios requiring explicit temporal representations include:
1. **Washout Periods:** "No cytotoxic chemotherapy within 28 days prior to Day 1."
2. **Recent Organ Function / Lab Tests:** "Serum creatinine measured within 14 days of enrollment."
3. **Lines of Therapy Sequencing:** "Disease progression on or following first-line platinum-based chemotherapy."
4. **Historical vs. Active Comorbidities:** "Childhood asthma resolved 15 years ago" (eligible) vs. "Active refractory asthma requiring systemic steroids" (ineligible).
5. **Relative Temporal Statements in Notes:** "Completed stereotactic radiosurgery 3 weeks ago."

---

## 2. Temporal Semantics & Taxonomy

The MedMatch temporal framework defines eight discrete temporality types under `TemporalityType`:

| Temporality Type | Clinical Definition | Canonical Example |
| :--- | :--- | :--- |
| `CURRENT` | Active symptom, ongoing medication, or baseline status at presentation. | "Patient currently taking amlodipine 5mg daily." |
| `HISTORICAL` | Past medical condition, completed therapy course, or resolved event. | "Prior history of deep vein thrombosis in 2018, anticoagulation discontinued." |
| `DATE_SPECIFIC` | Event associated with an exact calendar date. | "Biopsy performed on 2026-03-15 confirmed adenocarcinoma." |
| `DURATION` | Condition or medication course persisting over a defined interval. | "Non-productive cough ongoing for 6 months." |
| `BEFORE_EVENT` | Event that occurred strictly prior to a defined clinical anchor. | "Carboplatin completed prior to intracranial progression." |
| `AFTER_EVENT` | Event that occurred subsequent to a defined clinical anchor. | "Developed pneumonitis after initiating pembrolizumab." |
| `RELATIVE_INTERVAL`| Relative elapsed time from an anchor (e.g., examination or screening). | "Chemotherapy completed 27 days ago." |
| `UNKNOWN` | Timing of condition or intervention cannot be reliably ascertained. | "Past surgical history includes cholecystectomy (date unknown)." |

---

## 3. Structural Temporal Model (`TemporalContext`)

```python
class TemporalContext(BaseModel):
    temporality_type: TemporalityType = Field(default=TemporalityType.UNKNOWN)
    reference_date: Optional[str] = Field(default=None)         # ISO-8601 YYYY-MM-DD
    relative_interval: Optional[str] = Field(default=None)      # e.g., "27 days ago"
    duration_days: Optional[int] = Field(default=None, ge=0)    # Duration length
    relative_days_offset: Optional[int] = Field(default=None)   # Signed integer offset (-27)
    anchor_event: Optional[str] = Field(default=None)           # "chemotherapy_completion"
    is_approximate: bool = Field(default=False)                 # True if approximate
```

---

## 4. Critical Conversion & Safety Rules

> [!WARNING]
> **SAFETY RULE: Preservation of Relative Statements**
> Do **NOT** silently convert relative dates (e.g., "27 days ago") into absolute calendar dates unless an explicit, unambiguous clinical note timestamp (reference anchor) is documented.
>
> If a note created on 2026-09-01 states "chemotherapy 3 weeks ago", the relative offset (`relative_days_offset=-21`) and anchor event (`chemotherapy`) must be preserved as primary evidence. Converting to absolute dates without anchor verification introduces false precision and can invalidate washout calculations.

### Rules for Clinical Trial Matchers
1. **Never Assume Historical Equals Inactive:** A condition labeled `HISTORICAL` must specify whether it is resolved or chronic (e.g., hypertension diagnosed 10 years ago remains active).
2. **Washout Comparison Logic:**
   - If a trial requires `washout_days >= 28` and patient completed therapy `27 days ago`, the patient is **INELIGIBLE** today, but will become eligible in **1 day**.
   - Preserving relative intervals allows the reasoning engine to distinguish permanent disqualification from imminent eligibility.
3. **Explicit Indication of Uncertainty:**
   - If a clinician writes "Patient had chemotherapy several months ago", `is_approximate` must be set to `True`, and `temporality_type` set to `RELATIVE_INTERVAL` with `relative_interval="several months ago"`.
