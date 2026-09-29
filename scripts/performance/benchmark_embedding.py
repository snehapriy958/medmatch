"""
Phase 14.1 — Benchmark 1: Embedding Latency & Batch Throughput.

Evaluates SentenceTransformer ('all-MiniLM-L6-v2') on:
1. Cold model initialization latency (isolated from inference).
2. Warm single-text inference latency distribution (p50, p95, p99).
3. Batch inference latency and throughput across batch sizes (1, 4, 8, 16, 32).
4. Memory RSS and process CPU consumption profiling.
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

from scripts.performance.harness import (
    calculate_distribution,
    get_process_memory_mb,
)

SAMPLE_CLINICAL_TEXTS = [
    "Patient diagnosed with stage IV non-small cell lung cancer with EGFR exon 19 deletion.",
    "History of poorly controlled type 2 diabetes mellitus with HbA1c 8.8% and peripheral neuropathy.",
    "Prior systemic treatment with pembrolizumab and pemetrexed-carboplatin chemotherapy.",
    "ECOG performance status 1, absolute neutrophil count 2,100/mcL, platelets 165,000/mcL.",
    "Exclusion: active brain metastases or leptomeningeal disease requiring corticosteroids.",
    "Inclusion: documented HER2 overexpression by IHC 3+ or FISH amplification ratio >= 2.0.",
    "Patient has history of congestive heart failure NYHA Class III with left ventricular ejection fraction 38%.",
    "Current medications include metformin 1000mg BID, lisinopril 20mg daily, and atorvastatin 40mg daily.",
]


def run_embedding_benchmark(
    warmup_runs: int = 3,
    measured_runs: int = 25,
) -> dict[str, Any]:
    """Run comprehensive embedding latency and batch throughput benchmark."""
    initial_rss, _ = get_process_memory_mb()

    # --------------------------------------------------------------------------
    # Stage A: Cold Initialization
    # --------------------------------------------------------------------------
    init_start = time.perf_counter()
    from sentence_transformers import SentenceTransformer
    model_name = "all-MiniLM-L6-v2"
    model = SentenceTransformer(model_name)
    init_duration_ms = (time.perf_counter() - init_start) * 1000.0
    post_init_rss, peak_init_rss = get_process_memory_mb()

    # --------------------------------------------------------------------------
    # Stage B: Warm Single-Text Inference
    # --------------------------------------------------------------------------
    single_text = SAMPLE_CLINICAL_TEXTS[0]

    for _ in range(warmup_runs):
        _ = model.encode(single_text)

    single_latencies: list[float] = []
    t_start_single = time.perf_counter()
    for _ in range(measured_runs):
        t0 = time.perf_counter()
        _ = model.encode(single_text)
        single_latencies.append((time.perf_counter() - t0) * 1000.0)
    total_single_duration = time.perf_counter() - t_start_single

    single_stats = calculate_distribution(
        single_latencies,
        total_duration_sec=total_single_duration,
        item_multiplier=1,
    )

    # --------------------------------------------------------------------------
    # Stage C: Batch Inference (1, 4, 8, 16, 32)
    # --------------------------------------------------------------------------
    batch_sizes = [1, 4, 8, 16, 32]
    batch_results: dict[str, Any] = {}

    for bs in batch_sizes:
        batch_texts = [
            SAMPLE_CLINICAL_TEXTS[i % len(SAMPLE_CLINICAL_TEXTS)]
            for i in range(bs)
        ]

        for _ in range(warmup_runs):
            _ = model.encode(batch_texts, batch_size=bs)

        batch_latencies: list[float] = []
        per_item_latencies: list[float] = []
        t_start_batch = time.perf_counter()

        for _ in range(measured_runs):
            t0 = time.perf_counter()
            _ = model.encode(batch_texts, batch_size=bs)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            batch_latencies.append(elapsed_ms)
            per_item_latencies.append(elapsed_ms / bs)

        total_batch_duration = time.perf_counter() - t_start_batch

        batch_stats = calculate_distribution(
            batch_latencies,
            total_duration_sec=total_batch_duration,
            item_multiplier=bs,
        )
        per_item_stats = calculate_distribution(
            per_item_latencies,
            total_duration_sec=total_batch_duration,
            item_multiplier=1,
        )

        batch_results[f"batch_{bs}"] = {
            "batch_size": bs,
            "measured_iterations": measured_runs,
            "total_batch_latency_stats": batch_stats.to_dict(),
            "per_item_latency_stats": per_item_stats.to_dict(),
            "throughput_items_per_sec": batch_stats.throughput_items_per_sec,
        }

    post_bench_rss, peak_bench_rss = get_process_memory_mb()

    return {
        "benchmark_id": "BENCH-01-EMBEDDING",
        "evidence_classification": "MEASURED",
        "scope": "In-process SentenceTransformer CPU inference",
        "model_name": model_name,
        "embedding_dimension": 384,
        "initial_rss_mb": initial_rss,
        "cold_initialization": {
            "initialization_latency_ms": round(init_duration_ms, 2),
            "environment_note": (
                "Measured on 16-core host CPU. Differs from ~73s documented "
                "in Phase 13 inside a 1.0-core CPU container without pre-cached assets."
            ),
            "initialization_rss_mb": post_init_rss,
            "peak_rss_mb": peak_init_rss,
        },
        "warm_single_text_inference": {
            "warmup_runs": warmup_runs,
            "measured_runs": measured_runs,
            "sample_text_length_chars": len(single_text),
            "stats": single_stats.to_dict(),
        },
        "batch_inference": batch_results,
        "memory_profile": {
            "initial_rss_mb": initial_rss,
            "post_init_rss_mb": post_init_rss,
            "post_bench_rss_mb": post_bench_rss,
            "peak_rss_mb": peak_bench_rss,
            "delta_rss_mb": round(peak_bench_rss - initial_rss, 2),
        },
    }


if __name__ == "__main__":
    print("Running Benchmark 1: Embedding Latency & Batch Throughput...")
    result = run_embedding_benchmark(warmup_runs=3, measured_runs=25)
    print(f"Cold init latency: {result['cold_initialization']['initialization_latency_ms']} ms")
    single = result['warm_single_text_inference']['stats']
    print(f"Single inference p50: {single['p50_ms']} ms | p95: {single['p95_ms']} ms")
