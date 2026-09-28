"""
Tests for Phase 11 Extended Dataset Validation.
Phase 11: Evaluation & Ablation.
"""

from pathlib import Path
from scripts.dataset_validator_extended import ExtendedDatasetValidator


class TestDatasetValidation:
    """Verifies that extended dataset validator exhaustively checks integrity and emits summaries."""

    def test_extended_dataset_validation_passes(self):
        validator = ExtendedDatasetValidator(data_dir=Path("data"))
        summary = validator.validate_and_summarize()

        assert summary.is_valid is True
        assert summary.total_patients == 6
        assert summary.total_trials == 1
        assert summary.total_criteria == 8
        assert summary.total_patient_trial_pairs == 6
        assert summary.total_criterion_labels == 48
        assert summary.patient_leakage_detected is False
        assert summary.duplicate_record_count == 0
        assert summary.invalid_record_count == 0

    def test_criterion_label_distribution(self):
        validator = ExtendedDatasetValidator(data_dir=Path("data"))
        summary = validator.validate_and_summarize()

        assert summary.criterion_label_distribution["PASS"] == 41
        assert summary.criterion_label_distribution["FAIL"] == 4
        assert summary.criterion_label_distribution["UNKNOWN"] == 3

    def test_trial_label_distribution(self):
        validator = ExtendedDatasetValidator(data_dir=Path("data"))
        summary = validator.validate_and_summarize()

        assert summary.trial_label_distribution["ELIGIBLE"] == 1
        assert summary.trial_label_distribution["INELIGIBLE"] == 3
        assert summary.trial_label_distribution["NEEDS_REVIEW"] == 2

    def test_split_sizes_and_disjointness(self):
        validator = ExtendedDatasetValidator(data_dir=Path("data"))
        summary = validator.validate_and_summarize()

        assert summary.split_sizes["train"] == 3
        assert summary.split_sizes["validation"] == 1
        assert summary.split_sizes["test"] == 2
        assert summary.split_sizes["stress_test"] == 4
        assert summary.patient_leakage_detected is False
