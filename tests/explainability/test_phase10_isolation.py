"""
Tests for Phase 10 Production Isolation and Empirical Benchmark Guardrails.
Verifies that no Phase 10 module is imported by production services,
and that benchmark guardrails prevent unverified empirical claims.
"""

import os
import re
from pathlib import Path

from scripts.explainability_experiment import has_validated_benchmark


def test_production_isolation_no_phase10_imports():
    """Verify that services/ contains zero imports of Phase 10 modules or symbols."""
    phase10_patterns = [
        "evidence_graph_schema",
        "evidence_graph_builder",
        "evidence_graph_validator",
        "explanation_schema",
        "explanation_generator",
        "explanation_validator",
        "explainability_metrics",
        "explainability_experiment",
        "EvidenceGraph",
        "EvidenceGraphNode",
        "EvidenceGraphEdge",
        "EvidenceGraphBuilder",
        "EvidenceGraphValidator",
        "StructuredExplanation",
        "DeterministicExplanationGenerator",
        "ExplanationValidator",
    ]
    pattern_regex = re.compile(r"\b(" + "|".join(phase10_patterns) + r")\b")

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

    assert len(violations) == 0, f"Found Phase 10 imports in production services: {violations}"


def test_empirical_benchmark_guardrail():
    """Verify that has_validated_benchmark() is strictly False."""
    assert has_validated_benchmark() is False
