"""
Integration tests for MedMatch Phase 12 Master Pipeline.
Phase 12: Clinical Safety.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest
from scripts.run_phase12_pipeline import run_phase12_pipeline


def test_pipeline_execution_and_artifacts(tmp_path: Path):
    repo_root = Path(__file__).resolve().parent.parent.parent
    data_dir = repo_root / "data"
    output_dir = tmp_path / "phase12_test_results"

    # Execute pipeline in temporary directory
    run_phase12_pipeline(data_dir=data_dir, output_dir=output_dir)

    expected_files = [
        "s_e0_baseline.json",
        "s_e1_gates.json",
        "s_e2_uncertainty.json",
        "s_e3_grounding.json",
        "s_e4_full_safety.json",
        "safety_ablations.json",
        "error_injection_results.json",
        "safety_manifest.json",
        "phase12_summary.json",
    ]

    for fname in expected_files:
        fpath = output_dir / fname
        assert fpath.exists(), f"Expected artifact {fname} was not produced."
        content = json.loads(fpath.read_text(encoding="utf-8"))
        assert content is not None

    # Verify manifest integrity
    manifest = json.loads((output_dir / "safety_manifest.json").read_text(encoding="utf-8"))
    assert manifest["phase"] == "Phase 12 — Clinical Safety"
    assert manifest["is_development_fixture_observation_only"] is True
    assert manifest["clinical_claim_permitted"] is False
    assert manifest["scenarios_count"] == 24
    assert len(manifest["experiments_executed"]) == 5
    assert len(manifest["ablations_executed"]) == 7
    assert len(manifest["error_injections_executed"]) == 14

    # Verify summary metrics
    summary = json.loads((output_dir / "phase12_summary.json").read_text(encoding="utf-8"))
    assert summary["s_e0_synthetic_unmitigated_unsafe_rate"] > 0.0
    assert summary["s_e4_synthetic_safety_pipeline_unsafe_rate"] == 0.0
    assert summary["error_injection"]["aggregate_interception_rate"] == 1.0
    assert summary["error_injection"]["prevention_rate"] > 0.0
    assert summary["error_injection"]["mitigation_rate"] > 0.0
