"""
Tests for Patient Information Provenance and Character Offset Attribution.
Phase 4: Patient Clinical Information Extraction.
"""

import pytest
from pydantic import ValidationError

from scripts.patient_schema import FactProvenance


class TestPatientProvenance:
    """Test suite for evidence attribution, character offsets, and provenance rules."""

    def test_exact_character_offsets_match_note_slice(self):
        """Character offsets must accurately slice the source note text."""
        raw_note = (
            "Assessment: 63-year-old male with Stage IV adenocarcinoma.\n"
            "EGFR exon 19 deletion detected on tissue NGS."
        )
        target = "EGFR exon 19 deletion detected"
        start = raw_note.find(target)
        end = start + len(target)

        prov = FactProvenance(
            note_id="NOTE_001",
            patient_id="PAT_001",
            source_text=target,
            start_char=start,
            end_char=end,
            extraction_timestamp="2026-09-28T12:00:00Z",
        )

        assert raw_note[prov.start_char:prov.end_char] == target

    def test_unlocatable_offsets_marker(self):
        """When character offsets cannot be computed, -1 is preserved without error."""
        prov = FactProvenance(
            note_id="NOTE_001",
            patient_id="PAT_001",
            source_text="Legacy EHR note with unmapped character coordinates.",
            start_char=-1,
            end_char=-1,
            extraction_timestamp="2026-09-28T12:00:00Z",
        )
        assert prov.start_char == -1
        assert prov.end_char == -1

    def test_inverted_offsets_raise_error(self):
        """start_char > end_char must raise ValidationError."""
        with pytest.raises(ValidationError):
            FactProvenance(
                note_id="NOTE_001",
                patient_id="PAT_001",
                source_text="Sample text",
                start_char=50,
                end_char=20,  # Invalid: start > end!
                extraction_timestamp="2026-09-28T12:00:00Z",
            )

    def test_negative_offsets_other_than_minus_one_rejected(self):
        """Negative offsets like -2 or -5 must be rejected."""
        with pytest.raises(ValidationError):
            FactProvenance(
                note_id="NOTE_001",
                patient_id="PAT_001",
                source_text="Sample text",
                start_char=-5,
                end_char=10,
                extraction_timestamp="2026-09-28T12:00:00Z",
            )
