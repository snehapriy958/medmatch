"""
Tests for Provenance Tracking and Evidence Attribution.
Phase 3: Clinical Trial Document Intelligence.
"""

import pytest
from pydantic import ValidationError

from scripts.document_schema import (
    CriterionProvenance,
    CriterionType,
    SectionType,
    TrialCriterion,
    TrialDocument,
    TrialSection,
)
from scripts.validate_document_extraction import DocumentExtractionValidator


class TestProvenancePreservation:
    """Test suite for document provenance, character offsets, and cross-page attribution."""

    def test_exact_character_offsets_match_section_text(self):
        """Verifies that start_char and end_char accurately slice the section text."""
        section_text = (
            "1. Patient must be aged >= 18 years.\n"
            "2. ECOG performance status <= 1.\n"
            "3. Adequate bone marrow function."
        )
        c2_text = "2. ECOG performance status <= 1."
        start = section_text.find(c2_text)
        end = start + len(c2_text)

        prov = CriterionProvenance(
            document_id="DOC_001",
            trial_id="NCT02484404",
            section_id="SEC_001",
            page_number=1,
            start_char=start,
            end_char=end,
            source_text=c2_text,
        )

        assert section_text[prov.start_char:prov.end_char] == c2_text

    def test_unlocatable_offsets_marker(self):
        """When character offsets cannot be computed, -1 is preserved without crash or hallucination."""
        prov = CriterionProvenance(
            document_id="DOC_001",
            trial_id="NCT02484404",
            section_id="SEC_001",
            page_number=3,
            start_char=-1,
            end_char=-1,
            source_text="Legacy criterion from OCR with lost coordinates.",
        )
        assert prov.start_char == -1
        assert prov.end_char == -1

    def test_multi_page_provenance(self):
        """Document can have sections and criteria distributed across multiple pages."""
        crit_p1 = TrialCriterion(
            criterion_id="CRIT_P1",
            trial_id="NCT02484404",
            section_id="SEC_001",
            criterion_type=CriterionType.INCLUSION,
            raw_text="Age >= 18 on page 1",
            normalized_text="Age >= 18 on page 1",
            provenance=CriterionProvenance(
                document_id="DOC_001",
                trial_id="NCT02484404",
                section_id="SEC_001",
                page_number=1,
                source_text="Age >= 18 on page 1",
            ),
        )
        crit_p2 = TrialCriterion(
            criterion_id="CRIT_P2",
            trial_id="NCT02484404",
            section_id="SEC_001",
            criterion_type=CriterionType.INCLUSION,
            raw_text="Adequate renal function on page 2",
            normalized_text="Adequate renal function on page 2",
            provenance=CriterionProvenance(
                document_id="DOC_001",
                trial_id="NCT02484404",
                section_id="SEC_001",
                page_number=2,
                source_text="Adequate renal function on page 2",
            ),
        )
        sec = TrialSection(
            section_id="SEC_001",
            section_type=SectionType.INCLUSION_CRITERIA,
            heading="Inclusion Criteria",
            text="Age >= 18 on page 1\nAdequate renal function on page 2",
            page_start=1,
            page_end=2,
            source_order=1,
            criteria=[crit_p1, crit_p2],
        )

        assert sec.page_start == 1
        assert sec.page_end == 2
        assert sec.criteria[0].provenance.page_number == 1
        assert sec.criteria[1].provenance.page_number == 2

    def test_validator_warns_on_offset_text_mismatch(self):
        """Validator should flag a warning if character offsets point to different text in section."""
        sec_text = "Line A: Histology confirmed.\nLine B: Other info."
        crit = TrialCriterion(
            criterion_id="CRIT_OFFSET_MISMATCH",
            trial_id="NCT02484404",
            section_id="SEC_001",
            criterion_type=CriterionType.INCLUSION,
            raw_text="Histology confirmed.",
            normalized_text="Histology confirmed",
            provenance=CriterionProvenance(
                document_id="DOC_001",
                trial_id="NCT02484404",
                section_id="SEC_001",
                page_number=1,
                start_char=29,  # Points to "Line B: Other info."
                end_char=48,
                source_text="Histology confirmed.",  # Disagrees with slice!
            ),
        )
        sec = TrialSection(
            section_id="SEC_001",
            section_type=SectionType.INCLUSION_CRITERIA,
            heading="Inclusion",
            text=sec_text,
            source_order=1,
            criteria=[crit],
        )
        doc = TrialDocument(
            document_id="DOC_001",
            trial_id="NCT02484404",
            source_uri="protocol.pdf",
            processing_timestamp="2026-09-28T12:00:00Z",
            document_hash="d" * 64,
            sections=[sec],
        )

        validator = DocumentExtractionValidator()
        is_valid, issues = validator.validate_document(doc)
        # Warning, not hard error (allows slight whitespace normalization differences)
        assert is_valid is True
        assert any(i.code == "OFFSET_TEXT_MISMATCH" for i in validator.warnings)
