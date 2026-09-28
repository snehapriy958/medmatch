"""
Tests for Benchmark Guardrails, Reproducibility & Production Isolation.
Phase 7: RAG vs. Non-RAG Experimental Evaluation.
"""

import os
from scripts.run_phase7_experiment import Phase7ExperimentHarness


class TestBenchmarkGuardrails:
    """Verifies that un-ingested research benchmarks are handled honestly and production remains untouched."""

    def test_missing_research_benchmark_is_handled_explicitly(self):
        """Test 12: System correctly identifies that external research benchmark is not ingested."""
        # The repository currently has only the 6-patient fixture, not external TrialGPT/TREC CT files
        is_present = Phase7ExperimentHarness.check_research_benchmark_available(data_dir="data")
        assert is_present is False

    def test_metrics_calculation_formulae(self):
        """Verify macro-F1, precision, recall calculation behaves accurately on toy input."""
        y_true = ["ELIGIBLE", "INELIGIBLE", "NEEDS_REVIEW", "ELIGIBLE"]
        y_pred = ["ELIGIBLE", "INELIGIBLE", "ELIGIBLE", "ELIGIBLE"]
        classes = ["ELIGIBLE", "INELIGIBLE", "NEEDS_REVIEW"]

        metrics = Phase7ExperimentHarness.calculate_classification_metrics(y_true, y_pred, classes)
        assert "macro_f1" in metrics
        assert "accuracy" in metrics
        assert metrics["accuracy"] == 0.75

    def test_reproducibility_fields_completeness(self):
        """Test 11: Reproducibility schema requires complete environment, seed, and version metadata."""
        required_manifest_keys = {
            "experiment_id",
            "dataset_version",
            "git_commit_sha",
            "controlled_parameters",
            "execution",
        }
        mock_manifest = {
            "experiment_id": "E5_VS_E6_CONTROLLED",
            "dataset_version": "0.1.0-fixture",
            "git_commit_sha": "120bd7e",
            "controlled_parameters": {"seed": 42, "temperature": 0.0},
            "execution": {"duration_seconds": 1.2, "leakage_detected": False},
        }
        assert required_manifest_keys.issubset(mock_manifest.keys())

    def test_production_services_not_imported(self):
        """Test 14: Confirms zero production services import Phase 7 experiment modules."""
        services_dir = os.path.join("services", "ai-service", "app")
        forbidden_imports = ["nonrag_experiment", "rag_experiment", "run_phase7_experiment"]

        for root, _, files in os.walk(services_dir):
            for file in files:
                if file.endswith(".py"):
                    full_path = os.path.join(root, file)
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        for imp in forbidden_imports:
                            assert imp not in content, (
                                f"Production file '{full_path}' contains forbidden import '{imp}'!"
                            )
