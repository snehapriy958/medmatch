# Phase 11 Reproducibility Specification: Environment, Seeds, & Execution Manifest

**Document ID:** REPRO-SPEC-P11  
**Phase:** Phase 11 — Evaluation & Ablation  
**Scope:** Deterministic Reproduction Protocol, Environment Manifest, Checksums, and Verification Commands

---

## 1. Reproducibility Manifest

Every execution of the Phase 11 pipeline produces a frozen, machine-readable manifest at [`results/phase11/experiment_manifest.json`](file:///C:/Developers/Sneha/Projects/MEDMATCH_V2/results/phase11/experiment_manifest.json).

```json
{
  "phase": "Phase 11: Evaluation & Ablation",
  "git_commit_sha": "59e3f2f",
  "random_seed": 42,
  "environment_info": {
    "python_version": "3.13.14",
    "os": "Windows-11-10.0.26100-SP0",
    "platform": "AMD64"
  },
  "empirical_benchmark_available": false,
  "generalizable_claims_asserted": false
}
```

---

## 2. Frozen Environment Manifest

| Component | Verified Specification |
|:---|:---|
| **Operating System** | Windows 11 Pro (Build 10.0.26100) |
| **Python Runtime** | `3.13.14` (64-bit AMD64) |
| **Virtual Environment** | `services/ai-service/.venv` |
| **Core Libraries** | `pydantic >= 2.10`, `pytest >= 9.0`, `torch >= 2.6.0`, `fastapi >= 0.115` |
| **Random Seed** | `42` (Fixed across all tie-breaking, tokenization, and ordering logic) |
| **Base Git Checkpoint** | `59e3f2f feat: establish explainability and evidence graph foundation` |

---

## 3. Dataset Integrity & Cryptographic Hashes

All input dataset files used in Phase 11 must match the SHA-256 hashes recorded in [`data/manifests/checksums.sha256`](file:///C:/Developers/Sneha/Projects/MEDMATCH_V2/data/manifests/checksums.sha256):

| File Path | SHA-256 Checksum | Purpose |
|:---|:---|:---|
| `data/fixtures/trials.json` | `c6cbff197175510dd9fe3e786b896677943801f9bb9ca2eb2cbbca91a3cf8e3e` | Protocol definitions |
| `data/fixtures/patients.json` | `beea3e551c6b1285265691c8bafe6ba7f73c6a46132474dbcae22b109e4d0d0c` | Synthetic patient narratives & facts |
| `data/fixtures/criteria.json` | `835150824968840b3c6aa60f898fe780775d506d863e46ca7bbd56637ef696f8` | Decomposed trial criteria |
| `data/fixtures/criterion_labels.json` | `6b2d2dbd3f5723b3648a97960fa00db6271a25db9c2c77d612e6bf5f71e5c3e7` | Gold criterion labels |
| `data/fixtures/trial_labels.json` | `5e9ce6d42df7ae752a16d54238e8869ff9f6eb32ca4a38545853ee2fa4f40f0c` | Gold trial eligibility decisions |

---

## 4. Exact Execution Commands

To reproduce the Phase 11 evaluation pipeline and tests from scratch:

### 1. Run the Full Phase 11 Evaluation Pipeline
```powershell
services\ai-service\.venv\Scripts\python.exe scripts/run_phase11_pipeline.py --data-dir data --output-dir results/phase11
```
*Expected Output:*
- Emits all 11 JSON result bundles into `results/phase11/`.
- Exit code: `0`.

### 2. Run the Phase 11 Evaluation Test Suite
```powershell
services\ai-service\.venv\Scripts\python.exe -m pytest -v tests/evaluation
```
*Expected Output:*
- `24 passed` in ~1.6s.

### 3. Run the Complete Research Regression Suite (Phases 2–11)
```powershell
services\ai-service\.venv\Scripts\python.exe -m pytest -q tests/dataset tests/document_intelligence tests/patient_information tests/retrieval tests/eligibility tests/rag_evaluation tests/grounding_evaluation tests/human_review tests/explainability tests/evaluation
```
*Expected Output:*
- `286 passed` in ~3.8s.

### 4. Run the Production AI-Service Test Suite
```powershell
$env:DATABASE_URL="postgresql://postgres:postgres@localhost:5432/medmatch_test"; services\ai-service\.venv\Scripts\python.exe -m pytest -q services/ai-service/tests -o pythonpath=services/ai-service
```
*Expected Output:*
- `45 passed, 1 warning` in ~37s.

### 5. Verify Production Isolation
```powershell
git diff --stat services/ ; git status --porcelain -- services/
```
*Expected Output:*
- Completely empty (0 files modified, 0 untracked files).
