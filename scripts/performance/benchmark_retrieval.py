"""
Phase 14.1 — Benchmark 2: Vector Retrieval & EXPLAIN (ANALYZE, BUFFERS).

Benchmarks PostgreSQL pgvector cosine distance retrieval (<=>) across
corpus sizes (100, 1,000, 10,000, 50,000 vectors) without an HNSW index,
using an isolated unlogged benchmark table to ensure production data is untouched.

Explicit Scope Distinction:
- Raw pgvector distance scan (<=>) on unindexed vectors: MEASURED
- Full production MatchingRepository.find_similar_criteria query at scale: NOT MEASURED
"""

from __future__ import annotations

import io
import sys
import time
import uuid
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
AI_SERVICE_DIR = REPO_ROOT / "services" / "ai-service"
for p in [str(REPO_ROOT), str(AI_SERVICE_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np
import psycopg2
from scripts.performance.harness import calculate_distribution

DB_URL = "postgresql://postgres:postgres@localhost:5434/medmatch"
BENCHMARK_TABLE = "perf_isolated_vector_corpus"
EMBEDDING_DIM = 384
CORPUS_SIZES = [100, 1000, 10000, 50000]


def format_vector(arr: np.ndarray) -> str:
    return "[" + ",".join(f"{x:.5f}" for x in arr) + "]"


def setup_benchmark_table(cur: psycopg2.extensions.cursor) -> None:
    cur.execute(f"DROP TABLE IF EXISTS {BENCHMARK_TABLE};")
    cur.execute(
        f"""
        CREATE UNLOGGED TABLE {BENCHMARK_TABLE} (
            id uuid PRIMARY KEY,
            trial_id uuid NOT NULL,
            embedding vector({EMBEDDING_DIM}) NOT NULL
        );
        """
    )


def insert_vectors_batch(
    cur: psycopg2.extensions.cursor,
    count: int,
    batch_size: int = 5000,
) -> None:
    inserted = 0
    rng = np.random.default_rng(42 + count)
    while inserted < count:
        current_chunk = min(batch_size, count - inserted)
        buf = io.StringIO()
        matrix = rng.standard_normal(size=(current_chunk, EMBEDDING_DIM), dtype=np.float32)
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        matrix = matrix / np.maximum(norms, 1e-9)

        for row in matrix:
            buf.write(f"{uuid.uuid4()}\t{uuid.uuid4()}\t{format_vector(row)}\n")

        buf.seek(0)
        cur.copy_from(
            buf,
            BENCHMARK_TABLE,
            columns=("id", "trial_id", "embedding"),
        )
        inserted += current_chunk


def run_explain_analyze(
    cur: psycopg2.extensions.cursor,
    query_vec_str: str,
    top_k: int = 5,
) -> dict[str, Any]:
    query = f"""
        EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
        SELECT id, trial_id, embedding <=> '{query_vec_str}'::vector AS distance
        FROM {BENCHMARK_TABLE}
        ORDER BY distance ASC
        LIMIT {top_k};
    """
    cur.execute(query)
    raw_json = cur.fetchone()[0]
    plan_info = raw_json[0]["Plan"]
    planning_time = raw_json[0].get("Planning Time", 0.0)
    execution_time = raw_json[0].get("Execution Time", 0.0)

    node_type = plan_info.get("Node Type", "")
    plans = plan_info.get("Plans", [])
    scan_node = None
    if node_type == "Limit" and plans:
        sort_or_scan = plans[0]
        if sort_or_scan.get("Node Type") in ("Sort", "Top-N Heapsort"):
            sort_plans = sort_or_scan.get("Plans", [])
            if sort_plans:
                scan_node = sort_plans[0]
        else:
            scan_node = sort_or_scan
    elif "Scan" in node_type:
        scan_node = plan_info

    scan_type = scan_node.get("Node Type", "Unknown") if scan_node else "Unknown"
    shared_hit_blocks = plan_info.get("Shared Hit Blocks", 0)
    shared_read_blocks = plan_info.get("Shared Read Blocks", 0)

    return {
        "node_type": node_type,
        "scan_type": scan_type,
        "planning_time_ms": planning_time,
        "execution_time_ms": execution_time,
        "shared_hit_blocks": shared_hit_blocks,
        "shared_read_blocks": shared_read_blocks,
    }


def run_retrieval_benchmark(
    warmup_queries: int = 3,
    measured_queries: int = 25,
    top_k: int = 5,
) -> dict[str, Any]:
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = False
    cur = conn.cursor()

    results_by_corpus: dict[str, Any] = {}
    current_count = 0

    try:
        setup_benchmark_table(cur)
        conn.commit()

        rng = np.random.default_rng(12345)
        test_queries = []
        for _ in range(max(warmup_queries, measured_queries) + 10):
            q_vec = rng.standard_normal(size=EMBEDDING_DIM, dtype=np.float32)
            q_vec = q_vec / np.linalg.norm(q_vec)
            test_queries.append(format_vector(q_vec))

        for target_size in CORPUS_SIZES:
            needed = target_size - current_count
            if needed > 0:
                insert_vectors_batch(cur, needed)
                conn.commit()
                current_count = target_size

            cur.execute(f"ANALYZE {BENCHMARK_TABLE};")
            conn.commit()

            for i in range(warmup_queries):
                q = test_queries[i % len(test_queries)]
                cur.execute(
                    f"SELECT id, embedding <=> '{q}'::vector AS d FROM {BENCHMARK_TABLE} ORDER BY d LIMIT {top_k};"
                )
                cur.fetchall()

            explain_result = run_explain_analyze(cur, test_queries[0], top_k=top_k)

            latencies_ms: list[float] = []
            t_start = time.perf_counter()
            for i in range(measured_queries):
                q = test_queries[(i + warmup_queries) % len(test_queries)]
                t0 = time.perf_counter()
                cur.execute(
                    f"SELECT id, trial_id, embedding <=> '{q}'::vector AS d FROM {BENCHMARK_TABLE} ORDER BY d LIMIT {top_k};"
                )
                cur.fetchall()
                latencies_ms.append((time.perf_counter() - t0) * 1000.0)

            total_dur = time.perf_counter() - t_start
            stats = calculate_distribution(latencies_ms, total_duration_sec=total_dur)

            results_by_corpus[f"corpus_{target_size}"] = {
                "corpus_size": target_size,
                "top_k": top_k,
                "measured_queries": measured_queries,
                "stats": stats.to_dict(),
                "explain_plan": explain_result,
            }

        # Check existing production table
        cur.execute("SELECT COUNT(*) FROM trial_embeddings;")
        prod_count = cur.fetchone()[0]

    finally:
        cur.execute(f"DROP TABLE IF EXISTS {BENCHMARK_TABLE};")
        conn.commit()
        cur.close()
        conn.close()

    return {
        "benchmark_id": "BENCH-02-VECTOR-RETRIEVAL",
        "evidence_classification": "MEASURED",
        "scope": "Raw pgvector vector-scan primitive on isolated unlogged table",
        "production_matching_repository_status": "NOT MEASURED at scale (contains hospital filtering, joins, ranking)",
        "index_type": "NONE (Sequential Scan)",
        "distance_operator": "<=> (Cosine Distance)",
        "production_table_row_count": prod_count,
        "results_by_corpus": results_by_corpus,
    }


if __name__ == "__main__":
    print("Running Benchmark 2: Vector Retrieval & EXPLAIN (ANALYZE, BUFFERS)...")
    result = run_retrieval_benchmark()
    for c_key, data in result["results_by_corpus"].items():
        st = data["stats"]
        exp = data["explain_plan"]
        print(f"Corpus {data['corpus_size']:5d}: p50={st['p50_ms']:5.2f}ms | Scan={exp['scan_type']} | Exec={exp['execution_time_ms']:5.2f}ms")
