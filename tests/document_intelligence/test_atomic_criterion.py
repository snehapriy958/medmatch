"""
Tests for Atomic Criterion Representation and Decomposition.
Phase 3: Clinical Trial Document Intelligence.
"""

import pytest
from pydantic import ValidationError

from scripts.document_schema import (
    AtomicConstraint,
    CriterionDomain,
    CriterionOperator,
    CriterionProvenance,
    CriterionType,
    LogicalRelation,
    TrialCriterion,
)
from scripts.validate_document_extraction import DocumentExtractionValidator


class TestAtomicCriterion:
    """Test suite for atomic constraints, multi-intent decomposition, and non-decomposable logic."""

    def test_single_atomic_numeric_criterion(self):
        """Single atomic constraint with comparator, value, unit."""
        constraint = AtomicConstraint(
            concept="platelet_count",
            operator=CriterionOperator.GTE,
            value=100.0,
            unit="x 10^9/L",
        )
        crit = TrialCriterion(
            criterion_id="CRIT_PLT",
            trial_id="NCT02484404",
            section_id="SEC_001",
            criterion_type=CriterionType.INCLUSION,
            domain=CriterionDomain.LABORATORY_VALUES,
            raw_text="Platelet count >= 100 x 10^9/L.",
            normalized_text="Platelet count >= 100 x 10^9/L",
            is_atomic=True,
            can_decompose=True,
            atomic_constraints=[constraint],
            provenance=CriterionProvenance(
                document_id="DOC_001",
                trial_id="NCT02484404",
                section_id="SEC_001",
                source_text="Platelet count >= 100 x 10^9/L.",
            ),
        )
        assert crit.is_atomic is True
        assert len(crit.atomic_constraints) == 1
        assert crit.atomic_constraints[0].value == 100.0

    def test_compound_decomposable_criterion(self):
        """Sentence with multi-intent requirements decomposed into distinct atomic constraints."""
        c1 = AtomicConstraint(
            concept="age",
            operator=CriterionOperator.GTE,
            value=18,
            unit="years",
        )
        c2 = AtomicConstraint(
            concept="ecog_performance_status",
            operator=CriterionOperator.LTE,
            value=1,
            temporal_anchor="at_screening",
        )
        crit = TrialCriterion(
            criterion_id="CRIT_COMPOUND",
            trial_id="NCT02484404",
            section_id="SEC_001",
            criterion_type=CriterionType.INCLUSION,
            domain=CriterionDomain.PERFORMANCE_STATUS,
            raw_text="Age >= 18 years and ECOG <= 1 at screening.",
            normalized_text="Age >= 18 years and ECOG <= 1 at screening",
            is_atomic=False,
            can_decompose=True,
            compound_relation=LogicalRelation.AND,
            atomic_constraints=[c1, c2],
            provenance=CriterionProvenance(
                document_id="DOC_001",
                trial_id="NCT02484404",
                section_id="SEC_001",
                source_text="Age >= 18 years and ECOG <= 1 at screening.",
            ),
        )
        assert crit.is_atomic is False
        assert crit.compound_relation == LogicalRelation.AND
        assert len(crit.atomic_constraints) == 2

    def test_blocked_atomic_decomposition_with_rationale(self):
        """Clinical criterion whose decomposition should NOT be attempted due to coupled clauses."""
        crit = TrialCriterion(
            criterion_id="CRIT_BLOCKED",
            trial_id="NCT02484404",
            section_id="SEC_001",
            criterion_type=CriterionType.INCLUSION,
            domain=CriterionDomain.ORGAN_FUNCTION,
            raw_text="LVEF >= 50% only if prior doxorubicin > 300 mg/m2; otherwise cardiac evaluation not required.",
            normalized_text="LVEF >= 50% only if prior doxorubicin > 300 mg/m2; otherwise cardiac evaluation not required",
            is_atomic=False,
            can_decompose=False,
            decomposition_block_reason="Dependent condition where cardiac threshold is contingent on cumulative anthracycline threshold",
            atomic_constraints=[],
            provenance=CriterionProvenance(
                document_id="DOC_001",
                trial_id="NCT02484404",
                section_id="SEC_001",
                source_text="LVEF >= 50% only if prior doxorubicin > 300 mg/m2; otherwise cardiac evaluation not required.",
            ),
        )
        assert crit.can_decompose is False
        assert crit.decomposition_block_reason is not None

    def test_free_text_unquantified_criterion(self):
        """Valid clinical free-text criteria without numeric thresholds must be accepted."""
        crit = TrialCriterion(
            criterion_id="CRIT_FREETEXT",
            trial_id="NCT02484404",
            section_id="SEC_001",
            criterion_type=CriterionType.INCLUSION,
            domain=CriterionDomain.DIAGNOSIS_STAGE,
            raw_text="Patient must have signed written informed consent prior to initiating study procedures.",
            normalized_text="Signed written informed consent prior to initiating study procedures",
            is_atomic=True,
            can_decompose=True,
            atomic_constraints=[],
            provenance=CriterionProvenance(
                document_id="DOC_001",
                trial_id="NCT02484404",
                section_id="SEC_001",
                source_text="Patient must have signed written informed consent prior to initiating study procedures.",
            ),
        )
        assert len(crit.atomic_constraints) == 0
        assert crit.raw_text.startswith("Patient must have signed")

    def test_between_operator_constraint(self):
        """Between operator requires a valid 2-element range [min, max]."""
        c = AtomicConstraint(
            concept="systolic_blood_pressure",
            operator=CriterionOperator.BETWEEN,
            value=[90, 140],
            unit="mm Hg",
        )
        assert c.value == [90, 140]
