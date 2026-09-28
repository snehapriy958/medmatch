# MedMatch Capstone — Phase 6: Eligibility Reasoning Audit

## Executive Summary

This document establishes the baseline audit for clinical trial eligibility reasoning in the MedMatch platform. It contrasts the **current production behavior** with the **research requirements** of Phase 6, identifies key research deficiencies, delineates safe extension points, and specifies components that must remain strictly protected.

---

## 1. Current Production Behavior

### 1.1 Input & Workflow Flow
The production eligibility evaluation is orchestrated by `MatchingService.evaluate_eligibility` (`services/ai-service/app/services/matching_service.py`):
1. **Input:** Free-text `patient_note: str`, `hospital_id: UUID`, `current_user: dict`, and `limit: int` (default 10).
2. **Tenant Verification:** `_validate_user_hospital` ensures the authenticated user's `hospital_id` in their JWT strictly matches the requested `hospital_id`.
3. **Retrieval Handoff:**
   - Calls `_retrieve_matching_criteria`, which embeds the patient note using `sentence-transformers/all-MiniLM-L6-v2` (384-d).
   - Executes exact cosine distance search against PostgreSQL `trial_embeddings` (`<=>`) filtered by `hospital_id`.
   - Extracts unique trial IDs (`expected_trial_ids`).
   - Fetches **all** inclusion and exclusion criteria for those candidate trials via `TrialCriteriaRepository.list_by_trial(trial_id)`.
4. **Prompt Construction:**
   - `PromptBuilder.build_matching_prompt` groups criteria by trial ID and injects the raw `patient_note` and trial metadata into the monolithic `TRIAL_MATCHING_PROMPT`.
5. **LLM Invocation:**
   - Invokes Google Gemini via `LLMService.evaluate_eligibility(prompt)` requesting a structured JSON list of `EligibilityResponse` objects.
6. **Validation & Guardrails:**
   - `_validate_llm_trial_results` validates that Gemini returned exactly one evaluation object per retrieved trial ID (rejecting hallucinated, duplicated, or omitted trials).
   - On validation error, it returns a safe abstention (`POSSIBLY_ELIGIBLE`, confidence 0.0).
7. **Caching & Audit Logging:**
   - Results are cached in Redis (`CacheKeys.llm`) keyed by `f"{hospital_id}:{prompt}"`.
   - `_log_matching_audit` records an audit event without storing patient clinical text.

### 1.2 Output Schema (`EligibilityResponse`)
Defined in `services/ai-service/app/schemas/eligibility.py`:
- `eligibility`: `EligibilityStatus` enum (`Eligible`, `Not Eligible`, `Possibly Eligible`).
- `confidence`: `float` ($0.0 \le c \le 1.0$).
- `trial_ids_evaluated`: `list[str]`.
- `summary`: `str`.
- `matched_inclusion`: `list[str]` (free-text descriptions).
- `failed_inclusion`: `list[str]` (free-text descriptions).
- `satisfied_exclusion`: `list[str]` (free-text descriptions).
- `triggered_exclusion`: `list[str]` (free-text descriptions).
- `missing_information`: `list[str]`.
- `recommendation`: `str`.
- `reasoning`: `str`.

### 1.3 Tenant Isolation & Security
- Tenant boundary is enforced at database retrieval (`WHERE hospital_id = :hospital_id`), cache key namespacing (`f"{hospital_id}:..."`), and audit logging.
- Cross-tenant data leakage is prevented by SQL filters and JWT claim validation.

---

## 2. Research Deficiencies & Architectural Gaps

| Dimension | Current Production Behavior | Research Requirement (Phase 6) | Research Gap |
| :--- | :--- | :--- | :--- |
| **Criterion Granularity** | Unstructured lists of text strings (`matched_inclusion`, etc.). | Explicit, strongly typed criterion evaluation records with unique IDs and metadata. | Cannot trace evaluation to specific database criterion records or calculate per-criterion precision/recall. |
| **Truth Semantics** | Informal bucketing into satisfied/failed inclusion/exclusion lists. | Rigorous 3-valued truth model: `PASS`, `FAIL`, `UNKNOWN`. | Missing information is frequently conflated with negative evidence or arbitrary subjective decisions. |
| **Trial Aggregation** | The LLM directly determines whether a trial is `Eligible`, `Not Eligible`, or `Possibly Eligible`. | Deterministic programmatic aggregation logic: Any `FAIL` $\to$ `INELIGIBLE`; else any `UNKNOWN` $\to$ `NEEDS_REVIEW`; else all `PASS` $\to$ `ELIGIBLE`. | Black-box LLM decision making; risk of inconsistent aggregation logic across trials. |
| **Evidence Grounding** | Natural language reasoning string without character offsets or patient fact IDs. | Explicit pointers to patient clinical facts, source text character offsets, and trial criteria. | Lack of formal auditability; vulnerability to hallucinated evidence. |
| **Negation & Silence** | Relies on LLM internal linguistic attention. | Explicit handling of clinical assertion states (`PRESENT`, `ABSENT`, `POSSIBLE`). Silence is strictly `UNKNOWN`. | Risk of inferring absence from clinical silence or misinterpreting negated criteria. |
| **Temporal Reasoning** | Implicit LLM interpretation of relative dates and time intervals. | Explicit temporal representation comparing patient observation intervals with criterion time windows. | Risk of date fabrication or misinterpreting duration constraints (e.g. "within 30 days"). |
| **Numerical Reasoning** | Implicit LLM numerical comparisons. | Formal mathematical threshold checking for lab values, vitals, and scores with unit alignment. | Risk of numerical threshold errors and unit mismatches (e.g. creatinine, platelets). |
| **Conflict Handling** | LLM reconciles or ignores contradictory clinical notes silently. | Explicit representation of conflicting evidence, forcing an `UNKNOWN` or `NEEDS_REVIEW` state. | Silent resolution of clinical contradictions without human clinician alerting. |

---

## 3. Safe Extension Points

To preserve the production service while advancing capstone research, Phase 6 introduces a fully decoupled research reasoning pipeline:

```
[Phase 4 Patient Profile]   +   [Phase 5 Retrieved Criteria]
            │                                 │
            └───────────────┬─────────────────┘
                            ▼
              ┌───────────────────────────┐
              │ Canonical Research Model  │
              │ (scripts/eligibility_     │
              │  schema.py)               │
              └─────────────┬─────────────┘
                            ▼
              ┌───────────────────────────┐
              │ Evidence-Grounded         │
              │ Reasoner                  │
              │ (scripts/eligibility_     │
              │  reasoner.py)             │
              │ - Negation handling       │
              │ - Temporal constraint     │
              │ - Numerical check         │
              │ - Conflict detection      │
              └─────────────┬─────────────┘
                            ▼
              ┌───────────────────────────┐
              │ Deterministic Aggregator  │
              │ (scripts/eligibility_     │
              │  aggregator.py)           │
              │ - FAIL -> INELIGIBLE      │
              │ - UNKNOWN -> NEEDS_REVIEW │
              │ - PASS -> ELIGIBLE        │
              └─────────────┬─────────────┘
                            ▼
              ┌───────────────────────────┐
              │ Deterministic Validator   │
              │ (scripts/validate_        │
              │  eligibility.py)          │
              └───────────────────────────┘
```

1. **`scripts/eligibility_schema.py`**: Canonical Pydantic schemas for atomic criterion evaluations (`CriterionEvaluationRecord`), trial-level aggregated evaluations (`TrialEligibilityEvaluation`), and batch requests/responses.
2. **`scripts/eligibility_reasoner.py`**: Modular reasoning engine implementing rule-based and symbolic evidence matching for negation, numerical bounds, temporal intervals, compound logic, and conflicting evidence.
3. **`scripts/eligibility_aggregator.py`**: Pure, deterministic, side-effect-free trial-level aggregation engine.
4. **`scripts/validate_eligibility.py`**: Rigorous validation harness verifying schema compliance, evidence citation requirements, and aggregation invariants.

---

## 4. Components That Must Remain Unchanged

The following components are strictly protected and MUST NOT be modified:
1. `services/ai-service/app/services/matching_service.py`
2. `services/ai-service/app/services/llm_service.py`
3. `services/ai-service/app/services/embedding_service.py`
4. `services/ai-service/app/rag/prompt_builder.py`
5. `services/ai-service/app/prompts/trial_matching_prompt.py`
6. `services/ai-service/app/schemas/eligibility.py`
7. `scripts/patient_extractor.py` (remains isolated, NOT connected to production matcher)
8. `scripts/retrieval_engine.py` (Phase 5 retrieval remains locked)

---

## 5. Summary & Transition to Step 2

With the audit complete and the architectural boundaries verified, Step 2 defines the canonical eligibility research schema.
