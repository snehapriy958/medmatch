"""
Phase 14.1 — Benchmark: Gemini LLM Latency.

Evaluates Gemini LLM inference latency. In the offline/local benchmark
environment without live production Google GenAI credentials, external LLM
calls are NOT executed, and no synthetic latency values are fabricated.

Status: NOT MEASURED
Scope: External Google GenAI Cloud API
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
AI_SERVICE_DIR = REPO_ROOT / "services" / "ai-service"
for p in [str(REPO_ROOT), str(AI_SERVICE_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)


def run_gemini_benchmark() -> dict[str, Any]:
    """
    Check for live Gemini API credentials and characterize measurement status.
    In local/offline harness without credentials, returns strictly NOT MEASURED.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    has_credentials = bool(api_key and api_key != "mock-gemini-key" and not api_key.startswith("test_"))

    return {
        "benchmark_id": "BENCH-08-GEMINI",
        "evidence_classification": "NOT MEASURED",
        "status": "NOT MEASURED",
        "scope": "External Google GenAI Cloud API (gemini-2.5-flash)",
        "has_live_credentials": has_credentials,
        "reason": (
            "Live Gemini API calls require external network access and valid production API keys. "
            "In this local offline benchmark environment, live external calls were omitted to ensure "
            "determinism, avoid unexpected API quota usage, and prevent reliance on fabricated mocks. "
            "Live Gemini inference latency is strictly NOT MEASURED in this benchmark suite, and no "
            "synthetic latency values are fabricated."
        ),
        "empirical_measurements": None,
    }


if __name__ == "__main__":
    res = run_gemini_benchmark()
    print(f"Gemini Benchmark Status: {res['status']}")
    print(f"Reason: {res['reason']}")
