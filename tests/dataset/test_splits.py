"""
Split integrity and leakage prevention tests for MedMatch dataset.
Phase 2: Dataset + Ground Truth.
"""

import json
from pathlib import Path
import pytest

from scripts.validate_dataset import DatasetValidator


@pytest.fixture
def splits_dir():
    return Path("data/splits")


def test_split_files_exist(splits_dir):
    assert (splits_dir / "train.jsonl").exists()
    assert (splits_dir / "validation.jsonl").exists()
    assert (splits_dir / "test.jsonl").exists()
    assert (splits_dir / "stress_test.jsonl").exists()


def test_zero_patient_leakage_across_splits(splits_dir):
    """Guarantees patient sets are strictly disjoint across train, validation, and test."""
    def load_patients(filename):
        p_ids = set()
        for line in (splits_dir / filename).read_text(encoding="utf-8").splitlines():
            if line.strip():
                record = json.loads(line)
                p_ids.add(record["patient_id"])
        return p_ids

    train_pts = load_patients("train.jsonl")
    val_pts = load_patients("validation.jsonl")
    test_pts = load_patients("test.jsonl")

    # Mutual disjointness
    assert len(train_pts) > 0
    assert len(val_pts) > 0
    assert len(test_pts) > 0

    assert train_pts.isdisjoint(val_pts), f"Leakage train/val: {train_pts.intersection(val_pts)}"
    assert train_pts.isdisjoint(test_pts), f"Leakage train/test: {train_pts.intersection(test_pts)}"
    assert val_pts.isdisjoint(test_pts), f"Leakage val/test: {val_pts.intersection(test_pts)}"


def test_validator_split_method(splits_dir):
    validator = DatasetValidator(Path("data"))
    assert validator.validate_splits(splits_dir) is True
    assert len(validator.errors) == 0


def test_split_and_stress_test_classification_labels(splits_dir):
    """Verifies that development splits and stress test subset are explicitly labeled."""
    for split_name in ["train.jsonl", "validation.jsonl", "test.jsonl"]:
        for line in (splits_dir / split_name).read_text(encoding="utf-8").splitlines():
            if line.strip():
                record = json.loads(line)
                assert record.get("dataset_layer") == "development_fixture"
                assert "TEST FIXTURE ONLY" in record.get("benchmark_classification", "")

    stress_cases = []
    for line in (splits_dir / "stress_test.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            record = json.loads(line)
            assert record.get("dataset_layer") == "stress_test"
            assert "SYNTHETIC STRESS TEST" in record.get("benchmark_classification", "")
            stress_cases.append(record["stress_category"])

    expected_categories = {"missing_information", "conflicting_evidence", "boundary_condition", "temporal_washout"}
    assert set(stress_cases) == expected_categories
