"""
Tests for Document Extraction Validator.
Phase 3: Clinical Trial Document Intelligence.
"""

from pathlib import Path
import pytest

from scripts.document_schema import (
    AtomicConstraint,
    CriterionDomain,
    CriterionOperator,
    CriterionProvenance,
    CriterionType,
    SectionType,
    TrialCriterion,
    TrialDocument,
    TrialSection,
)
from scripts.validate_document_extraction import (
    DocumentExtractionValidator,
    validate_extraction_file,
)


class TestExtractionValidator:
    """Test suite for deterministic validation of extracted clinical trial documents."""

    def test_canonical_fixture_passes_cleanly(self):
        """The canonical development fixture must pass validation with 0 errors and 0 warnings."""
        fixture_path = Path("data/fixtures/phase3/trial_document_fixture.json")
        assert fixture_path.exists(), f"Fixture file not found: {fixture_path}"

        is_valid, issues = validate_extraction_file(fixture_path)
        errors = [i for i in issues if i.severity == "ERROR"]
        warnings = [i for i in issues if i.severity == "WARNING"]

        assert is_valid is True
        assert len(errors) == 0
        assert len(warnings) == 0

    def test_missing_trial_id_caught(self):
        """Validator must report error on empty or missing trial_id."""
        validator = DocumentExtractionValidator()
        doc_dict = {
            "document_id": "DOC_001",
            "trial_id": "",  # Empty!
            "source_uri": "protocol.pdf",
            "processing_timestamp": "2026-09-28T12:00:00Z",
            "document_hash": "a" * 64,
            "sections": [],
        }
        is_valid, issues = validator.validate_document(doc_dict)
        assert is_valid is False
        assert any(i.code == "MISSING_TRIAL_ID" for i in validator.errors)

    def test_duplicate_criterion_id_caught(self):
        """Validator must flag error if two criteria share the same criterion_id."""
        crit1 = TrialCriterion(
            criterion_id="DUPLICATE_ID",
            trial_id="NCT02484404",
            section_id="SEC_001",
            criterion_type=CriterionType.INCLUSION,
            raw_text="Criterion text 1",
            normalized_text="Criterion text 1",
            provenance=CriterionProvenance(
                document_id="DOC_001",
                trial_id="NCT02484404",
                section_id="SEC_001",
                source_text="Criterion text 1",
            ),
        )
        crit2 = TrialCriterion(
            criterion_id="DUPLICATE_ID",  # Duplicate!
            trial_id="NCT02484404",
            section_id="SEC_001",
            criterion_type=CriterionType.INCLUSION,
            raw_text="Criterion text 2",
            normalized_text="Criterion text 2",
            provenance=CriterionProvenance(
                document_id="DOC_001",
                trial_id="NCT02484404",
                section_id="SEC_001",
                source_text="Criterion text 2",
            ),
        )
        sec = TrialSection(
            section_id="SEC_001",
            section_type=SectionType.INCLUSION_CRITERIA,
            heading="Inclusion",
            text="Criterion text 1\nCriterion text 2",
            source_order=1,
            criteria=[crit1, crit2],
        )
        doc = TrialDocument(
            document_id="DOC_001",
            trial_id="NCT02484404",
            source_uri="protocol.pdf",
            processing_timestamp="2026-09-28T12:00:00Z",
            document_hash="a" * 64,
            sections=[sec],
        )

        validator = DocumentExtractionValidator()
        is_valid, issues = validator.validate_document(doc)
        assert is_valid is False
        assert any(i.code == "DUPLICATE_CRITERION_ID" for i in validator.errors)

    def test_duplicate_section_id_caught(self):
        """Validator must flag error if two sections share the same section_id."""
        sec1 = TrialSection(
            section_id="SEC_DUP",
            section_type=SectionType.INCLUSION_CRITERIA,
            heading="Inclusion",
            text="Text A",
            source_order=1,
            criteria=[],
        )
        sec2 = TrialSection(
            section_id="SEC_DUP",  # Duplicate!
            section_type=SectionType.EXCLUSION_CRITERIA,
            heading="Exclusion",
            text="Text B",
            source_order=2,
            criteria=[],
        )
        doc = TrialDocument(
            document_id="DOC_001",
            trial_id="NCT02484404",
            source_uri="protocol.pdf",
            processing_timestamp="2026-09-28T12:00:00Z",
            document_hash="b" * 64,
            sections=[sec1, sec2],
        )

        validator = DocumentExtractionValidator()
        is_valid, issues = validator.validate_document(doc)
        assert is_valid is False
        assert any(i.code == "DUPLICATE_SECTION_ID" for i in validator.errors)

    def test_missing_decomposition_block_reason_caught(self):
        """If can_decompose is False, missing reason must be flagged as error."""
        crit = TrialCriterion(
            criterion_id="CRIT_NO_REASON",
            trial_id="NCT02484404",
            section_id="SEC_001",
            criterion_type=CriterionType.INCLUSION,
            raw_text="Complex conditional criterion",
            normalized_text="Complex conditional criterion",
            is_atomic=False,
            can_decompose=False,
            decomposition_block_reason=None,  # Missing!
            provenance=CriterionProvenance(
                document_id="DOC_001",
                trial_id="NCT02484404",
                section_id="SEC_001",
                source_text="Complex conditional criterion",
            ),
        )
        sec = TrialSection(
            section_id="SEC_001",
            section_type=SectionType.INCLUSION_CRITERIA,
            heading="Inclusion",
            text="Complex conditional criterion",
            source_order=1,
            criteria=[crit],
        )
        doc = TrialDocument(
            document_id="DOC_001",
            trial_id="NCT02484404",
            source_uri="protocol.pdf",
            processing_timestamp="2026-09-28T12:00:00Z",
            document_hash="c" * 64,
            sections=[sec],
        )

        validator = DocumentExtractionValidator()
        is_valid, issues = validator.validate_document(doc)
        assert is_valid is False
        assert any(i.code == "MISSING_DECOMPOSITION_BLOCK_REASON" for i in validator.errors)

    def test_invalid_character_offsets_range(self):
        """Validator must report error if start_char > end_char."""
        crit = TrialCriterion(
            criterion_id="CRIT_OFFSET_RANGE",
            trial_id="NCT02484404",
            section_id="SEC_001",
            criterion_type=CriterionType.INCLUSION,
            raw_text="Sample text",
            normalized_text="Sample text",
            provenance=CriterionProvenance(
                document_id="DOC_001",
                trial_id="NCT02484404",
                section_id="SEC_001",
                start_char=50,
                end_char=20,  # Invalid: start > end!
                source_text="Sample text",
            ),
        )
        sec = TrialSection(
            section_id="SEC_001",
            section_type=SectionType.INCLUSION_CRITERIA,
            heading="Inclusion",
            text="Sample text 01234567890123456789012345678901234567890123456789",
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
        assert is_valid is False
        assert any(i.code == "INVALID_CHARACTER_OFFSET_RANGE" for i in validator.errors)

    def test_inconsistent_section_and_criterion_type_warning(self):
        """Exclusion criterion placed in Inclusion section should produce a warning."""
        crit = TrialCriterion(
            criterion_id="CRIT_INCONSISTENT",
            trial_id="NCT02484404",
            section_id="SEC_001",
            criterion_type=CriterionType.EXCLUSION,  # Marked exclusion
            raw_text="No active infection",
            normalized_text="No active infection",
            provenance=CriterionProvenance(
                document_id="DOC_001",
                trial_id="NCT02484404",
                section_id="SEC_001",
                source_text="No active infection",
            ),
        )
        sec = TrialSection(
            section_id="SEC_001",
            section_type=SectionType.INCLUSION_CRITERIA,  # Inside inclusion section!
            heading="Inclusion Criteria",
            text="No active infection",
            source_order=1,
            criteria=[crit],
        )
        doc = TrialDocument(
            document_id="DOC_001",
            trial_id="NCT02484404",
            source_uri="protocol.pdf",
            processing_timestamp="2026-09-28T12:00:00Z",
            document_hash="e" * 64,
            sections=[sec],
        )

        validator = DocumentExtractionValidator()
        is_valid, issues = validator.validate_document(doc)
        # Warning, not error
        assert is_valid is True
        assert any(i.code == "INCONSISTENT_SECTION_CRITERION_TYPE" for i in validator.warnings)

    def test_deterministic_validation(self):
        """Repeated validations of identical object must return identical issues."""
        fixture_path = Path("data/fixtures/phase3/trial_document_fixture.json")
        res1, issues1 = validate_extraction_file(fixture_path)
        res2, issues2 = validate_extraction_file(fixture_path)

        assert res1 == res2
        assert [i.to_dict() for i in issues1] == [i.to_dict() for i in issues2]
