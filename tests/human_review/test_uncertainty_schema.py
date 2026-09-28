"""
Tests for Phase 9 Canonical Uncertainty Schema.
Verifies strongly-typed models, enums, conflict details, and validation constraints.
"""

import pytest
from pydantic import ValidationError

from scripts.uncertainty_schema import (
    ConflictEvidenceItem,
    UncertaintyProfile,
    UncertaintyRecord,
    UncertaintySeverity,
    UncertaintyStatus,
    UncertaintyType,
)


def test_uncertainty_status_and_type_enums():
    """Verify all required enum members exist."""
    assert UncertaintyStatus.RESOLVED.value == "RESOLVED"
    assert UncertaintyStatus.MISSING.value == "MISSING"
    assert UncertaintyStatus.CONFLICTING.value == "CONFLICTING"
    assert UncertaintyStatus.AMBIGUOUS.value == "AMBIGUOUS"
    assert UncertaintyStatus.STALE.value == "STALE"
    assert UncertaintyStatus.LOW_CONFIDENCE.value == "LOW_CONFIDENCE"
    assert UncertaintyStatus.INSUFFICIENT_EVIDENCE.value == "INSUFFICIENT_EVIDENCE"

    assert UncertaintyType.MISSING_PATIENT_FACT.value == "MISSING_PATIENT_FACT"
    assert UncertaintyType.CONFLICTING_PATIENT_FACTS.value == "CONFLICTING_PATIENT_FACTS"
    assert UncertaintyType.CONFLICTING_DOCUMENTS.value == "CONFLICTING_DOCUMENTS"
    assert UncertaintyType.TEMPORAL_AMBIGUITY.value == "TEMPORAL_AMBIGUITY"
    assert UncertaintyType.NUMERICAL_AMBIGUITY.value == "NUMERICAL_AMBIGUITY"
    assert UncertaintyType.UNSUPPORTED_INFERENCE.value == "UNSUPPORTED_INFERENCE"
    assert UncertaintyType.GROUNDING_CONTRADICTION.value == "GROUNDING_CONTRADICTION"
    assert UncertaintyType.INSUFFICIENT_RETRIEVAL.value == "INSUFFICIENT_RETRIEVAL"
    assert UncertaintyType.STALE_CLINICAL_DATA.value == "STALE_CLINICAL_DATA"


def test_valid_uncertainty_record():
    """Verify clean instantiation of an UncertaintyRecord."""
    record = UncertaintyRecord(
        uncertainty_id="UNC-001",
        subject="HER2_status",
        fact_or_criterion_ref="CRIT-01",
        status=UncertaintyStatus.MISSING,
        uncertainty_type=UncertaintyType.MISSING_PATIENT_FACT,
        description="HER2 status absent from records",
        evidence_references=[],
        affected_criterion="CRIT-01",
        severity=UncertaintySeverity.HIGH,
        review_required=True,
        machine_decision_allowed=False,
        reason="Required inclusion biomarker missing",
    )
    assert record.uncertainty_id == "UNC-001"
    assert record.status == UncertaintyStatus.MISSING
    assert record.review_required is True
    assert record.machine_decision_allowed is False


def test_high_severity_cannot_permit_machine_decision():
    """HIGH or CRITICAL unresolved uncertainty must reject machine_decision_allowed=True."""
    with pytest.raises(ValidationError, match="cannot permit machine_decision_allowed=True"):
        UncertaintyRecord(
            uncertainty_id="UNC-ERR-01",
            subject="biomarker",
            fact_or_criterion_ref="CRIT-01",
            status=UncertaintyStatus.MISSING,
            uncertainty_type=UncertaintyType.MISSING_PATIENT_FACT,
            description="Missing biomarker",
            severity=UncertaintySeverity.HIGH,
            review_required=True,
            machine_decision_allowed=True,  # VIOLATION
            reason="Violation of safety guardrail",
        )


def test_conflicting_uncertainty_requires_multiple_conflict_items():
    """CONFLICTING uncertainty must have at least 2 conflict items in conflict_details."""
    item1 = ConflictEvidenceItem(
        source_id="DOC-1",
        source_type="CLINICIAN_NOTE",
        asserted_value="positive",
        snippet="Patient is positive",
    )
    # Only 1 item provided -> should fail
    with pytest.raises(ValidationError, match="at least 2 conflicting evidence items"):
        UncertaintyRecord(
            uncertainty_id="UNC-ERR-02",
            subject="allergy",
            fact_or_criterion_ref="CRIT-01",
            status=UncertaintyStatus.CONFLICTING,
            uncertainty_type=UncertaintyType.CONFLICTING_PATIENT_FACTS,
            description="Conflicting allergy",
            severity=UncertaintySeverity.CRITICAL,
            review_required=True,
            machine_decision_allowed=False,
            reason="Conflict detected",
            conflict_details=[item1],
        )

    # 2 items provided -> should succeed
    item2 = ConflictEvidenceItem(
        source_id="DOC-2",
        source_type="PATIENT_INTAKE",
        asserted_value="negative",
        snippet="Patient denies allergy",
    )
    valid_rec = UncertaintyRecord(
        uncertainty_id="UNC-OK-02",
        subject="allergy",
        fact_or_criterion_ref="CRIT-01",
        status=UncertaintyStatus.CONFLICTING,
        uncertainty_type=UncertaintyType.CONFLICTING_PATIENT_FACTS,
        description="Conflicting allergy",
        severity=UncertaintySeverity.CRITICAL,
        review_required=True,
        machine_decision_allowed=False,
        reason="Conflict detected",
        conflict_details=[item1, item2],
    )
    assert len(valid_rec.conflict_details) == 2


def test_uncertainty_profile_summary_recomputation():
    """Verify that UncertaintyProfile automatically aggregates record counts."""
    r1 = UncertaintyRecord(
        uncertainty_id="U1",
        subject="s1",
        fact_or_criterion_ref="c1",
        status=UncertaintyStatus.MISSING,
        uncertainty_type=UncertaintyType.MISSING_PATIENT_FACT,
        description="d1",
        severity=UncertaintySeverity.MEDIUM,
        review_required=True,
        machine_decision_allowed=False,
        reason="r1",
    )
    r2 = UncertaintyRecord(
        uncertainty_id="U2",
        subject="s2",
        fact_or_criterion_ref="c2",
        status=UncertaintyStatus.CONFLICTING,
        uncertainty_type=UncertaintyType.CONFLICTING_PATIENT_FACTS,
        description="d2",
        severity=UncertaintySeverity.CRITICAL,
        review_required=True,
        machine_decision_allowed=False,
        reason="r2",
        conflict_details=[
            ConflictEvidenceItem(source_id="A", source_type="NOTE", asserted_value="V1"),
            ConflictEvidenceItem(source_id="B", source_type="NOTE", asserted_value="V2"),
        ],
    )
    r3 = UncertaintyRecord(
        uncertainty_id="U3",
        subject="s3",
        fact_or_criterion_ref="c3",
        status=UncertaintyStatus.RESOLVED,
        uncertainty_type=UncertaintyType.MISSING_PATIENT_FACT,
        description="d3",
        severity=UncertaintySeverity.LOW,
        review_required=False,
        machine_decision_allowed=True,
        reason="r3",
    )

    profile = UncertaintyProfile(
        case_id="CASE-100",
        trial_id="TRIAL-100",
        records=[r1, r2, r3],
    )

    assert profile.total_uncertainties == 3
    assert profile.unresolved_count == 2
    assert profile.critical_count == 1
    assert profile.review_required is True
