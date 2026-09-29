"""
Tests for Phase 14.1 Performance Benchmark Harness Utilities.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.performance.harness import (
    calculate_distribution,
    get_process_memory_mb,
    capture_environment_metadata,
)


def test_calculate_distribution_empty():
    stats = calculate_distribution([])
    assert stats.sample_count == 0
    assert stats.mean_ms == 0.0
    assert stats.p50_ms == 0.0


def test_calculate_distribution_single():
    stats = calculate_distribution([42.5])
    assert stats.sample_count == 1
    assert stats.mean_ms == 42.5
    assert stats.p50_ms == 42.5
    assert stats.p99_ms == 42.5
    assert stats.min_ms == 42.5
    assert stats.max_ms == 42.5


def test_calculate_distribution_multi():
    data = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]
    stats = calculate_distribution(data, total_duration_sec=1.0)
    assert stats.sample_count == 10
    assert stats.mean_ms == 55.0
    assert stats.min_ms == 10.0
    assert stats.max_ms == 100.0
    assert stats.p50_ms == 55.0
    assert stats.p90_ms == 91.0
    assert stats.p99_ms == 99.1
    assert stats.throughput_items_per_sec == 10.0


def test_get_process_memory():
    rss_mb, peak_mb = get_process_memory_mb()
    assert rss_mb >= 0.0
    assert peak_mb >= 0.0


def test_capture_environment_metadata():
    meta = capture_environment_metadata()
    assert "timestamp_utc" in meta
    assert "git_commit" in meta
    assert "python_version" in meta
    assert "cpu_count" in meta
    assert meta["cpu_count"] >= 1
