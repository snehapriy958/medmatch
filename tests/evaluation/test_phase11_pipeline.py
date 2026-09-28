"""
Tests for Phase 11 Full Evaluation Pipeline Execution & Artifact Integrity.
Phase 11: Evaluation & Ablation.
"""

import json
from pathlib import Path
from scripts.run_phase11_pipeline import run_pipeline


class TestPhase11Pipeline:
    """Verifies end-to-end pipeline execution and output artifact structure."""

    def test_pipeline_execution_and_artifacts(self, tmp_path: Path):
        data_dir = Path("data")
        output_dir = tmp_path / "results_test"

        run_pipeline(data_dir=data_dir, output_dir=output_dir)

        expected_files = [
            "dataset_validation.json",
            "experiment_manifest.json",
            "e0_baseline.json",
            "e1_structured_profile.json",
            "e2_dense_rag.json",
            "e3_hybrid_rag.json",
            "e4_reranked_rag.json",
            "ablation_results.json",
            "error_analysis.json",
            "statistical_analysis.json",
            "phase11_summary.json",
        ]

        for fname in expected_files:
            fpath = output_dir / fname
            assert fpath.exists(), f"Missing required artifact: {fname}"
            # Verify JSON parseability
            content = json.loads(fpath.read_text(encoding="utf-8"))
            assert content is not None

        # Verify summary guardrails
        summary = json.loads((output_dir / "phase11_summary.json").read_text(encoding="utf-8"))
        assert summary["empirical_claims_permitted"] is False
        assert summary["statistical_inference_permitted"] is False
        assert summary["development_fixture_sample_size"] == 6
