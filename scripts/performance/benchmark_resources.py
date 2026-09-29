"""
Phase 14.1 — Benchmark 7: Process Memory & Resource Profiling.

Measures memory (RSS) and resource characteristics in the local benchmark environment.

Explicit Scope Distinctions & Methodology Qualifications:
- Local Process RSS = MEASURED
- Kubernetes CFS Throttling = NOT MEASURED
- OOM Risk Overclaim Removed: Observed local peak RSS does NOT establish Kubernetes
  production OOM risk. Container cgroup memory limits (1.0–2.0 GiB) interact with
  operating system page caches, Python memory allocator fragmentation, and multi-worker
  concurrency in ways that cannot be determined from single-process local execution.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
AI_SERVICE_DIR = REPO_ROOT / "services" / "ai-service"
for p in [str(REPO_ROOT), str(AI_SERVICE_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from scripts.performance.harness import get_process_memory_mb


def run_resource_benchmark() -> dict[str, Any]:
    """
    Profile process memory (RSS) baseline and peak during model operations.
    """
    base_rss, base_peak = get_process_memory_mb()

    # Load SentenceTransformer and run inference to reach peak memory
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")
    post_load_rss, post_load_peak = get_process_memory_mb()

    # Execute batch encode
    dummy_texts = [f"Sample clinical research note number {i}" for i in range(64)]
    _ = model.encode(dummy_texts, batch_size=32)
    final_rss, final_peak = get_process_memory_mb()

    return {
        "benchmark_id": "BENCH-07-RESOURCES",
        "benchmark_title": "Process Memory & Resource Profiling",
        "evidence_classification": "PARTIALLY CONFIRMED",
        "scope": "Local process working set memory (RSS) on Windows 11 host",
        "local_memory_measurements": {
            "status": "MEASURED",
            "baseline_rss_mb": base_rss,
            "post_model_load_rss_mb": post_load_rss,
            "peak_rss_mb": final_peak,
            "model_memory_footprint_mb": round(final_peak - base_rss, 2),
            "environment_qualification": (
                f"Observed local peak RSS was {final_peak:.2f} MB in the local Windows benchmark environment; "
                "this does not establish Kubernetes production OOM risk. Production containers run under "
                "cgroups with hard memory limits (1.0–2.0 GiB) where page cache usage, allocator fragmentation, "
                "and concurrent request concurrency may lead to OOMKills under heavy load."
            ),
        },
        "kubernetes_cfs_throttling": {
            "status": "NOT MEASURED",
            "reason": (
                "Kubernetes Completely Fair Scheduler (CFS) quota throttling was NOT MEASURED. "
                "CFS throttling requires Linux cgroup v1/v2 cpu.cfs_quota_us enforcement, which is "
                "not present on a native Windows host execution environment."
            ),
        },
        "production_resource_limits": {
            "ai_service_cpu_limit": "1000m",
            "ai_service_memory_limit": "2Gi",
            "worker_cpu_limit": "1000m",
            "worker_memory_limit": "1.5Gi",
        },
    }


if __name__ == "__main__":
    print("Running Benchmark 7: Process Memory & Resource Profiling...")
    res = run_resource_benchmark()
    print(f"Peak RSS: {res['local_memory_measurements']['peak_rss_mb']} MB")
    print(f"CFS Status: {res['kubernetes_cfs_throttling']['status']}")
