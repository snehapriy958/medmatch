# MedMatch Capstone — Eligibility Uncertainty & Missing Information Policy
**Document Version:** `1.0.0`  
**Phase:** 6 — Eligibility Reasoning  

---

## 1. Epistemic Foundations

In real-world electronic health records, clinical documentation is routinely incomplete, ambiguous, or contradictory. Classical information systems frequently force incomplete records into binary decisions (`Eligible` vs `Ineligible`), either hallucinating absence from silence or making unwarranted optimistic assumptions.

MedMatch adopts a strict **3-Valued Epistemic Framework**:
- **True (`PASS`):** The clinical evidence definitively demonstrates that the criterion is met.
- **False (`FAIL`):** The clinical evidence definitively demonstrates that the criterion is violated.
- **Unknown (`UNKNOWN`):** The available clinical evidence is missing, uncertain, contradictory, or unverifiable.

> **Fundamental Research Directive:**  
> `UNKNOWN` is an independent, first-class semantic state. It must **NEVER** be silently collapsed into `PASS` or `FAIL`.

---

## 2. Categories of Clinical Uncertainty

The eligibility reasoning engine explicitly distinguishes six categories of uncertainty:

### 2.1 Missing Information (Silence)
- **Definition:** The medical record does not document the concept or measurement referenced in the criterion.
- **Rule:** *Absence of evidence is not evidence of absence.* If a note fails to mention "prior chemotherapy", the system cannot conclude that the patient is chemotherapy-naive.
- **Status:** `UNKNOWN`
- **Documentation:** `uncertainty_notes = "Concept not mentioned in available clinical evidence."`

### 2.2 Uncertain Clinical Statements
- **Definition:** The physician's note contains hedging, suspect language, or unconfirmed differential diagnoses (e.g., "possible brain metastases", "rule out pulmonary embolism").
- **Rule:** Suspected or unconfirmed assertions cannot satisfy or fail criteria requiring confirmed diagnoses.
- **Status:** `UNKNOWN`
- **Documentation:** `uncertainty_notes = "Evidence documented as POSSIBLE/suspected; requires confirmatory diagnostics."`

### 2.3 Conflicting Clinical Evidence
- **Definition:** The patient record contains contradictory statements from different providers, dates, or sections (e.g., Note A states "Patient has diabetes mellitus type 2"; Note B states "No history of diabetes").
- **Rule:** The AI reasoner must **NOT** arbitrarily pick a side.
- **Status:** `UNKNOWN`
- **Trial Impact:** Triggers `NEEDS_REVIEW` at the trial level and generates an explicit clinical conflict alert.
- **Documentation:** `uncertainty_notes = "Conflicting evidence detected across clinical records. Requires physician reconciliation."`

### 2.4 Outdated Evidence (Historical vs. Active)
- **Definition:** A clinical observation is documented in the remote past, but the criterion demands active or current disease status (e.g., "active infection requiring IV antibiotics", while the patient had pneumonia 3 years ago).
- **Rule:** If the temporal recency cannot be established, evaluate as `UNKNOWN`. If explicitly resolved, evaluate as `FAIL` for active criteria.
- **Status:** `UNKNOWN` or `FAIL` (depending on whether resolution is confirmed).

### 2.5 Temporal Ambiguity
- **Definition:** A criterion imposes a strict temporal boundary (e.g., "within 28 days prior to Day 1"), but the patient's test date is missing, relative without an anchor, or approximate (e.g., "recently", "last month").
- **Rule:** When the mathematical constraint cannot be bounded within the allowable window, it must not be assumed valid.
- **Status:** `UNKNOWN`
- **Documentation:** `uncertainty_notes = "Temporal constraint cannot be verified due to missing or imprecise date anchors."`

### 2.6 Numerical & Unit Ambiguity
- **Definition:** A laboratory value is missing, reported as qualitative only (e.g., "platelets adequate"), or reported in incompatible units that cannot be safely converted.
- **Rule:** Numerical thresholds require exact, unit-aligned quantification.
- **Status:** `UNKNOWN`
- **Documentation:** `uncertainty_notes = "Measurement unquantified or unit mismatch requires clinical laboratory conversion."`

---

## 3. Propagation of Uncertainty to Trial Decisions

Uncertainty at the criterion level propagates deterministically to the trial level:

```
                  Criterion Evaluations
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
    Any FAIL?          No FAIL, but         All PASS?
                       Any UNKNOWN?
        │                   │                   │
        ▼                   ▼                   ▼
   INELIGIBLE         NEEDS_REVIEW           ELIGIBLE
```

By routing any trial with at least one `UNKNOWN` criterion to `NEEDS_REVIEW`, the system ensures that patients are neither mistakenly excluded (false negative due to missing data) nor prematurely enrolled (false positive risk), preserving patient safety and clinical trial integrity.
