"""
Tests for Canonical Clinical Trial Document Schemas.
Phase 3: Clinical Trial Document Intelligence.
"""

import json
from pathlib import Path
import pytest
from pydantic import ValidationError

from scripts.document_schema import (
    AtomicConstraint,
    CriterionDomain,
    CriterionOperator,
    CriterionProvenance,
    CriterionType,
    DocumentExtractionContract,
    LogicalRelation,
    SectionType,
    TrialCriterion,
    TrialDocument,
    TrialSection,
)


def _make_valid_criterion(
    criterion_id: str = "CRIT_001",
    trial_id: str = "NCT02484404",
    section_id: str = "SEC_001",
    doc_id: str = "DOC_001",
    criterion_type: CriterionType = CriterionType.INCLUSION,
) -> TrialCriterion:
    return TrialCriterion(
        criterion_id=criterion_id,
        trial_id=trial_id,
        section_id=section_id,
        criterion_type=criterion_type,
        domain=CriterionDomain.DIAGNOSIS_STAGE,
        raw_text="Confirmed Stage IV non-small cell lung cancer.",
        normalized_text="Confirmed Stage IV non-small cell lung cancer",
        is_atomic=True,
        can_decompose=True,
        atomic_constraints=[
            AtomicConstraint(
                concept="nsclc",
                operator=CriterionOperator.EQ,
                value="Stage IV",
            )
        ],
        provenance=CriterionProvenance(
            document_id=doc_id,
            trial_id=trial_id,
            section_id=section_id,
            page_number=1,
            start_char=0,
            end_char=46,
            source_text="Confirmed Stage IV non-small cell lung cancer.",
        ),
    )


class TestDocumentSchema:
    """Test suite for canonical document, section, and criterion schema models."""

    def test_trial_criterion_valid_instantiation(self):
        crit = _make_valid_criterion()
        assert crit.criterion_id == "CRIT_001"
        assert crit.trial_id == "NCT02484404"
        assert crit.is_atomic is True
        assert len(crit.atomic_constraints) == 1
        assert crit.atomic_constraints[0].operator == CriterionOperator.EQ

    def test_trial_criterion_provenance_id_mismatch(self):
        """Criterion trial_id must match provenance trial_id."""
        with pytest.raises(ValidationError) as exc_info:
            TrialCriterion(
                criterion_id="CRIT_001",
                trial_id="NCT02484404",
                section_id="SEC_001",
                criterion_type=CriterionType.INCLUSION,
                raw_text="Age >= 18",
                normalized_text="Age >= 18",
                provenance=CriterionProvenance(
                    document_id="DOC_001",
                    trial_id="NCT99999999",  # Mismatch!
                    section_id="SEC_001",
                    source_text="Age >= 18",
                ),
            )
        assert "Provenance trial_id" in str(exc_info.value)

    def test_trial_criterion_provenance_section_mismatch(self):
        """Criterion section_id must match provenance section_id."""
        with pytest.raises(ValidationError) as exc_info:
            TrialCriterion(
                criterion_id="CRIT_001",
                trial_id="NCT02484404",
                section_id="SEC_001",
                criterion_type=CriterionType.INCLUSION,
                raw_text="Age >= 18",
                normalized_text="Age >= 18",
                provenance=CriterionProvenance(
                    document_id="DOC_001",
                    trial_id="NCT02484404",
                    section_id="SEC_999",  # Mismatch!
                    source_text="Age >= 18",
                ),
            )
        assert "Provenance section_id" in str(exc_info.value)

    def test_trial_section_page_range_validation(self):
        """Section page_start cannot exceed page_end."""
        with pytest.raises(ValidationError) as exc_info:
            TrialSection(
                section_id="SEC_001",
                section_type=SectionType.INCLUSION_CRITERIA,
                heading="Inclusion",
                text="Some text",
                page_start=5,
                page_end=2,  # Invalid: start > end
                source_order=1,
            )
        assert "page_start (5) cannot exceed page_end (2)" in str(exc_info.value)

    def test_trial_document_hierarchy_validation(self):
        """Document must enforce trial_id and document_id consistency across sections and criteria."""
        crit = _make_valid_criterion(trial_id="NCT02484404", doc_id="DOC_001")
        sec = TrialSection(
            section_id="SEC_001",
            section_type=SectionType.INCLUSION_CRITERIA,
            heading="Inclusion Criteria",
            text="Confirmed Stage IV non-small cell lung cancer.",
            page_start=1,
            page_end=1,
            source_order=1,
            criteria=[crit],
        )

        # Mismatched document_id in document vs criterion provenance
        with pytest.raises(ValidationError) as exc_info:
            TrialDocument(
                document_id="DOC_DIFFERENT",  # Mismatch!
                trial_id="NCT02484404",
                source_uri="protocol.pdf",
                processing_timestamp="2026-09-28T12:00:00Z",
                document_hash="a" * 64,
                sections=[sec],
            )
        assert "provenance document_id" in str(exc_info.value)

    def test_document_json_roundtrip(self):
        """Document should serialize to JSON and deserialize back losslessly."""
        crit = _make_valid_criterion()
        sec = TrialSection(
            section_id="SEC_001",
            section_type=SectionType.INCLUSION_CRITERIA,
            heading="Inclusion Criteria",
            text="Confirmed Stage IV non-small cell lung cancer.",
            page_start=1,
            page_end=1,
            source_order=1,
            criteria=[crit],
        )
        doc = TrialDocument(
            document_id="DOC_001",
            trial_id="NCT02484404",
            source_uri="protocol.pdf",
            processing_timestamp="2026-09-28T12:00:00Z",
            document_hash="b" * 64,
            sections=[sec],
        )

        doc_json = doc.model_dump_json()
        doc_parsed = TrialDocument.model_validate_json(doc_json)

        assert doc_parsed.document_id == doc.document_id
        assert doc_parsed.sections[0].criteria[0].criterion_id == crit.criterion_id
        assert doc_parsed.sections[0].criteria[0].atomic_constraints[0].value == "Stage IV"

    def test_document_extraction_contract(self):
        """Contract must wrap TrialDocument and compute extraction summary counts."""
        crit = _make_valid_criterion()
        sec = TrialSection(
            section_id="SEC_001",
            section_type=SectionType.INCLUSION_CRITERIA,
            heading="Inclusion Criteria",
            text="Confirmed Stage IV non-small cell lung cancer.",
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
        contract = DocumentExtractionContract(
            status="SUCCESS",
            document=doc,
            total_sections=1,
            total_criteria=1,
            inclusion_count=1,
            exclusion_count=0,
            ambiguous_count=0,
            atomic_count=1,
            compound_count=0,
            validation_passed=True,
        )
        assert contract.status == "SUCCESS"
        assert contract.total_criteria == 1
        assert contract.inclusion_count == 1
