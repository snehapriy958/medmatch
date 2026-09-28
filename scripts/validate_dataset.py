"""
MedMatch Dataset & Ground Truth Validator.
Phase 2: Dataset + Ground Truth.

Validates the integrity, schema conformance, deterministic clinical aggregation,
referential consistency, and split disjointness across MedMatch datasets.

Returns exit code 0 if all checks pass; non-zero if any validation failure occurs.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Set

# Ensure scripts directory is in python path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dataset_schema import (
    CanonicalCriterion,
    CanonicalPatient,
    CanonicalTrial,
    CriterionGroundTruth,
    CriterionVerdict,
    TrialEligibilityVerdict,
    TrialGroundTruth,
    compute_trial_eligibility,
)


class DatasetValidationError(Exception):
    """Raised when dataset integrity or schema validation fails."""
    pass


class DatasetValidator:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def log_error(self, message: str) -> None:
        self.errors.append(message)
        print(f"[ERROR] {message}", file=sys.stderr)

    def log_warning(self, message: str) -> None:
        self.warnings.append(message)
        print(f"[WARNING] {message}")

    def validate_fixtures(self, fixtures_dir: Path) -> bool:
        """Validates all canonical fixtures in data/fixtures/."""
        print(f"--> Validating fixtures in {fixtures_dir}...")

        trials_file = fixtures_dir / "trials.json"
        patients_file = fixtures_dir / "patients.json"
        criteria_file = fixtures_dir / "criteria.json"
        crit_labels_file = fixtures_dir / "criterion_labels.json"
        trial_labels_file = fixtures_dir / "trial_labels.json"

        required_files = [trials_file, patients_file, criteria_file, crit_labels_file, trial_labels_file]
        for f in required_files:
            if not f.exists():
                self.log_error(f"Missing required fixture file: {f}")
                return False

        # 1. Load and parse Trials
        trials_data = json.loads(trials_file.read_text(encoding="utf-8"))
        trials: Dict[str, CanonicalTrial] = {}
        for idx, item in enumerate(trials_data):
            try:
                trial = CanonicalTrial.model_validate(item)
                if trial.trial_id in trials:
                    self.log_error(f"Duplicate trial_id '{trial.trial_id}' at index {idx}")
                trials[trial.trial_id] = trial
            except Exception as e:
                self.log_error(f"Failed to validate trial at index {idx}: {e}")

        # 2. Load and parse Criteria
        criteria_data = json.loads(criteria_file.read_text(encoding="utf-8"))
        criteria: Dict[str, CanonicalCriterion] = {}
        for idx, item in enumerate(criteria_data):
            try:
                criterion = CanonicalCriterion.model_validate(item)
                if criterion.criterion_id in criteria:
                    self.log_error(f"Duplicate criterion_id '{criterion.criterion_id}' at index {idx}")
                if criterion.trial_id not in trials:
                    self.log_error(f"Criterion '{criterion.criterion_id}' references unknown trial '{criterion.trial_id}'")
                criteria[criterion.criterion_id] = criterion
            except Exception as e:
                self.log_error(f"Failed to validate criterion at index {idx}: {e}")

        # 3. Load and parse Patients
        patients_data = json.loads(patients_file.read_text(encoding="utf-8"))
        patients: Dict[str, CanonicalPatient] = {}
        for idx, item in enumerate(patients_data):
            try:
                patient = CanonicalPatient.model_validate(item)
                if patient.patient_id in patients:
                    self.log_error(f"Duplicate patient_id '{patient.patient_id}' at index {idx}")
                patients[patient.patient_id] = patient
            except Exception as e:
                self.log_error(f"Failed to validate patient at index {idx}: {e}")

        # 4. Load and parse Criterion Ground Truth
        crit_labels_data = json.loads(crit_labels_file.read_text(encoding="utf-8"))
        crit_labels: List[CriterionGroundTruth] = []
        crit_label_keys: Set[str] = set()
        patient_trial_criterion_map: Dict[Tuple[str, str], List[CriterionGroundTruth]] = {}

        for idx, item in enumerate(crit_labels_data):
            try:
                cgt = CriterionGroundTruth.model_validate(item)
                crit_labels.append(cgt)

                # Uniqueness of (patient, trial, criterion)
                key = f"{cgt.patient_id}::{cgt.trial_id}::{cgt.criterion_id}"
                if key in crit_label_keys:
                    self.log_error(f"Duplicate criterion label for key '{key}' at index {idx}")
                crit_label_keys.add(key)

                # Foreign key checks
                if cgt.patient_id not in patients:
                    self.log_error(f"Criterion label at index {idx} references unknown patient '{cgt.patient_id}'")
                if cgt.trial_id not in trials:
                    self.log_error(f"Criterion label at index {idx} references unknown trial '{cgt.trial_id}'")
                if cgt.criterion_id not in criteria:
                    self.log_error(f"Criterion label at index {idx} references unknown criterion '{cgt.criterion_id}'")

                # Verify character offset alignment if offsets provided
                if cgt.patient_id in patients and cgt.patient_evidence.start_char is not None:
                    sc = cgt.patient_evidence.start_char
                    ec = cgt.patient_evidence.end_char
                    ev_txt = cgt.patient_evidence.text
                    patient_note = patients[cgt.patient_id].clinical_note
                    if sc >= 0 and ec >= 0:
                        actual_span = patient_note[sc:ec]
                        if actual_span != ev_txt:
                            self.log_error(
                                f"Span mismatch for {key}: note[{sc}:{ec}]='{actual_span}' != evidence '{ev_txt}'"
                            )

                pt_key = (cgt.patient_id, cgt.trial_id)
                patient_trial_criterion_map.setdefault(pt_key, []).append(cgt)

            except Exception as e:
                self.log_error(f"Failed to validate criterion label at index {idx}: {e}")

        # 5. Load and parse Trial Ground Truth
        trial_labels_data = json.loads(trial_labels_file.read_text(encoding="utf-8"))
        trial_labels: Dict[Tuple[str, str], TrialGroundTruth] = {}

        for idx, item in enumerate(trial_labels_data):
            try:
                tgt = TrialGroundTruth.model_validate(item)
                pt_key = (tgt.patient_id, tgt.trial_id)
                if pt_key in trial_labels:
                    self.log_error(f"Duplicate trial label for patient-trial pair {pt_key} at index {idx}")
                trial_labels[pt_key] = tgt

                # Foreign key checks
                if tgt.patient_id not in patients:
                    self.log_error(f"Trial label at index {idx} references unknown patient '{tgt.patient_id}'")
                if tgt.trial_id not in trials:
                    self.log_error(f"Trial label at index {idx} references unknown trial '{tgt.trial_id}'")

                # 6. Check Deterministic Clinical Aggregation
                if pt_key in patient_trial_criterion_map:
                    evaluated_crits = patient_trial_criterion_map[pt_key]
                    verdicts = [cg.ground_truth for cg in evaluated_crits]
                    expected_eligibility = compute_trial_eligibility(verdicts)
                    if tgt.eligibility != expected_eligibility:
                        self.log_error(
                            f"Aggregation mismatch for {pt_key}: trial label is '{tgt.eligibility}' "
                            f"but criterion aggregation evaluates to '{expected_eligibility}'"
                        )
                else:
                    self.log_error(f"Trial label {pt_key} has no corresponding criterion labels")

            except Exception as e:
                self.log_error(f"Failed to validate trial label at index {idx}: {e}")

        return len(self.errors) == 0

    def validate_splits(self, splits_dir: Path) -> bool:
        """Validates that train, validation, and test splits have zero patient leakage."""
        print(f"--> Validating splits in {splits_dir}...")
        train_file = splits_dir / "train.jsonl"
        val_file = splits_dir / "validation.jsonl"
        test_file = splits_dir / "test.jsonl"

        if not (train_file.exists() and val_file.exists() and test_file.exists()):
            self.log_warning(f"Split files not found in {splits_dir}. Skipping split checks.")
            return True

        def read_patient_ids(path: Path) -> Set[str]:
            p_ids = set()
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    record = json.loads(line)
                    p_ids.add(record["patient_id"])
            return p_ids

        train_patients = read_patient_ids(train_file)
        val_patients = read_patient_ids(val_file)
        test_patients = read_patient_ids(test_file)

        # Leakage checks
        train_val_overlap = train_patients.intersection(val_patients)
        if train_val_overlap:
            self.log_error(f"Patient leakage between train and validation splits: {train_val_overlap}")

        train_test_overlap = train_patients.intersection(test_patients)
        if train_test_overlap:
            self.log_error(f"Patient leakage between train and test splits: {train_test_overlap}")

        val_test_overlap = val_patients.intersection(test_patients)
        if val_test_overlap:
            self.log_error(f"Patient leakage between validation and test splits: {val_test_overlap}")

        return len(self.errors) == 0

    def validate_manifest(self, manifest_file: Path) -> bool:
        """Validates that dataset manifest exists and has required metadata fields."""
        if not manifest_file.exists():
            self.log_error(f"Dataset manifest not found: {manifest_file}")
            return False

        try:
            data = json.loads(manifest_file.read_text(encoding="utf-8"))
            required_keys = ["dataset_name", "dataset_version", "created_at", "seed", "sources", "splits"]
            for k in required_keys:
                if k not in data:
                    self.log_error(f"Manifest missing required key '{k}'")
            return len(self.errors) == 0
        except Exception as e:
            self.log_error(f"Failed to parse manifest: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description="MedMatch Dataset Validator")
    parser.add_argument("--data-dir", type=Path, default=Path("data"), help="Path to data directory")
    parser.add_argument("--fixtures-only", action="store_true", help="Validate only fixtures")
    args = parser.parse_args()

    validator = DatasetValidator(args.data_dir)
    fixtures_dir = args.data_dir / "fixtures"

    fixtures_ok = validator.validate_fixtures(fixtures_dir)
    splits_ok = True
    manifest_ok = True

    if not args.fixtures_only:
        splits_ok = validator.validate_splits(args.data_dir / "splits")
        manifest_ok = validator.validate_manifest(args.data_dir / "manifests" / "dataset_manifest.json")

    total_errors = len(validator.errors)
    total_warnings = len(validator.warnings)

    print("\n" + "=" * 50)
    print(f"VALIDATION SUMMARY: {total_errors} errors, {total_warnings} warnings")
    print("=" * 50)

    if total_errors > 0:
        print("[FAIL] Dataset validation failed.", file=sys.stderr)
        sys.exit(1)
    else:
        print("[PASS] All dataset integrity and schema validations succeeded.")
        sys.exit(0)


if __name__ == "__main__":
    main()
