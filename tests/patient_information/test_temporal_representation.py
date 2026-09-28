"""
Tests for Patient Temporal Information Representation.
Phase 4: Patient Clinical Information Extraction.
"""

import pytest
from pydantic import ValidationError

from scripts.patient_schema import (
    AssertionType,
    ClinicalFact,
    FactProvenance,
    PatientClinicalProfile,
    TemporalContext,
    TemporalityType,
)
from scripts.validate_patient_profile import PatientProfileValidator


class TestTemporalRepresentation:
    """Test suite for temporal contexts, relative intervals, event anchors, and durations."""

    def test_relative_temporal_interval_preservation(self):
        """Relative statements like '27 days ago' must preserve interval and signed offset."""
        temp = TemporalContext(
            temporality_type=TemporalityType.RELATIVE_INTERVAL,
            relative_interval="27 days ago",
            relative_days_offset=-27,
            anchor_event="chemotherapy_completion",
        )
        assert temp.temporality_type == TemporalityType.RELATIVE_INTERVAL
        assert temp.relative_interval == "27 days ago"
        assert temp.relative_days_offset == -27
        assert temp.anchor_event == "chemotherapy_completion"

    def test_date_specific_temporality(self):
        """Calendar date-specific clinical event."""
        temp = TemporalContext(
            temporality_type=TemporalityType.DATE_SPECIFIC,
            reference_date="2025-11-10",
            anchor_event="surgical_resection",
        )
        assert temp.reference_date == "2025-11-10"
        assert temp.anchor_event == "surgical_resection"

    def test_duration_temporality(self):
        """Ongoing duration in days."""
        temp = TemporalContext(
            temporality_type=TemporalityType.DURATION,
            duration_days=180,
            is_approximate=True,
        )
        assert temp.duration_days == 180
        assert temp.is_approximate is True

    def test_negative_duration_days_rejected(self):
        """Negative duration must be rejected by schema and validator."""
        with pytest.raises(ValidationError):
            TemporalContext(duration_days=-10)

    def test_current_vs_historical_distinct_classification(self):
        """Verify current medication vs historical completed medication."""
        prov = FactProvenance(
            note_id="NOTE_001",
            patient_id="PAT_001",
            source_text="Sample text",
            extraction_timestamp="2026-09-28T12:00:00Z",
        )
        f_current = ClinicalFact(
            fact_id="F_CURR",
            patient_id="PAT_001",
            concept="amlodipine",
            assertion=AssertionType.AFFIRMED,
            temporality=TemporalContext(temporality_type=TemporalityType.CURRENT),
            source_text="Sample text",
            provenance=prov,
        )
        f_hist = ClinicalFact(
            fact_id="F_HIST",
            patient_id="PAT_001",
            concept="carboplatin",
            assertion=AssertionType.HISTORICAL,
            temporality=TemporalContext(temporality_type=TemporalityType.HISTORICAL),
            source_text="Sample text",
            provenance=prov,
        )
        assert f_current.temporality.temporality_type == TemporalityType.CURRENT
        assert f_hist.temporality.temporality_type == TemporalityType.HISTORICAL
