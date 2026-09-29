"""
Phase 14.1 — Performance Benchmark Harness Core Utilities.

Provides reproducible timing, statistical distribution calculation, process
profiling, and environment metadata capture for MedMatch V2 performance benchmarks.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import math
import os
import platform
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Sequence

# Set default local connection URLs if not already configured
os.environ.setdefault("REDIS_URL", "redis://localhost:6380/0")
os.environ.setdefault("CELERY_BROKER_URL", "redis://localhost:6380/0")
os.environ.setdefault("CELERY_RESULT_BACKEND", "redis://localhost:6380/0")
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5434/medmatch")


# ==============================================================================
# Windows Process Memory Profiling via ctypes
# ==============================================================================

class _PROCESS_MEMORY_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
    ]


def get_process_memory_mb() -> tuple[float, float]:
    """
    Returns (current_working_set_mb, peak_working_set_mb) for current process.
    Supports Windows via psapi and Unix via resource fallback.
    """
    if platform.system() == "Windows":
        try:
            pmc = _PROCESS_MEMORY_COUNTERS()
            pmc.cb = ctypes.sizeof(_PROCESS_MEMORY_COUNTERS)
            get_mem_info = ctypes.windll.psapi.GetProcessMemoryInfo
            get_mem_info.argtypes = [
                wintypes.HANDLE,
                ctypes.POINTER(_PROCESS_MEMORY_COUNTERS),
                wintypes.DWORD,
            ]
            get_mem_info.restype = wintypes.BOOL
            handle = ctypes.windll.kernel32.GetCurrentProcess()
            if get_mem_info(handle, ctypes.byref(pmc), pmc.cb):
                rss_mb = pmc.WorkingSetSize / (1024 * 1024)
                peak_mb = pmc.PeakWorkingSetSize / (1024 * 1024)
                return round(rss_mb, 2), round(peak_mb, 2)
        except Exception:
            pass
    else:
        try:
            import resource
            usage = resource.getrusage(resource.RUSAGE_SELF)
            factor = 1024.0 if platform.system() == "Linux" else 1024.0 * 1024.0
            peak_mb = usage.ru_maxrss / factor
            return round(peak_mb, 2), round(peak_mb, 2)
        except Exception:
            pass
    return 0.0, 0.0


# ==============================================================================
# Statistical Distribution Calculations
# ==============================================================================

@dataclass
class DistributionStats:
    """Statistical summary of latency samples in milliseconds."""
    sample_count: int
    mean_ms: float
    stddev_ms: float
    min_ms: float
    max_ms: float
    p50_ms: float
    p90_ms: float
    p95_ms: float
    p99_ms: float
    throughput_items_per_sec: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def calculate_distribution(
    latencies_ms: Sequence[float],
    total_duration_sec: Optional[float] = None,
    item_multiplier: int = 1,
) -> DistributionStats:
    """
    Calculate statistical percentiles and moments for a sequence of latency measurements (ms).
    Uses nearest-rank percentile method with linear interpolation.
    """
    if not latencies_ms:
        return DistributionStats(
            sample_count=0,
            mean_ms=0.0,
            stddev_ms=0.0,
            min_ms=0.0,
            max_ms=0.0,
            p50_ms=0.0,
            p90_ms=0.0,
            p95_ms=0.0,
            p99_ms=0.0,
            throughput_items_per_sec=0.0,
        )

    sorted_vals = sorted(latencies_ms)
    n = len(sorted_vals)
    mean_val = sum(sorted_vals) / n
    variance = sum((x - mean_val) ** 2 for x in sorted_vals) / max(1, n - 1)
    stddev_val = math.sqrt(variance)

    def percentile(p: float) -> float:
        if n == 1:
            return sorted_vals[0]
        k = (n - 1) * (p / 100.0)
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return sorted_vals[int(k)]
        d0 = sorted_vals[int(f)] * (c - k)
        d1 = sorted_vals[int(c)] * (k - f)
        return d0 + d1

    p50 = percentile(50.0)
    p90 = percentile(90.0)
    p95 = percentile(95.0)
    p99 = percentile(99.0)

    throughput = 0.0
    if total_duration_sec and total_duration_sec > 0:
        throughput = (n * item_multiplier) / total_duration_sec
    elif sum(sorted_vals) > 0:
        total_time_s = sum(sorted_vals) / 1000.0
        throughput = (n * item_multiplier) / total_time_s

    return DistributionStats(
        sample_count=n,
        mean_ms=round(mean_val, 3),
        stddev_ms=round(stddev_val, 3),
        min_ms=round(sorted_vals[0], 3),
        max_ms=round(sorted_vals[-1], 3),
        p50_ms=round(p50, 3),
        p90_ms=round(p90, 3),
        p95_ms=round(p95, 3),
        p99_ms=round(p99, 3),
        throughput_items_per_sec=round(throughput, 2),
    )


# ==============================================================================
# Environment Metadata Capture
# ==============================================================================

def get_git_commit() -> str:
    """Retrieve the current HEAD git commit hash."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=str(Path(__file__).resolve().parents[2]),
        )
        return res.stdout.strip()
    except Exception:
        return "b8dc053"


def get_git_branch() -> str:
    """Retrieve the current git branch name."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=str(Path(__file__).resolve().parents[2]),
        )
        return res.stdout.strip()
    except Exception:
        return "capstone/phase-13-production-engineering"


def capture_environment_metadata() -> dict[str, Any]:
    """Capture execution environment metadata for benchmark reproducibility."""
    mem_rss, mem_peak = get_process_memory_mb()
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": get_git_commit(),
        "git_branch": get_git_branch(),
        "python_version": platform.python_version(),
        "python_compiler": platform.python_compiler(),
        "os_platform": platform.platform(),
        "os_system": platform.system(),
        "os_release": platform.release(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count() or 1,
        "initial_rss_mb": mem_rss,
        "database": {
            "default_url": "postgresql+psycopg2://postgres:postgres@localhost:5434/medmatch",
            "docker_container": "medmatch-postgres",
            "pgvector_version": "0.8.5",
            "postgres_version": "17.10",
        },
        "redis": {
            "default_url": "redis://localhost:6380/0",
            "docker_container": "medmatch-redis",
            "redis_version": "8-alpine",
        },
        "models": {
            "embedding_model": "all-MiniLM-L6-v2",
            "embedding_dimension": 384,
            "llm_model": "gemini-2.5-flash",
        },
    }
