# Phase 10: Reproducibility Specification

## 1. Environment & Dependencies

- **Platform**: Windows 11 / x86_64
- **Python**: 3.13.14 (in `services/ai-service/.venv`)
- **Pytest**: 9.1.1
- **Pydantic**: 2.13.x
- **Isolation Constraint**: Research code operates strictly under `scripts/`, `data/fixtures/phase10/`, `tests/explainability/`, and `docs/capstone/`. Zero imports or modifications to `services/`.

---

## 2. Test Execution Commands

### Phase 10 Explainability Suite
```powershell
services\ai-service\.venv\Scripts\python.exe -m pytest -v tests/explainability
```

### Complete Research Regressions (Phases 2–10)
```powershell
services\ai-service\.venv\Scripts\python.exe -m pytest -q tests/explainability tests/human_review tests/grounding_evaluation tests/rag_evaluation tests/eligibility tests/retrieval tests/patient_information tests/document_intelligence tests/dataset
```

### Production AI-Service Suite
```powershell
services\ai-service\.venv\Scripts\python.exe -m pytest -q services/ai-service/tests -o pythonpath=services/ai-service
```

### Phase 10 Experiment Harness CLI
```powershell
services\ai-service\.venv\Scripts\python.exe scripts/explainability_experiment.py
```

---

## 3. Data & Fixture Manifest

- Fixtures file: `data/fixtures/phase10/explainability_fixtures.json` (18 scenarios)
- SHA-256 Checksum: Computed deterministically upon generation
- Benchmark Guardrail: `has_validated_benchmark() == False` is programmatically enforced in `scripts/explainability_experiment.py`.
