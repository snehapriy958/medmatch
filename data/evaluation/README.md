# MedMatch Evaluation Artifacts & Run Directory

This directory stores outputs from benchmark evaluation runs, baseline model inferences, and metric artifacts produced by the MedMatch evaluation harness.

---

## Directory Structure

```text
data/evaluation/
├── README.md               # This specification
├── baselines/              # Reference predictions from baseline systems (E0, E1)
│   └── .gitkeep
└── runs/                   # Individual timestamped experiment runs (Git-ignored)
    └── .gitkeep
```

---

## Run Artifact Bundle Specification

When an experiment (E0 through E4) is executed by the evaluation harness, it produces an immutable run bundle under `data/evaluation/runs/{experiment_id}/`:

1. `config.yaml`: Frozen snapshot of the execution configuration (parameters, seeds, model IDs, prompt hash).
2. `predictions.jsonl`: Line-delimited JSON containing per-query retrieval results, criterion evaluations, evidence text spans, and trial eligibility decisions.
3. `metrics_summary.json`: Computed metrics (Recall@K, MRR, Macro-$F_1$, ECE, etc.) with 95% bootstrap confidence intervals.
4. `confusion_matrix.png`: Serialized $3 \times 3$ confusion matrix image.
5. `error_log.jsonl`: Detailed categorization of all prediction errors mapped to the 12-factor error taxonomy.

---

## Versioning & Git Policy

- Individual evaluation execution logs (`runs/`) are excluded from Git via `.gitignore` to prevent repository bloat.
- Key baseline reference predictions (`baselines/`) and aggregated summary tables may be committed alongside final milestone reports.
