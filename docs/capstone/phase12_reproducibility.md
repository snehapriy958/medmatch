# Phase 12 Reproducibility Specification & Execution Manifest

**Document ID:** SAFETY-REPRO-P12  
**Phase:** Phase 12 — Clinical Safety  
**Scope:** Execution Instructions, Fixture Hashes, Seeds, Artifact Locations, and Environment Specifications  
**Status:** DRAFT — RESEARCH SPECIFICATION ONLY  

---

## 1. Executive Summary & Epistemic Scope

This document specifies the exact environment, deterministic random seeds, software dependencies, execution commands, and artifact schemas required to reproduce all Phase 12 Clinical Safety experiments, safety gates, and error-injection suites.

> [!NOTE]
> **DEVELOPMENT/TEST FIXTURE ONLY:**  
> All executions run against the synthetic 24-scenario safety fixture. No live external network calls or human patient data are utilized.

---

## 2. Environment & Dependency Specifications

- **Python Version:** 3.13.x (via virtual environment `services/ai-service/.venv`)
- **Operating System:** Windows 11 Enterprise (x64)
- **Primary Libraries:**
  - `pydantic >= 2.10.0`
  - `pytest >= 8.3.0`
  - `numpy >= 1.26.0`
- **Random Seed:** Locked at `42` across all deterministic processes.
- **Network Access:** Prohibited during execution (100% offline hermetic execution).

---

## 3. Directory Layout & Artifact Map

```text
MEDMATCH_V2/
├── data/
│   └── fixtures/
│       └── phase12/
│           └── safety_scenarios.json       # 24 synthetic clinical safety test scenarios
├── scripts/
│   ├── safety_schema.py                   # Canonical safety data models & taxonomy enums
│   ├── safety_policy.py                   # 18 conservative reasoning policy rules
│   ├── safety_gates.py                    # Deterministic Safety Gates (GATE-01 to GATE-12)
│   ├── safety_validator.py                # Machine-checkable invariant validator (INV-01 to INV-15)
│   ├── safety_metrics.py                  # 14 safety metric calculators (M-S01 to M-S14)
│   ├── error_injector.py                  # Fault injection harness (INJ-01 to INJ-14)
│   ├── safety_experiment.py               # Experiment runner (S-E0 to S-E4, A-S1 to A-S7)
│   └── run_phase12_pipeline.py            # Master Phase 12 pipeline execution script
├── tests/
│   └── clinical_safety/
│       ├── test_safety_gates.py           # Unit tests for GATE-01 through GATE-12
│       ├── test_safety_invariants.py      # Unit tests for INV-01 through INV-15
│       ├── test_safety_taxonomy.py        # Tests for S1–S24 error classifications
│       ├── test_error_injection.py        # Tests for fault injection and detection/mitigation
│       ├── test_safety_metrics.py         # Tests for M-S01 through M-S14 formulas
│       ├── test_safety_pipeline.py        # End-to-end pipeline integration test
│       └── test_phase12_isolation.py      # Zero-production-import verification test
└── results/
    └── phase12/
        ├── safety_manifest.json           # Execution manifest & timestamp
        ├── s_e0_baseline.json             # S-E0 baseline experiment results
        ├── s_e1_gates.json                # S-E1 deterministic gates experiment results
        ├── s_e2_uncertainty.json          # S-E2 uncertainty routing experiment results
        ├── s_e3_grounding.json            # S-E3 grounding & provenance experiment results
        ├── s_e4_full_safety.json          # S-E4 full safety pipeline experiment results
        ├── safety_ablations.json          # A-S1 through A-S7 ablation results
        ├── error_injection_results.json   # Fault injection outcomes across INJ-01 to INJ-14
        └── phase12_summary.json           # Comprehensive Phase 12 summary metrics
```

---

## 4. Execution Commands

### 1. Execute Master Safety Pipeline:
```bash
services\ai-service\.venv\Scripts\python.exe scripts/run_phase12_pipeline.py
```

### 2. Run Phase 12 Clinical Safety Test Suite:
```bash
services\ai-service\.venv\Scripts\python.exe -m pytest -q tests/clinical_safety
```

### 3. Run Complete Full Research Regression (Phases 2–12):
```bash
services\ai-service\.venv\Scripts\python.exe -m pytest -q \
tests/dataset \
tests/document_intelligence \
tests/patient_information \
tests/retrieval \
tests/eligibility \
tests/rag_evaluation \
tests/grounding_evaluation \
tests/human_review \
tests/explainability \
tests/evaluation \
tests/clinical_safety
```

### 4. Run Production AI-Service Suite:
```bash
services\ai-service\.venv\Scripts\python.exe -m pytest -q services/ai-service/tests -o pythonpath=services/ai-service
```
