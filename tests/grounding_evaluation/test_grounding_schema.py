"""
Tests for Canonical Grounding and Faithfulness Schemas.
Phase 8: Grounding Evaluation & Faithfulness Auditing.
"""

import pytest
from pydantic import ValidationError

from scripts.grounding_schema import (
    CitationValidationRecord,
    ClaimType,
    ContradictionStatus,
    EvidenceSourceType,
    GroundingClaim,
    GroundingEvaluation,
    GroundingEvidence,
    HallucinationCategory,
    SupportStatus,
)


class TestGroundingSchema:
    """Verifies schema constraints, type safety, and validation invariants."""

    def test_support_status_enums(self):
        """All required 5 support status enum values must exist."""
        expected = {
            "SUPPORTED",
            "PARTIALLY_SUPPORTED",
            "UNSUPPORTED",
            "CONTRADICTED",
            "INSUFFICIENT_EVIDENCE",
        }
        actual = {s.value for s in SupportStatus}
        assert actual == expected

    def test_claim_type_enums(self):
        """All 6 claim types must exist."""
        expected = {
            "PATIENT_FACT",
            "TRIAL_CRITERION",
            "TEMPORAL_FACT",
            "NUMERICAL_VALUE",
            "ELIGIBILITY_CONCLUSION",
            "INFERRED_CLAIM",
        }
        actual = {c.value for c in ClaimType}
        assert actual == expected

    def test_hallucination_category_enums(self):
        """H1 through H10 must all be represented in HallucinationCategory."""
        categories = {h.name for h in HallucinationCategory}
        for i in range(1, 11):
            assert any(f"H{i}_" in cat for cat in categories)

    def test_grounding_evidence_valid_instantiation(self):
        """GroundingEvidence instantiates and forbids extra fields."""
        ev = GroundingEvidence(
            evidence_id="f1",
            source_type=EvidenceSourceType.PATIENT_FACT,
            source_id="f1",
            text="stage IV adenocarcinoma",
            start_char=10,
            end_char=33,
            assertion="PRESENT",
        )
        assert ev.evidence_id == "f1"
        assert ev.assertion == "PRESENT"

        with pytest.raises(ValidationError):
            GroundingEvidence(
                evidence_id="f1",
                source_type=EvidenceSourceType.PATIENT_FACT,
                source_id="f1",
                text="stage IV adenocarcinoma",
                forbidden_extra="disallowed",
            )

    def test_grounding_claim_valid_instantiation(self):
        """GroundingClaim instantiates and enforces validation."""
        claim = GroundingClaim(
            claim_id="c1-001",
            claim_text="Patient has stage IV adenocarcinoma",
            claim_type=ClaimType.PATIENT_FACT,
            support_status=SupportStatus.SUPPORTED,
            supporting_evidence_ids=["f1"],
            confidence=1.0,
        )
        assert claim.claim_id == "c1-001"
        assert claim.support_status == SupportStatus.SUPPORTED
        assert claim.contradiction_status == ContradictionStatus.NO_CONTRADICTION

    def test_grounding_evaluation_counts_consistency(self):
        """GroundingEvaluation enforces that total_claims equals the sum of status buckets."""
        claim1 = GroundingClaim(
            claim_id="c1",
            claim_text="Test claim 1",
            claim_type=ClaimType.PATIENT_FACT,
            support_status=SupportStatus.SUPPORTED,
        )
        claim2 = GroundingClaim(
            claim_id="c2",
            claim_text="Test claim 2",
            claim_type=ClaimType.PATIENT_FACT,
            support_status=SupportStatus.UNSUPPORTED,
        )

        # Consistent counts
        eval_obj = GroundingEvaluation(
            evaluation_id="eval-01",
            trial_id="T1",
            criterion_id="crit-1",
            raw_reasoning_text="Test claim 1. Test claim 2.",
            claims=[claim1, claim2],
            total_claims=2,
            supported_claim_count=1,
            unsupported_claim_count=1,
        )
        assert eval_obj.total_claims == 2

        # Inconsistent counts must raise ValidationError
        with pytest.raises(ValidationError):
            GroundingEvaluation(
                evaluation_id="eval-bad",
                trial_id="T1",
                criterion_id="crit-1",
                raw_reasoning_text="Test claim 1.",
                claims=[claim1],
                total_claims=2,  # mismatch with len(claims)=1 and sum=1
                supported_claim_count=1,
            )
