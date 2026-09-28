"""
Tests for Section Normalization and Segmentation.
Phase 3: Clinical Trial Document Intelligence.
"""

import pytest
from scripts.document_schema import SectionType
from scripts.section_normalizer import SectionNormalizer


class TestSectionNormalization:
    """Test suite for deterministic section header classification and text segmentation."""

    @pytest.mark.parametrize(
        "heading,expected_type,min_conf",
        [
            ("Inclusion Criteria", SectionType.INCLUSION_CRITERIA, 0.95),
            ("Subject Inclusion Criteria:", SectionType.INCLUSION_CRITERIA, 0.95),
            ("1. Key Inclusion Criteria", SectionType.INCLUSION_CRITERIA, 0.95),
            ("Exclusion Criteria", SectionType.EXCLUSION_CRITERIA, 0.95),
            ("Patient Exclusion Criteria -", SectionType.EXCLUSION_CRITERIA, 0.95),
            ("Eligibility Criteria", SectionType.ELIGIBILITY_CRITERIA, 0.90),
            ("Patient Eligibility", SectionType.ELIGIBILITY_CRITERIA, 0.90),
            ("Study Population", SectionType.STUDY_POPULATION, 0.90),
            ("Target Population", SectionType.STUDY_POPULATION, 0.90),
            ("Disease Characteristics", SectionType.DISEASE_CHARACTERISTICS, 0.90),
            ("Prior Therapy", SectionType.PRIOR_CONCURRENT_THERAPY, 0.90),
            ("Prohibited Medications", SectionType.PRIOR_CONCURRENT_THERAPY, 0.90),
            ("Patient Characteristics", SectionType.PATIENT_CHARACTERISTICS, 0.85),
        ],
    )
    def test_known_heading_classification(self, heading: str, expected_type: SectionType, min_conf: float):
        sec_type, conf = SectionNormalizer.classify_heading(heading)
        assert sec_type == expected_type
        assert conf >= min_conf

    @pytest.mark.parametrize(
        "heading",
        [
            ("Statistical Analysis Plan"),
            ("Schedule of Assessments"),
            ("Adverse Event Reporting Procedure"),
            ("Investigator Signatures"),
            (""),
            ("   "),
        ],
    )
    def test_unclassified_or_ambiguous_headings(self, heading: str):
        sec_type, conf = SectionNormalizer.classify_heading(heading)
        assert sec_type == SectionType.UNKNOWN_AMBIGUOUS
        assert conf == 0.0

    def test_segment_raw_eligibility_text(self):
        raw_narrative = (
            "Inclusion Criteria\n"
            "1. Age >= 18 years.\n"
            "2. Confirmed adenocarcinoma.\n"
            "\n"
            "Exclusion Criteria\n"
            "1. Active CNS metastases.\n"
            "2. Prior immunotherapy within 30 days.\n"
        )

        sections = SectionNormalizer.segment_raw_eligibility_text(raw_narrative)
        assert len(sections) == 2

        sec1 = sections[0]
        assert sec1["section_type"] == SectionType.INCLUSION_CRITERIA
        assert sec1["heading"] == "Inclusion Criteria"
        assert "Age >= 18 years." in sec1["text"]
        assert sec1["start_char"] == 0
        assert sec1["source_order"] == 1

        sec2 = sections[1]
        assert sec2["section_type"] == SectionType.EXCLUSION_CRITERIA
        assert sec2["heading"] == "Exclusion Criteria"
        assert "Active CNS metastases." in sec2["text"]
        assert sec2["start_char"] >= sec1["end_char"]
        assert sec2["source_order"] == 2

    def test_segment_empty_narrative(self):
        assert SectionNormalizer.segment_raw_eligibility_text("") == []
        assert SectionNormalizer.segment_raw_eligibility_text("   \n\n  ") == []
