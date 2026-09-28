"""
Tests for Phase 9 Production Isolation and Empirical Benchmark Guardrails.
Verifies that no Phase 9 module is imported by production services,
and that benchmark guardrails prevent unverified empirical claims.
"""

import os
import re
from pathlib import Path

from scripts.human_review_experiment import has_validated_benchmark


def test_production_isolation_no_phase9_imports():
    """Verify that services/ contains zero imports of Phase 9 modules or symbols."""
    phase9_patterns = [
        "uncertainty_schema",
        "review_schema",
        "review_policy",
        "review_priority",
        "review_audit",
        "uncertainty_metrics",
        "human_review_experiment",
        "UncertaintyRecord",
        "UncertaintyProfile",
        "HumanReviewRecord",
        "ReviewRoutingPolicy",
        "ReviewPrioritizer",
        "ReviewResolutionManager",
    ]
    pattern_regex = re.compile(r"\b(" + "|".join(phase9_patterns) + r")\b")

    services_dir = Path("services")
    violations = []

    for root, dirs, files in os.walk(services_dir):
        if ".venv" in root or "__pycache__" in root or ".pytest_cache" in root:
            continue
        for f in files:
            if f.endswith(".py"):
                path = Path(root) / f
                content = path.read_text(encoding="utf-8", errors="ignore")
                matches = pattern_regex.findall(content)
                if matches:
                    violations.append((str(path), matches))

    assert len(violations) == 0, f"Found Phase 9 imports in production services: {violations}"


def test_empirical_benchmark_guardrail():
    """Verify that has_validated_benchmark() is strictly False."""
    assert has_validated_benchmark() is False
