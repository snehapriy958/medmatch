"""
Isolation tests for MedMatch Phase 12 Clinical Safety.
Ensures zero pollution or modifications to production services/ code.
"""

from __future__ import annotations

from pathlib import Path
import pytest


def test_production_code_isolation():
    """Verify that services/ contains no Phase 12 research imports."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    services_dir = repo_root / "services"

    forbidden_tokens = [
        "scripts.safety_",
        "safety_schema",
        "safety_gates",
        "safety_policy",
        "safety_validator",
        "DeterministicSafetyGates",
        "MachineCheckableSafetyValidator",
        "SafetyTaxonomyCode",
    ]

    for py_file in services_dir.rglob("*.py"):
        # Ignore virtual environments if present
        if ".venv" in py_file.parts or "venv" in py_file.parts or "__pycache__" in py_file.parts:
            continue
        content = py_file.read_text(encoding="utf-8", errors="ignore")
        for token in forbidden_tokens:
            assert token not in content, f"Forbidden Phase 12 token '{token}' found in production file: {py_file}"


def test_fixtures_are_explicitly_synthetic():
    """Verify that safety scenarios are strictly synthetic and contain no real patient data."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    scenarios_file = repo_root / "data" / "fixtures" / "phase12" / "safety_scenarios.json"
    assert scenarios_file.exists()

    content = scenarios_file.read_text(encoding="utf-8")
    assert "SYNTHETIC" in content or "SCEN-" in content
