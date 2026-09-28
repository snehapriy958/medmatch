"""
Tests for Grounding Validator & Provenance Auditing.
Phase 8: Grounding Evaluation & Faithfulness Auditing.
"""

import pytest

from scripts.eligibility_schema import CriterionEvaluationRecord, CriterionEvaluationStatus, EvidenceCitation
from scripts.grounding_schema import (
    ClaimType,
    ContradictionStatus,
    GroundingClaim,
    HallucinationCategory,
    SupportStatus,
)
from scripts.grounding_validator import GroundingValidator


class TestGroundingValidator:
    """Verifies citation auditing, contradiction detection, and claim support classification."""

    def setup_method(self):
        self.validator = GroundingValidator()

    def test_citation_validation_detects_wrong_patient_fact_id(self):
        """Citation referencing nonexistent fact_id is flagged as invalid."""
        citations = [
            EvidenceCitation(
                fact_id="nonexistent-fact-999",
                text_snippet="some snippet",
                source_field="patient_note",
            )
        ]
        records = self.validator.validate_citations(
            citations=citations,
            patient_facts=[{"fact_id": "real-fact-1", "concept": "NSCLC"}],
            trial_id="NCT001",
            criterion_id="c1",
        )
        assert len(records) == 1
        assert not records[0].is_valid
        assert records[0].error_type == "WRONG_PATIENT_FACT_REFERENCE"

    def test_citation_validation_detects_nonexistent_evidence_span(self):
        """Citation pointing beyond note bounds or mismatched text is flagged."""
        citations = [
            EvidenceCitation(
                fact_id="f1",
                text_snippet="melanoma",
                source_field="patient_note",
                start_char=200,
                end_char=210,
            )
        ]
        note = "Patient with stage IV melanoma."  # len = 31
        records = self.validator.validate_citations(
            citations=citations,
            patient_facts=[{"fact_id": "f1", "concept": "melanoma"}],
            trial_id="NCT001",
            criterion_id="c1",
            patient_note=note,
        )
        assert len(records) == 1
        assert not records[0].is_valid
        assert records[0].error_type == "NONEXISTENT_EVIDENCE_SPAN"

    def test_citation_validation_detects_mismatched_retrieval_method(self):
        """Citation claiming hybrid_rrf when active retrieval was dense is flagged."""
        citations = [
            EvidenceCitation(
                fact_id="f1",
                text_snippet="advanced adenocarcinoma",
                source_field="hybrid_rrf:trial:NCT001",
            )
        ]
        records = self.validator.validate_citations(
            citations=citations,
            patient_facts=[{"fact_id": "f1", "concept": "adenocarcinoma"}],
            trial_id="NCT001",
            criterion_id="c1",
            retrieved_evidence={"retrieval_method": "dense", "trial_id": "NCT001"},
        )
        assert len(records) == 1
        assert not records[0].is_valid
        assert records[0].error_type == "MISMATCHED_RETRIEVAL_PROVENANCE"

    def test_citation_validation_detects_wrong_trial_target(self):
        """Citation pointing to wrong trial target is flagged."""
        citations = [
            EvidenceCitation(
                fact_id="f1",
                text_snippet="adenocarcinoma",
                source_field="dense:trial:WRONG-TRIAL-999",
            )
        ]
        records = self.validator.validate_citations(
            citations=citations,
            patient_facts=[{"fact_id": "f1", "concept": "adenocarcinoma"}],
            trial_id="NCT001",
            criterion_id="c1",
            retrieved_evidence={"retrieval_method": "dense", "trial_id": "NCT001"},
        )
        assert len(records) == 1
        assert not records[0].is_valid
        assert records[0].error_type == "WRONG_TRIAL_REFERENCE"

    def test_contradiction_detection_with_negated_fact(self):
        """Claim asserting presence of a concept documented as ABSENT is marked CONTRADICTED."""
        evidence = self.validator.compile_ground_evidence(
            patient_facts=[
                {
                    "fact_id": "f_neg",
                    "concept": "brain metastases",
                    "assertion": "ABSENT",
                    "snippet": "negative for brain metastases",
                }
            ],
            criteria=[{"id": "c1", "description": "Active brain metastases"}],
        )
        claim = GroundingClaim(
            claim_id="cl-001",
            claim_text="Patient has active brain metastases",
            claim_type=ClaimType.PATIENT_FACT,
        )
        eval_cl = self.validator.evaluate_claim_support(claim, evidence)
        assert eval_cl.support_status == SupportStatus.CONTRADICTED
        assert eval_cl.contradiction_status == ContradictionStatus.ASSERTION_CONFLICT
        assert eval_cl.hallucination_category == HallucinationCategory.H6_CONTRADICTION_OF_SOURCE_EVIDENCE

    def test_numerical_contradiction_detected(self):
        """Claim with age discrepancy is marked CONTRADICTED."""
        evidence = self.validator.compile_ground_evidence(
            patient_facts=[],
            criteria=[{"id": "c1", "description": "Age >= 65"}],
            demographics={"age": 45},
        )
        claim = GroundingClaim(
            claim_id="cl-age",
            claim_text="Patient age is 70",
            claim_type=ClaimType.NUMERICAL_VALUE,
        )
        eval_cl = self.validator.evaluate_claim_support(claim, evidence, demographics={"age": 45})
        assert eval_cl.support_status == SupportStatus.CONTRADICTED
        assert eval_cl.contradiction_status == ContradictionStatus.NUMERICAL_CONFLICT
        assert eval_cl.hallucination_category == HallucinationCategory.H3_FABRICATED_NUMERICAL_VALUE

    def test_inferred_claim_marked_unsupported(self):
        """Inferred/speculative claim is marked UNSUPPORTED with H5 category."""
        evidence = self.validator.compile_ground_evidence(
            patient_facts=[{"fact_id": "f1", "concept": "hypertension"}],
            criteria=[],
        )
        claim = GroundingClaim(
            claim_id="cl-inf",
            claim_text="Patient likely tolerates chemotherapy well",
            claim_type=ClaimType.INFERRED_CLAIM,
        )
        eval_cl = self.validator.evaluate_claim_support(claim, evidence)
        assert eval_cl.support_status == SupportStatus.UNSUPPORTED
        assert eval_cl.hallucination_category == HallucinationCategory.H5_UNSUPPORTED_CLINICAL_INFERENCE

    def test_missing_evidence_marked_insufficient(self):
        """Reasoning that acknowledges missing evidence is marked INSUFFICIENT_EVIDENCE (valid abstention)."""
        evidence = self.validator.compile_ground_evidence(
            patient_facts=[],
            criteria=[{"id": "c1", "description": "Serum creatinine <= 1.5"}],
        )
        claim = GroundingClaim(
            claim_id="cl-miss",
            claim_text="Serum creatinine is not documented in clinical record",
            claim_type=ClaimType.PATIENT_FACT,
        )
        eval_cl = self.validator.evaluate_claim_support(claim, evidence)
        assert eval_cl.support_status == SupportStatus.INSUFFICIENT_EVIDENCE
