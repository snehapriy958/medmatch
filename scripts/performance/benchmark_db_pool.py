"""
Phase 14.1 — Benchmark 6: Database Connection Pool Behavior.

Evaluates SQLAlchemy QueuePool connection checkout latency, concurrency limits,
and overflow behavior for a single local engine.

Explicit Scope Distinctions & Methodology Qualifications:
A. Production Pool Configuration:
   - pool_size = 10, max_overflow = 20, pool_timeout = 30 (theoretical per-engine capacity = 30)
B. Isolated Benchmark Pool Configuration:
   - pool_size = 5, max_overflow = 10, pool_timeout = 1.0 (theoretical capacity = 15)
   - "An isolated benchmark engine with a deliberately bounded pool was used to validate
     pool exhaustion behavior; this does not measure the production pool capacity."
C. Measured Single-Engine Behavior:
   - QueuePool checkout latency and exhaustion on the isolated bounded engine = MEASURED
D. Unmeasured Cluster-Wide Saturation:
   - Aggregate cluster-wide multi-replica saturation = NOT MEASURED
   - PERF-04 classification = CONFIGURATION RISK ONLY
"""

from __future__ import annotations

import concurrent.futures
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
AI_SERVICE_DIR = REPO_ROOT / "services" / "ai-service"
for p in [str(REPO_ROOT), str(AI_SERVICE_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from sqlalchemy import create_engine, text
from sqlalchemy.exc import TimeoutError as SATimeoutError
from scripts.performance.harness import (
    calculate_distribution,
    get_process_memory_mb,
)

DB_URL = "postgresql+psycopg2://postgres:postgres@localhost:5434/medmatch"


def run_db_pool_benchmark() -> dict[str, Any]:
    """
    Benchmark SQLAlchemy QueuePool on a single engine:
    1. Single checkout latency distribution.
    2. Concurrent connection checkout up to pool_size + max_overflow.
    3. Overflow exhaustion test.
    """
    initial_rss, _ = get_process_memory_mb()

    # Create engine with standard MedMatch settings (pool_size=5, max_overflow=10, timeout=1.0)
    engine = create_engine(
        DB_URL,
        pool_size=5,
        max_overflow=10,
        pool_timeout=1.0,
    )

    # 1. Measure sequential checkout latencies
    sequential_latencies: list[float] = []
    for _ in range(25):
        t0 = time.perf_counter()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1;"))
        sequential_latencies.append((time.perf_counter() - t0) * 1000.0)

    seq_stats = calculate_distribution(sequential_latencies)

    # 2. Concurrent checkout within capacity (15 connections = 5 base + 10 overflow)
    def hold_connection(hold_time_s: float = 0.2):
        t0 = time.perf_counter()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1;"))
            time.sleep(hold_time_s)
        return (time.perf_counter() - t0) * 1000.0

    concurrent_success = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        futures = [executor.submit(hold_connection, 0.2) for _ in range(15)]
        for f in concurrent.futures.as_completed(futures):
            try:
                _ = f.result()
                concurrent_success += 1
            except Exception:
                pass

    # 3. Overflow exhaustion test (attempt 16th concurrent connection with hold)
    exhaustion_detected = False
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        # Hold 15 connections
        futures_hold = [executor.submit(hold_connection, 0.5) for _ in range(15)]
        time.sleep(0.05)  # Allow all 15 to acquire
        future_excess = executor.submit(hold_connection, 0.1)
        try:
            future_excess.result()
        except SATimeoutError:
            exhaustion_detected = True
        except Exception:
            pass
        # Wait for holding futures to complete
        for f in futures_hold:
            try:
                f.result()
            except Exception:
                pass

    engine.dispose()
    post_rss, peak_rss = get_process_memory_mb()

    return {
        "benchmark_id": "BENCH-06-DB-POOL",
        "benchmark_title": "Database Connection Pool Behavior",
        "evidence_classification": "CONFIGURATION RISK ONLY",
        "scope": "Local SQLAlchemy QueuePool checkout & exhaustion microbenchmark",
        "production_pool_configuration": {
            "pool_size": 10,
            "max_overflow": 20,
            "pool_timeout_seconds": 30,
            "theoretical_max_capacity_per_engine": 30,
        },
        "isolated_benchmark_pool_configuration": {
            "pool_size": 5,
            "max_overflow": 10,
            "pool_timeout_seconds": 1.0,
            "theoretical_max_capacity": 15,
            "methodology_qualification": (
                "An isolated benchmark engine with a deliberately bounded pool was used to "
                "validate pool exhaustion behavior; this does not measure the production pool capacity."
            ),
        },
        "measured_single_engine_behavior": {
            "status": "MEASURED",
            "sequential_checkout_stats": seq_stats.to_dict(),
            "concurrent_connections_tested": 15,
            "concurrent_success_count": concurrent_success,
            "overflow_exhaustion_detected": exhaustion_detected,
        },
        "unmeasured_cluster_wide_saturation": {
            "status": "NOT MEASURED",
            "reason": (
                "Cluster-wide connection pool saturation was NOT MEASURED. In a full production deployment, "
                "multiple replicas of ai-service, worker, and auth-service create separate connection pools. "
                "With the production configuration of 30 connections per engine, 3 ai-service replicas (90 conns) "
                "+ 3 worker replicas (90 conns) + auth-service pools aggregate to over 180 potential connections, "
                "exceeding PostgreSQL default max_connections (100). This remains a CONFIGURATION RISK ONLY."
            ),
        },
        "memory_profile": {
            "initial_rss_mb": initial_rss,
            "post_rss_mb": post_rss,
            "peak_rss_mb": peak_rss,
        },
    }


if __name__ == "__main__":
    print("Running Benchmark 6: Database Connection Pool Behavior...")
    res = run_db_pool_benchmark()
    print(f"Single engine checkout p50: {res['single_engine_pool']['sequential_checkout_stats']['p50_ms']} ms")
    print(f"Concurrent checkouts (15/15): {res['single_engine_pool']['concurrent_success_count']}")
    print(f"Exhaustion detected on 16th: {res['single_engine_pool']['overflow_exhaustion_detected']}")
    print(f"Cluster-wide saturation: {res['cluster_wide_saturation']['status']}")
