"""
MedMatch V2 — Master Engineering Performance & Capacity Benchmark Suite.
Phase 5 Deliverable.

Benchmarks:
1. SentenceTransformer Embedding Latency & Batch Throughput (all-MiniLM-L6-v2)
2. Vector Similarity Search Latency (Cosine Distance Search over Index)
3. Deterministic Clinical Eligibility Engine Evaluation Latency & Throughput
4. RS256 JWT Issuance & Cryptographic Verification Latency & Throughput
5. Cache Latency Comparison (Cache Hit vs. Cache Miss / Inference)
"""

from __future__ import annotations

import json
import math
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "services" / "ai-service"))

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.embeddings.model import EmbeddingModel
from evaluation.evaluate_ai_pipeline import AIPipelineEvaluator, cosine_similarity


def compute_percentiles(durations_ms: List[float]) -> Dict[str, float]:
    sorted_d = sorted(durations_ms)
    n = len(sorted_d)
    if n == 0:
        return {"p50": 0.0, "p90": 0.0, "p95": 0.0, "p99": 0.0, "mean": 0.0, "min": 0.0, "max": 0.0}

    def p(q: float) -> float:
        idx = max(0, min(n - 1, int(math.ceil(q * n)) - 1))
        return sorted_d[idx]

    return {
        "p50": round(p(0.50), 3),
        "p90": round(p(0.90), 3),
        "p95": round(p(0.95), 3),
        "p99": round(p(0.99), 3),
        "mean": round(sum(sorted_d) / float(n), 3),
        "min": round(sorted_d[0], 3),
        "max": round(sorted_d[-1], 3),
    }


def benchmark_embeddings(iterations: int = 50) -> Dict[str, Any]:
    print("\n[1/5] Benchmarking SentenceTransformer Embeddings (all-MiniLM-L6-v2)...")
    model = EmbeddingModel()

    sample_texts = [
        "Patient diagnosed with stage IV non-small cell lung cancer with EGFR exon 19 deletion.",
        "Histologically confirmed invasive ductal carcinoma with triple-negative receptor profile.",
        "ECOG performance status 1, absolute neutrophil count 2,400/uL, platelets 180,000/uL.",
        "Exclusion criteria: active or untreated central nervous system metastases or leptomeningeal disease.",
        "Patient has prior systemic progression on osimertinib 80mg daily and carboplatin pemetrexed."
    ]

    # Warmup
    for text in sample_texts:
        model.encode(text)

    # 1. Single text latency
    single_latencies = []
    for _ in range(iterations):
        for text in sample_texts:
            t0 = time.perf_counter()
            model.encode(text)
            t1 = time.perf_counter()
            single_latencies.append((t1 - t0) * 1000.0)

    single_stats = compute_percentiles(single_latencies)
    throughput_single = round(1000.0 / single_stats["mean"], 2) if single_stats["mean"] > 0 else 0.0

    # 2. Batch throughput (simulated batching)
    batch_sizes = [4, 8, 16, 32]
    batch_results = {}
    sentence_model = EmbeddingModel._model

    if sentence_model is not None:
        for b_size in batch_sizes:
            batch_corpus = (sample_texts * ((b_size // len(sample_texts)) + 1))[:b_size]
            batch_latencies = []
            for _ in range(15):
                t0 = time.perf_counter()
                sentence_model.encode(batch_corpus, normalize_embeddings=True)
                t1 = time.perf_counter()
                batch_latencies.append((t1 - t0) * 1000.0)
            b_stats = compute_percentiles(batch_latencies)
            tput = round((b_size / (b_stats["mean"] / 1000.0)), 2) if b_stats["mean"] > 0 else 0.0
            batch_results[f"batch_{b_size}"] = {
                "batch_size": b_size,
                "latency_ms": b_stats,
                "throughput_texts_per_sec": tput
            }

    return {
        "single_inference": single_stats,
        "single_throughput_texts_per_sec": throughput_single,
        "batches": batch_results
    }


def benchmark_vector_search(corpus_size: int = 2000, queries: int = 50) -> Dict[str, Any]:
    print(f"\n[2/5] Benchmarking Dense Vector Cosine Search (Corpus size = {corpus_size})...")
    model = EmbeddingModel()
    base_text = "Stage IV Non-Small Cell Lung Cancer with EGFR activating mutation"
    base_vec = model.encode(base_text)

    # Generate synthetic normalized 384-d vectors with controlled drift
    import random
    random.seed(42)
    corpus = []
    for _ in range(corpus_size):
        drift = [random.gauss(0, 0.05) for _ in range(384)]
        v = [b + d for b, d in zip(base_vec, drift)]
        norm = math.sqrt(sum(x * x for x in v))
        corpus.append([x / norm for x in v])

    query_vec = base_vec

    latencies = []
    for _ in range(queries):
        t0 = time.perf_counter()
        scores = [cosine_similarity(query_vec, doc) for doc in corpus]
        # Top-5 selection
        top5 = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:5]
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000.0)

    stats = compute_percentiles(latencies)
    tput = round(1000.0 / stats["mean"], 2) if stats["mean"] > 0 else 0.0
    return {
        "corpus_size": corpus_size,
        "search_latencies_ms": stats,
        "queries_per_second": tput
    }


def benchmark_deterministic_reasoner(iterations: int = 100) -> Dict[str, Any]:
    print("\n[3/5] Benchmarking Deterministic Clinical Eligibility Engine...")
    dataset_file = REPO_ROOT / "evaluation" / "fixtures" / "synthetic_eval_dataset.json"
    gold_file = REPO_ROOT / "evaluation" / "gold_labels.json"
    evaluator = AIPipelineEvaluator(dataset_file, gold_file)

    latencies = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        evaluator.run_improved_matching()
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000.0)

    stats = compute_percentiles(latencies)
    total_evals_per_run = len(evaluator.dataset)
    tput = round((total_evals_per_run / (stats["mean"] / 1000.0)), 2) if stats["mean"] > 0 else 0.0

    return {
        "batch_eval_latencies_ms": stats,
        "scenarios_evaluated_per_run": total_evals_per_run,
        "evaluations_per_second": tput
    }


def benchmark_jwt_crypto(iterations: int = 500) -> Dict[str, Any]:
    print("\n[4/5] Benchmarking RS256 JWT Token Signing & Cryptographic Verification...")
    from uuid import uuid4

    private_key_path = REPO_ROOT / "services" / "auth-service" / "src" / "main" / "resources" / "keys" / "private.pem"
    public_key_path = REPO_ROOT / "services" / "ai-service" / "keys" / "public.pem"

    with open(private_key_path, "r", encoding="utf-8") as f:
        priv_pem = f.read()
    with open(public_key_path, "r", encoding="utf-8") as f:
        pub_pem = f.read()

    payload = {
        "sub": str(uuid4()),
        "email": "doctor@hospital.org",
        "role": "PHYSICIAN",
        "hospital_id": str(uuid4()),
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
    }

    # Signing benchmark (Spring Boot Auth Service role)
    signing_latencies = []
    tokens = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        tok = jwt.encode(payload, priv_pem, algorithm="RS256")
        t1 = time.perf_counter()
        signing_latencies.append((t1 - t0) * 1000.0)
        tokens.append(tok)

    signing_stats = compute_percentiles(signing_latencies)
    signing_tput = round(1000.0 / signing_stats["mean"], 2) if signing_stats["mean"] > 0 else 0.0

    # Verification benchmark (FastAPI AI Service role)
    verify_latencies = []
    for tok in tokens:
        t0 = time.perf_counter()
        jwt.decode(tok, pub_pem, algorithms=["RS256"], options={"require": ["sub", "hospital_id", "role"]})
        t1 = time.perf_counter()
        verify_latencies.append((t1 - t0) * 1000.0)

    verify_stats = compute_percentiles(verify_latencies)
    verify_tput = round(1000.0 / verify_stats["mean"], 2) if verify_stats["mean"] > 0 else 0.0

    return {
        "signing_rs256": {
            "latencies_ms": signing_stats,
            "tokens_per_second": signing_tput
        },
        "verification_rs256": {
            "latencies_ms": verify_stats,
            "verifications_per_second": verify_tput
        }
    }


def benchmark_cache_impact() -> Dict[str, Any]:
    print("\n[5/5] Benchmarking Redis Cache Hit vs Cache Miss Latencies...")
    model = EmbeddingModel()
    text = "Stage IV Non-Small Cell Lung Cancer EGFR exon 19 deletion"

    # Cache miss = model inference
    miss_latencies = []
    for _ in range(30):
        t0 = time.perf_counter()
        model.encode(text)
        t1 = time.perf_counter()
        miss_latencies.append((t1 - t0) * 1000.0)

    miss_stats = compute_percentiles(miss_latencies)

    # In-memory / Redis cache hit simulation (dict lookup with deserialization)
    precomputed = model.encode(text)
    serialized = json.dumps(precomputed)

    hit_latencies = []
    for _ in range(1000):
        t0 = time.perf_counter()
        _ = json.loads(serialized)
        t1 = time.perf_counter()
        hit_latencies.append((t1 - t0) * 1000.0)

    hit_stats = compute_percentiles(hit_latencies)
    speedup = round(miss_stats["mean"] / hit_stats["mean"], 2) if hit_stats["mean"] > 0 else 0.0

    return {
        "cache_miss_latency_ms": miss_stats,
        "cache_hit_latency_ms": hit_stats,
        "speedup_factor": f"{speedup}x"
    }


def main():
    print("================================================================================")
    print("MEDMATCH V2 — PRODUCTION PERFORMANCE, CAPACITY & LATENCY BENCHMARK")
    print("================================================================================")

    results_dir = REPO_ROOT / "benchmarks" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    emb_results = benchmark_embeddings(iterations=30)
    search_results = benchmark_vector_search(corpus_size=2000, queries=50)
    reasoner_results = benchmark_deterministic_reasoner(iterations=50)
    jwt_results = benchmark_jwt_crypto(iterations=300)
    cache_results = benchmark_cache_impact()

    master_results = {
        "benchmark_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "embedding_benchmark": emb_results,
        "vector_search_benchmark": search_results,
        "clinical_reasoner_benchmark": reasoner_results,
        "jwt_cryptography_benchmark": jwt_results,
        "cache_impact_benchmark": cache_results
    }

    output_path = results_dir / "master_benchmark_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(master_results, f, indent=2)

    print("\n================================================================================")
    print("SUMMARY BENCHMARK REPORT")
    print("================================================================================")
    print(f"Embedding Single Inference (p50): {emb_results['single_inference']['p50']} ms | p95: {emb_results['single_inference']['p95']} ms | p99: {emb_results['single_inference']['p99']} ms")
    print(f"Embedding Throughput: {emb_results['single_throughput_texts_per_sec']} texts/sec (Single) | {emb_results['batches'].get('batch_32', {}).get('throughput_texts_per_sec', 'N/A')} texts/sec (Batch 32)")
    print(f"Dense Vector Search (2,000 vectors): {search_results['search_latencies_ms']['p50']} ms (p50) | {search_results['queries_per_second']} queries/sec")
    print(f"Clinical Eligibility Reasoner: {reasoner_results['batch_eval_latencies_ms']['p50']} ms/batch | {reasoner_results['evaluations_per_second']} evaluations/sec")
    print(f"RS256 JWT Verification: {jwt_results['verification_rs256']['latencies_ms']['p50']} ms (p50) | {jwt_results['verification_rs256']['verifications_per_second']} verifies/sec")
    print(f"Cache Hit Speedup: {cache_results['speedup_factor']} faster ({cache_results['cache_hit_latency_ms']['p50']} ms vs {cache_results['cache_miss_latency_ms']['p50']} ms)")
    print(f"\n[SUCCESS] Master benchmarks generated and saved to {output_path}")


if __name__ == "__main__":
    main()
