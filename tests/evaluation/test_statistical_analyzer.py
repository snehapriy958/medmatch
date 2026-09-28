"""
Tests for Phase 11 Statistical Analyzer & Safeguard Layer.
Phase 11: Evaluation & Ablation.
"""

from scripts.evaluation_schema import (
    EligibilityMetrics,
    ExperimentConfig,
    ExperimentResult,
    ExperimentType,
)
from scripts.statistical_analyzer import StatisticalAnalyzer


class TestStatisticalAnalyzer:
    """Verifies statistical inference safeguards and sample-size thresholds."""

    @staticmethod
    def _create_mock_result(exp_id: str, n_cases: int, correct_count: int) -> ExperimentResult:
        cases = []
        for i in range(n_cases):
            pred = "ELIGIBLE" if i < correct_count else "INELIGIBLE"
            cases.append(
                {
                    "patient_id": f"P{i:03d}",
                    "trial_id": "T001",
                    "predicted_eligibility": pred,
                    "ground_truth_eligibility": "ELIGIBLE",
                }
            )
        config = ExperimentConfig(
            experiment_id=exp_id,
            experiment_type=ExperimentType.E0_BASELINE,
            description="Mock experiment for statistical unit test",
            dataset_version="0.1.0-fixture",
            patient_representation="raw_clinical_note",
        )
        return ExperimentResult(
            experiment_id=exp_id,
            experiment_type=ExperimentType.E0_BASELINE,
            config=config,
            dataset_classification="DEVELOPMENT/TEST FIXTURE ONLY",
            sample_size=n_cases,
            eligibility_metrics=EligibilityMetrics(accuracy=correct_count / float(n_cases) if n_cases > 0 else 0.0),
            execution_time_seconds=0.01,
            evaluated_cases=cases,
        )

    def test_refuses_inference_on_small_development_fixture(self):
        # n=6 cases
        exp_a = self._create_mock_result("SYS_A", 6, 4)
        exp_b = self._create_mock_result("SYS_B", 6, 5)

        record = StatisticalAnalyzer.compare_experiments(exp_a, exp_b)

        assert record.sample_size == 6
        assert record.inference_permitted is False
        assert record.p_value is None
        assert record.confidence_interval_95 is None
        assert record.statistically_significant is False
        assert "minimum threshold" in record.justification_for_inference

    def test_permits_inference_on_sufficient_sample_size(self):
        # n=50 cases
        exp_a = self._create_mock_result("SYS_A", 50, 45)
        exp_b = self._create_mock_result("SYS_B", 50, 30)

        record = StatisticalAnalyzer.compare_experiments(exp_a, exp_b)

        assert record.sample_size == 50
        assert record.inference_permitted is True
        assert record.p_value is not None
        assert isinstance(record.statistically_significant, bool)
