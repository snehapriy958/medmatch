# Phase 9: Reproducibility & Provenance Specification

## 1. Specification Overview

Phase 9 establishes formal uncertainty representation and human-review adjudication protocols. To ensure complete reproducibility across environments, operating systems, and executions, all Phase 9 components operate under strict deterministic rules without random state, hidden probabilistic models, or unseeded external dependencies.

---

## 2. Invariants & Environment Manifest

### 2.1 Software & Evaluator Identifiers
- **Phase 9 Evaluator Version**: `1.0.0-phase9-research`
- **Schema Version**: `1.0.0`
- **Fixture Version**: `phase9-dev-v1.0`
- **Random Seed Policy**: `Deterministic` (Zero stochasticity; no pseudo-random generators utilized).
- **Execution Runtime**: Python 3.13 / Virtual Environment (`services/ai-service/.venv`).

### 2.2 Deterministic Ordering Guarantees
- **Uncertainty IDs**: Sequentially formatted as `UNC-{case_id}-{index:02d}`.
- **Audit Event IDs**: Sequentially formatted as `EVT-{review_id}-{event_index:04d}`.
- **Priority Sorting**: Sorted by discrete priority enum hierarchy (`ESCALATED` > `PRIORITY` > `ROUTINE`), then by criteria index.
- **Timestamp Standard**: ISO 8601 UTC string format (`YYYY-MM-DDTHH:MM:SS.ffffff+00:00`).

---

## 3. Grounding & Uncertainty Provenance Binding

1. **Patient Fact Provenance**: Bound to canonical `PatientClinicalProfile` fact identifiers (`fact_id`) and character offsets `[start_char, end_char]` where available. If character offsets cannot be located, `-1` is assigned per project convention without synthetic interpolation.
2. **Protocol Evidence Provenance**: Bound to trial accession (`trial_id`), criterion accession (`criterion_id`), and Phase 5 chunk metadata (`document_id`, `section_id`, `chunk_id`, `retrieval_method`, `rank`, `similarity_score`).
3. **Machine Output Immutability**: All original machine reasoning, confidence values, and criterion-level assessments are stored immutably in `original_machine_output` upon review creation. Review actions append to `audit_metadata` and the chronological `ReviewAuditTrail`.

---

## 4. Test & Verification Commands

All test suites can be reproduced via the following commands:

```bash
# 1. Phase 9 Human Review Suite
services/ai-service/.venv/Scripts/python.exe -m pytest -q tests/human_review

# 2. Complete Research Regression Suites (Phases 2-8)
services/ai-service/.venv/Scripts/python.exe -m pytest -q tests/grounding_evaluation tests/rag_evaluation tests/document_intelligence tests/patient_information tests/eligibility tests/retrieval

# 3. Production Service Isolation Tests
services/ai-service/.venv/Scripts/python.exe -m pytest -q services/ai-service/tests -o pythonpath=services/ai-service
```
