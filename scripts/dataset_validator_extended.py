"""
MedMatch Extended Dataset Validator.
Phase 11: Evaluation & Ablation.

Performs exhaustive, deterministic dataset validation and exports machine-readable summaries.
Checks:
1. Referential and foreign key integrity across trials, patients, criteria, and labels
2. Exact character span offset integrity against patient clinical notes
3. Deterministic clinical aggregation consistency
4. Zero-patient leakage across train, validation, and test splits
5. Missingness semantics (UNKNOWN due to missing data)
6. Detailed label distributions and summary metrics
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

try:
    from scripts.dataset_schema import (
        CanonicalCriterion,
        CanonicalPatient,
        CanonicalTrial,
        CriterionGroundTruth,
        TrialGroundTruth,
        compute_trial_eligibility,
    )
    from scripts.evaluation_schema import DatasetValidationSummary
except ImportError:
    from dataset_schema import (
        CanonicalCriterion,
        CanonicalPatient,
        CanonicalTrial,
        CriterionGroundTruth,
        TrialGroundTruth,
        compute_trial_eligibility,
    )
    from evaluation_schema import DatasetValidationSummary


class ExtendedDatasetValidator:
    """
    Exhaustive deterministic validator for MedMatch datasets.
    """

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_and_summarize(self) -> DatasetValidationSummary:
        fixtures_dir = self.data_dir / "fixtures"
        splits_dir = self.data_dir / "splits"
        manifest_path = self.data_dir / "manifests" / "dataset_manifest.json"

        # Load Manifest
        manifest_data = {}
        if manifest_path.exists():
            manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))

        dataset_name = manifest_data.get("dataset_name", "MedMatch Fixture Dataset")
        version = manifest_data.get("dataset_version", "0.1.0-fixture")
        classification = manifest_data.get(
            "dataset_classification", "DEVELOPMENT/TEST FIXTURE ONLY"
        )

        # 1. Trials
        trials_file = fixtures_dir / "trials.json"
        trials_data = json.loads(trials_file.read_text(encoding="utf-8"))
        trials: Dict[str, CanonicalTrial] = {}
        duplicates = 0
        invalid_records = 0

        for idx, item in enumerate(trials_data):
            try:
                trial = CanonicalTrial.model_validate(item)
                if trial.trial_id in trials:
                    duplicates += 1
                    self.errors.append(f"Duplicate trial_id: {trial.trial_id}")
                trials[trial.trial_id] = trial
            except Exception as e:
                invalid_records += 1
                self.errors.append(f"Invalid trial at {idx}: {e}")

        # 2. Criteria
        criteria_file = fixtures_dir / "criteria.json"
        criteria_data = json.loads(criteria_file.read_text(encoding="utf-8"))
        criteria: Dict[str, CanonicalCriterion] = {}
        for idx, item in enumerate(criteria_data):
            try:
                crit = CanonicalCriterion.model_validate(item)
                if crit.criterion_id in criteria:
                    duplicates += 1
                    self.errors.append(f"Duplicate criterion_id: {crit.criterion_id}")
                if crit.trial_id not in trials:
                    self.errors.append(f"Criterion references unknown trial: {crit.trial_id}")
                criteria[crit.criterion_id] = crit
            except Exception as e:
                invalid_records += 1
                self.errors.append(f"Invalid criterion at {idx}: {e}")

        # 3. Patients
        patients_file = fixtures_dir / "patients.json"
        patients_data = json.loads(patients_file.read_text(encoding="utf-8"))
        patients: Dict[str, CanonicalPatient] = {}
        for idx, item in enumerate(patients_data):
            try:
                pat = CanonicalPatient.model_validate(item)
                if pat.patient_id in patients:
                    duplicates += 1
                    self.errors.append(f"Duplicate patient_id: {pat.patient_id}")
                patients[pat.patient_id] = pat
            except Exception as e:
                invalid_records += 1
                self.errors.append(f"Invalid patient at {idx}: {e}")

        # 4. Criterion Labels
        crit_labels_file = fixtures_dir / "criterion_labels.json"
        crit_labels_data = json.loads(crit_labels_file.read_text(encoding="utf-8"))
        crit_label_dist: Dict[str, int] = {}
        unknown_dist: Dict[str, int] = {"MISSING_EVIDENCE": 0, "UNCERTAIN_EVIDENCE": 0, "OTHER": 0}
        patient_trial_criterion_map: Dict[Tuple[str, str], List[CriterionGroundTruth]] = {}
        crit_keys: Set[str] = set()

        for idx, item in enumerate(crit_labels_data):
            try:
                cgt = CriterionGroundTruth.model_validate(item)
                key = f"{cgt.patient_id}::{cgt.trial_id}::{cgt.criterion_id}"
                if key in crit_keys:
                    duplicates += 1
                    self.errors.append(f"Duplicate criterion label key: {key}")
                crit_keys.add(key)

                verdict_str = cgt.ground_truth.value
                crit_label_dist[verdict_str] = crit_label_dist.get(verdict_str, 0) + 1

                if verdict_str == "UNKNOWN":
                    if cgt.patient_evidence and (
                        "not" in cgt.patient_evidence.text.lower()
                        or "missing" in cgt.patient_evidence.text.lower()
                    ):
                        unknown_dist["MISSING_EVIDENCE"] += 1
                    else:
                        unknown_dist["UNCERTAIN_EVIDENCE"] += 1

                # Provenance offset check
                if cgt.patient_id in patients and cgt.patient_evidence.start_char is not None:
                    sc = cgt.patient_evidence.start_char
                    ec = cgt.patient_evidence.end_char
                    txt = cgt.patient_evidence.text
                    note = patients[cgt.patient_id].clinical_note
                    if sc >= 0 and ec >= 0:
                        span = note[sc:ec]
                        if span != txt:
                            self.errors.append(
                                f"Character span mismatch for {key}: note[{sc}:{ec}]='{span}' != '{txt}'"
                            )

                pt_key = (cgt.patient_id, cgt.trial_id)
                patient_trial_criterion_map.setdefault(pt_key, []).append(cgt)
            except Exception as e:
                invalid_records += 1
                self.errors.append(f"Invalid criterion label at {idx}: {e}")

        # 5. Trial Labels
        trial_labels_file = fixtures_dir / "trial_labels.json"
        trial_labels_data = json.loads(trial_labels_file.read_text(encoding="utf-8"))
        trial_label_dist: Dict[str, int] = {}
        trial_keys: Set[str] = set()

        for idx, item in enumerate(trial_labels_data):
            try:
                tgt = TrialGroundTruth.model_validate(item)
                pt_key = (tgt.patient_id, tgt.trial_id)
                key_str = f"{tgt.patient_id}::{tgt.trial_id}"
                if key_str in trial_keys:
                    duplicates += 1
                    self.errors.append(f"Duplicate trial label: {key_str}")
                trial_keys.add(key_str)

                t_verdict = tgt.eligibility.value
                trial_label_dist[t_verdict] = trial_label_dist.get(t_verdict, 0) + 1

                # Aggregation check
                if pt_key in patient_trial_criterion_map:
                    ev_crits = patient_trial_criterion_map[pt_key]
                    verdicts = [c.ground_truth for c in ev_crits]
                    expected_verdict = compute_trial_eligibility(verdicts)
                    if tgt.eligibility != expected_verdict:
                        self.errors.append(
                            f"Aggregation mismatch for {pt_key}: label is {tgt.eligibility} but criteria compute to {expected_verdict}"
                        )
                else:
                    self.errors.append(f"Trial label {pt_key} has no criterion evaluations")
            except Exception as e:
                invalid_records += 1
                self.errors.append(f"Invalid trial label at {idx}: {e}")

        # 6. Split Leakage & Sizes
        split_sizes: Dict[str, int] = {}
        leakage_detected = False
        patient_sets: Dict[str, Set[str]] = {}

        for split_name in ["train", "validation", "test"]:
            s_file = splits_dir / f"{split_name}.jsonl"
            if s_file.exists():
                pids = set()
                for line in s_file.read_text(encoding="utf-8").splitlines():
                    if line.strip():
                        rec = json.loads(line)
                        pids.add(rec["patient_id"])
                split_sizes[split_name] = len(pids)
                patient_sets[split_name] = pids

        stress_file = splits_dir / "stress_test.jsonl"
        if stress_file.exists():
            stress_count = sum(
                1 for line in stress_file.read_text(encoding="utf-8").splitlines() if line.strip()
            )
            split_sizes["stress_test"] = stress_count

        # Check disjointness
        for s1, p1 in patient_sets.items():
            for s2, p2 in patient_sets.items():
                if s1 < s2:
                    overlap = p1.intersection(p2)
                    if overlap:
                        leakage_detected = True
                        self.errors.append(f"Patient leakage between {s1} and {s2}: {overlap}")

        is_valid = len(self.errors) == 0

        return DatasetValidationSummary(
            dataset_name=dataset_name,
            version=version,
            classification=classification,
            total_patients=len(patients),
            total_trials=len(trials),
            total_criteria=len(criteria),
            total_patient_trial_pairs=len(trial_keys),
            total_criterion_labels=len(crit_keys),
            criterion_label_distribution=crit_label_dist,
            trial_label_distribution=trial_label_dist,
            unknown_missing_distribution=unknown_dist,
            split_sizes=split_sizes,
            patient_leakage_detected=leakage_detected,
            duplicate_record_count=duplicates,
            invalid_record_count=invalid_records,
            is_valid=is_valid,
            validation_timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )
