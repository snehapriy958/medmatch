# MedMatch Capstone — Phase 7: Reproducibility & Provenance Specification

**Document Version:** `1.0.0`  
**Phase:** 7 — RAG vs. Non-RAG Experimental Evaluation  
**Date:** September 2026  
**Status:** Reproducibility Standard  

---

## 1. Reproducibility Mandate

To satisfy the standards of scientific peer review and capstone rigor, every experimental execution in Phase 7 must produce an immutable, self-contained **Reproducibility Record**. Any claim of empirical difference between RAG and Non-RAG must be 100% reproducible from frozen code, deterministic seeds, and versioned datasets.

---

## 2. Immutable Run Record Schema

Whenever `scripts/run_phase7_experiment.py` executes an experimental comparison, it writes an audit manifest to `data/evaluation/runs/{experiment_run_id}/manifest.json` containing:

```json
{
  "manifest_version": "1.0.0",
  "experiment_run_id": "run-phase7-20260928-001",
  "experiment_id": "E5_VS_E6_CONTROLLED",
  "dataset": {
    "dataset_id": "medmatch-evaluation-corpus",
    "dataset_version": "0.1.0-fixture",
    "dataset_manifest_checksum": "sha256:7f83b1a2..."
  },
  "environment": {
    "git_commit_sha": "120bd7e",
    "git_branch": "capstone/phase-6-eligibility-reasoning",
    "python_version": "3.13.14",
    "operating_system": "Windows 11 (win32)",
    "pytorch_version": "2.2.0",
    "transformers_version": "4.40.0"
  },
  "controlled_parameters": {
    "random_seed": 42,
    "temperature": 0.0,
    "max_tokens": 2048,
    "model_identifier": "rule_reasoner_v1",
    "prompt_version": "v1.0.0-canonical"
  },
  "retrieval_configuration": {
    "nonrag_retriever": "NONE",
    "rag_retriever": "hybrid_rrf",
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "embedding_dim": 384,
    "top_k": 5,
    "rrf_k": 60
  },
  "execution": {
    "start_time_utc": "2026-09-28T21:30:00Z",
    "end_time_utc": "2026-09-28T21:30:05Z",
    "duration_seconds": 5.12,
    "total_cases_evaluated": 6,
    "information_leakage_detected": false
  },
  "artifact_paths": {
    "predictions_jsonl": "data/evaluation/runs/run-phase7-20260928-001/predictions.jsonl",
    "comparisons_jsonl": "data/evaluation/runs/run-phase7-20260928-001/comparisons.jsonl",
    "metrics_json": "data/evaluation/runs/run-phase7-20260928-001/metrics.json"
  }
}
```

---

## 3. Seed Control & Deterministic Execution

1. **Random Seed Pinning:** Global seeds (`random.seed(42)`, `numpy.random.seed(42)`, `torch.manual_seed(42)`) are explicitly set prior to candidate shuffling or sampling.
2. **Deterministic Sort Tie-Breaking:** In retrievers, rank ties are always broken by lexicographical order of unique identifiers (`(-score, trial_id, criterion_id)`).
3. **Model Decoding:** LLM generation is configured with `temperature = 0.0`, eliminating stochastic variation across inference passes.

---

## 4. Verification of Information Isolation

Before metrics are calculated, the evaluation runner executes an automated **Information Leakage Check**:
- Confirms that the input context passed to the E5 adapter contains **zero** substring matches from retrieved trial brief summaries or retrieval score fields.
- If leakage is detected, the run is aborted and flagged as invalid.
