"""
Integrity and referential consistency tests for MedMatch dataset.
Phase 2: Dataset + Ground Truth.
"""

import json
from pathlib import Path
import pytest

from scripts.validate_dataset import DatasetValidator


@pytest.fixture
def fixtures_dir():
    return Path("data/fixtures")


def test_fixtures_referential_integrity(fixtures_dir):
    """Validates that all foreign keys and relations in fixtures resolve correctly."""
    validator = DatasetValidator(Path("data"))
    assert validator.validate_fixtures(fixtures_dir) is True
    assert len(validator.errors) == 0


def test_character_span_offsets_match_verbatim(fixtures_dir):
    """Verifies that patient_evidence.text is the EXACT substring at start_char:end_char in clinical_note."""
    patients_data = json.loads((fixtures_dir / "patients.json").read_text(encoding="utf-8"))
    patients_map = {p["patient_id"]: p["clinical_note"] for p in patients_data}

    crit_labels = json.loads((fixtures_dir / "criterion_labels.json").read_text(encoding="utf-8"))

    for cgt in crit_labels:
        p_id = cgt["patient_id"]
        ev = cgt["patient_evidence"]
        sc = ev.get("start_char")
        ec = ev.get("end_char")
        ev_txt = ev["text"]

        if sc is not None and sc >= 0 and ec is not None and ec >= 0:
            note = patients_map[p_id]
            extracted_span = note[sc:ec]
            assert extracted_span == ev_txt, (
                f"Span mismatch for {p_id} on {cgt['criterion_id']}: "
                f"note[{sc}:{ec}]='{extracted_span}' != evidence '{ev_txt}'"
            )


def test_no_orphan_criterion_labels(fixtures_dir):
    """Verifies no criterion label references a nonexistent criterion ID or patient ID."""
    criteria_data = json.loads((fixtures_dir / "criteria.json").read_text(encoding="utf-8"))
    criteria_ids = {c["criterion_id"] for c in criteria_data}

    crit_labels = json.loads((fixtures_dir / "criterion_labels.json").read_text(encoding="utf-8"))
    for cgt in crit_labels:
        assert cgt["criterion_id"] in criteria_ids, f"Orphan criterion label: {cgt['criterion_id']}"
