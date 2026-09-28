"""
Tests for Deterministic Claim Extractor.
Phase 8: Grounding Evaluation & Faithfulness Auditing.
"""

import pytest

from scripts.claim_extractor import DeterministicClaimExtractor
from scripts.grounding_schema import ClaimType


class TestDeterministicClaimExtractor:
    """Verifies deterministic proposition segmentation and taxonomic claim typing."""

    def setup_method(self):
        self.extractor = DeterministicClaimExtractor()

    def test_segment_reasoning_splits_compound_sentences(self):
        """Reasoning text is segmented into atomic proposition clauses."""
        text = "Patient has metastatic NSCLC. Trial requires age >= 18; patient age 62 meets requirement."
        segments = self.extractor.segment_reasoning(text)
        assert len(segments) >= 2
        assert any("metastatic NSCLC" in s for s in segments)
        assert any("age" in s.lower() for s in segments)

    def test_classify_patient_fact_claim(self):
        """Standard patient medical history / condition classified as PATIENT_FACT."""
        claim_type = self.extractor.classify_claim_type("Patient has confirmed stage IV adenocarcinoma")
        assert claim_type == ClaimType.PATIENT_FACT

    def test_classify_trial_criterion_claim(self):
        """Statements describing trial protocol rules classified as TRIAL_CRITERION."""
        claim_type = self.extractor.classify_claim_type("Trial requires documented EGFR T790M mutation")
        assert claim_type == ClaimType.TRIAL_CRITERION

    def test_classify_numerical_claim(self):
        """Statements containing lab values, cutoffs, or scores classified as NUMERICAL_VALUE."""
        c1 = self.extractor.classify_claim_type("Patient has ECOG performance status of 1")
        c2 = self.extractor.classify_claim_type("Serum creatinine cutoff is <= 1.5 mg/dL")
        c3 = self.extractor.classify_claim_type("Patient age is 62")
        assert c1 == ClaimType.NUMERICAL_VALUE
        assert c2 == ClaimType.NUMERICAL_VALUE
        assert c3 == ClaimType.NUMERICAL_VALUE

    def test_classify_temporal_claim(self):
        """Statements describing dates or durations classified as TEMPORAL_FACT."""
        c1 = self.extractor.classify_claim_type("Diagnosed in January 2024")
        c2 = self.extractor.classify_claim_type("Completed chemotherapy within the past 6 months")
        assert c1 == ClaimType.TEMPORAL_FACT
        assert c2 == ClaimType.TEMPORAL_FACT

    def test_classify_conclusion_claim(self):
        """Statements asserting satisfaction or failure classified as ELIGIBILITY_CONCLUSION."""
        c1 = self.extractor.classify_claim_type("Patient satisfies inclusion criterion c1")
        c2 = self.extractor.classify_claim_type("Patient fails exclusion criterion")
        assert c1 == ClaimType.ELIGIBILITY_CONCLUSION
        assert c2 == ClaimType.ELIGIBILITY_CONCLUSION

    def test_classify_inferred_claim(self):
        """Speculative or hedged claims classified as INFERRED_CLAIM."""
        c1 = self.extractor.classify_claim_type("Patient likely tolerates checkpoint inhibition")
        c2 = self.extractor.classify_claim_type("Presentation suggests underlying metastatic recurrence")
        assert c1 == ClaimType.INFERRED_CLAIM
        assert c2 == ClaimType.INFERRED_CLAIM

    def test_extract_claims_assigns_ids_and_preserves_determinism(self):
        """Repeated extraction on same reasoning text yields identical claim IDs and contents."""
        text = "Patient has stage IV NSCLC. Trial requires age >= 18. Patient age 62 meets requirement."
        claims1 = self.extractor.extract_claims(text, criterion_id="c1", trial_id="NCT001")
        claims2 = self.extractor.extract_claims(text, criterion_id="c1", trial_id="NCT001")

        assert len(claims1) == len(claims2)
        for cl1, cl2 in zip(claims1, claims2):
            assert cl1.claim_id == cl2.claim_id
            assert cl1.claim_text == cl2.claim_text
            assert cl1.claim_type == cl2.claim_type
            assert cl1.source_reference == cl2.source_reference
