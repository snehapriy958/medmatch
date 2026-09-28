"""
Fixture validation and controlled scenario verification tests.
Phase 2: Dataset + Ground Truth.
"""

import hashlib
import json
from pathlib import Path
import pytest


@pytest.fixture
def fixtures_dir():
    return Path("data/fixtures")


def test_controlled_scenarios_representation(fixtures_dir):
    """Verifies that all 6 controlled scenario types exist in fixtures with correct eligibility."""
    trial_labels = json.loads((fixtures_dir / "trial_labels.json").read_text(encoding="utf-8"))
    tl_map = {tl["patient_id"]: tl for tl in trial_labels}

    def get_summary(tl):
        cs = tl["criterion_summary"]
        return {
            "pass": cs.get("pass", cs.get("pass_count", 0)),
            "fail": cs.get("fail", cs.get("fail_count", 0)),
            "unknown": cs.get("unknown", cs.get("unknown_count", 0)),
        }

    # 1. Scenario A: Clearly Eligible
    assert "SYN_P001" in tl_map
    assert tl_map["SYN_P001"]["eligibility"] == "ELIGIBLE"
    s1 = get_summary(tl_map["SYN_P001"])
    assert s1["fail"] == 0
    assert s1["unknown"] == 0

    # 2. Scenario B: Clearly Ineligible (EGFR wild-type + ECOG 3)
    assert "SYN_P002" in tl_map
    assert tl_map["SYN_P002"]["eligibility"] == "INELIGIBLE"
    s2 = get_summary(tl_map["SYN_P002"])
    assert s2["fail"] >= 1

    # 3. Scenario C: Missing Information (EGFR pending + Brain MRI unrecorded)
    assert "SYN_P003" in tl_map
    assert tl_map["SYN_P003"]["eligibility"] == "NEEDS_REVIEW"
    s3 = get_summary(tl_map["SYN_P003"])
    assert s3["fail"] == 0
    assert s3["unknown"] >= 1

    # 4. Scenario D: Conflicting Information (Biopsy positive vs liquid biopsy negative)
    assert "SYN_P004" in tl_map
    assert tl_map["SYN_P004"]["eligibility"] == "NEEDS_REVIEW"
    s4 = get_summary(tl_map["SYN_P004"])
    assert s4["fail"] == 0
    assert s4["unknown"] >= 1

    # 5. Scenario E: Boundary Condition (Platelets 99 vs >= 100)
    assert "SYN_P005" in tl_map
    assert tl_map["SYN_P005"]["eligibility"] == "INELIGIBLE"
    s5 = get_summary(tl_map["SYN_P005"])
    assert s5["fail"] >= 1

    # 6. Scenario F: Temporal Condition (Washout 27 days vs >= 28 days required)
    assert "SYN_P006" in tl_map
    assert tl_map["SYN_P006"]["eligibility"] == "INELIGIBLE"
    s6 = get_summary(tl_map["SYN_P006"])
    assert s6["fail"] >= 1


def test_checksums_sha256_integrity():
    """Verifies that all files listed in checksums.sha256 match their actual disk hashes."""
    checksums_file = Path("data/manifests/checksums.sha256")
    assert checksums_file.exists()

    for line in checksums_file.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        expected_hash, rel_path = line.split(maxsplit=1)
        file_path = Path(rel_path)
        assert file_path.exists(), f"File in checksums does not exist: {file_path}"
        actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
        assert actual_hash == expected_hash, f"SHA-256 hash mismatch for {file_path}"
