# MedMatch Capstone — Reproducibility Specification

> **Status:** Specification Document  
> **Phase:** 1 — Research Problem & Evaluation Design  
> **Author:** MedMatch Research Team  
> **Date:** September 2026  
> **Target System:** MedMatch Clinical Decision-Support Prototype

---

## 1. Reproducibility Mandate

Scientific validation requires that every experiment, metric, baseline comparison, and ablation reported in the MedMatch capstone project be **100% deterministic, audit-traceable, and independently reproducible**.

No metric may be reported in future phases without a corresponding frozen experiment configuration file, an immutable dataset split checksum, and recorded model execution parameters.

---

## 2. Experiment Configuration Schema

Every benchmark run must be defined by an immutable YAML/JSON configuration file conforming to the schema below:

```yaml
# Example: configs/experiments/E1_baseline_minilm.yaml
experiment_metadata:
  experiment_id: "EXP_E1_20260928_V1"
  description: "Phase 0 Baseline benchmark: MiniLM-L6-v2 dense retrieval + Gemini 2.5 Flash"
  git_commit_hash: "a4f8c2b918d3e4f7105..."
  author: "MedMatch Research Team"
  created_at_utc: "2026-09-28T14:30:00Z"
  tags: ["baseline", "phase0_audit", "dense_only"]

dataset_specification:
  dataset_name: "medmatch-oncology-benchmark"
  dataset_version: "v1.0.0-capstone"
  split_file: "data/splits/test.json"
  split_sha256: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
  global_random_seed: 42

retrieval_configuration:
  pipeline: "dense_vector_pgvector"
  embedding_model:
    name: "sentence-transformers/all-MiniLM-L6-v2"
    source: "local_disk"
    path: "services/ai-service/models/all-MiniLM-L6-v2"
    dimension: 384
    pooling_strategy: "mean"
    normalize_embeddings: true
  search_parameters:
    top_k: 5
    distance_metric: "cosine"
    similarity_threshold: 0.75
    indexed: false # sequential scan in baseline; HNSW in E4

reasoning_configuration:
  engine: "gemini"
  model_identifier: "gemini-2.5-flash"
  api_version: "v1beta"
  hyperparameters:
    temperature: 0.0
    top_p: 0.95
    max_output_tokens: 4096
    seed: 42
  prompt_specification:
    prompt_id: "trial_matching_prompt"
    prompt_path: "services/ai-service/app/prompts/trial_matching_prompt.py"
    prompt_sha256: "8f7e2d..."
    input_format: "raw_clinical_note"

aggregation_configuration:
  aggregation_mode: "monolithic_in_prompt" # In E1; 'deterministic_python' in E3/E4
  unknown_handling: "surface_needs_review"

output_artifacts:
  results_directory: "data/evaluation/runs/EXP_E1_20260928_V1/"
  save_raw_completions: true
  save_per_query_metrics: true
```

---

## 3. Mandatory Experiment Recording Checklist

For every execution of an experiment in the matrix (E0 through E4):

```text
+-----------------------------------------------------------------------------------+
|                         PROVENANCE TRACKING CHECKLIST                             |
+-----------------------------------------------------------------------------------+
| Parameter                    | Tracking Requirement                               |
+------------------------------+----------------------------------------------------+
| 1. Dataset Version           | Semantic version tag (e.g. v1.0.0-capstone)        |
| 2. Split Hash                | SHA-256 hash of the exact split JSON file used     |
| 3. Random Seed               | Explicit integer (e.g. 42) for Python, PyTorch,   |
|                              | NumPy, and provider API seeds                     |
| 4. Embedding Model State     | Exact model repo ID, revision SHA, or local disk   |
|                              | directory checksum                                 |
| 5. LLM Model Identifier      | Exact provider string, e.g. "gemini-2.5-flash"     |
| 6. LLM Temperature           | 0.0 (Deterministic greedy decoding)               |
| 7. Prompt Content Hash       | SHA-256 of the prompt template string              |
| 8. Retrieval Top-K           | Explicit integer (e.g. 5)                          |
| 9. Distance Threshold        | Explicit float (e.g. 0.75)                         |
| 10. System Version           | Git commit SHA of the MedMatch codebase            |
| 11. Timestamp                | ISO-8601 UTC timestamp of execution                |
| 12. Hardware Manifest        | OS version, CPU, GPU, CUDA driver, RAM             |
| 13. Software Manifest        | Python virtualenv `pip freeze` lockfile            |
+-----------------------------------------------------------------------------------+
```

---

## 4. Software Environment Specification

To eliminate dependency drift, the evaluation harness will run under a strictly pinned environment:

### 4.1 Host and Runtime Environment
- **Operating System:** Windows 11 Enterprise / Ubuntu 22.04 LTS (Docker containerized)
- **Python Version:** 3.13.x (or pinned 3.11.8 for CUDA stability)
- **Database:** PostgreSQL 16.2 with `pgvector` 0.7.0+
- **Backend Service:** FastAPI 0.115.0+ / Uvicorn 0.32.0+
- **Auth Service:** Spring Boot 3.3.4 / OpenJDK 21

### 4.2 Core AI/ML Libraries
- `sentence-transformers == 3.3.1`
- `torch == 2.5.1`
- `google-genai == 1.0.0`
- `numpy == 1.26.4`
- `pydantic == 2.10.4`
- `scikit-learn == 1.5.2`
- `rank-bm25 == 0.2.2`

---

## 5. Artifact Provenance and Storage Policy

When an evaluation script runs, it must output a structured run bundle into `data/evaluation/runs/{experiment_id}/`:

1. `config.yaml`: Frozen snapshot of the execution configuration.
2. `predictions.jsonl`: Line-delimited JSON containing for every test query:
   - `patient_id`
   - `retrieved_trial_ids` with scores and ranks
   - `criterion_evaluations` with cited text spans
   - `predicted_eligibility`
   - `ground_truth_eligibility`
   - `inference_latency_ms`
3. `metrics_summary.json`: Computed metric values (Recall@K, MRR, Macro-$F_1$, ECE, etc.) with 95% bootstrap confidence intervals.
4. `confusion_matrix.png`: Serialized $3 \times 3$ confusion matrix graphic.
5. `error_log.jsonl`: Instances categorized by the 12-factor error taxonomy.
