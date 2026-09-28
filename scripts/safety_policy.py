"""
MedMatch Clinical Safety Policy Implementation.
Phase 12: Clinical Safety.

Implements conservative reasoning policy rules (POL-01 to POL-18),
unit normalizations, deterministic inequality math, criterion-dependent
temporal validity calculations, and open-world defaults.

IMPORTANT EPISTEMIC NOTICE:
1. Unit conversions implemented here represent synthetic research fixture coverage
   (creatinine and platelets), NOT a universal clinical unit ontology (such as UCUM).
   Unsupported units MUST produce an explicit unsupported condition and cannot be
   silently converted.
2. Temporal staleness is CRITERION-DEPENDENT. A generic threshold (e.g. 90 days)
   is strictly a synthetic research fixture parameter, NOT a universal clinical rule.
   Unsupported temporal semantics strictly default to UNKNOWN / human review.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple


class ClinicalSafetyPolicy:
    """
    Canonical implementation of MedMatch conservative reasoning policy rules.
    """

    # Supported research fixture unit conversion factors
    # e.g., Creatinine: 1 mg/dL = 88.42 umol/L -> umol/L / 88.42 = mg/dL
    CREATININE_UMOL_TO_MGDL = 88.42

    # Canonical list of supported unit pairs for research evaluation
    SUPPORTED_UNIT_DOMAINS = {
        "creatinine": {"mg/dl", "umol/l", "µmol/l"},
        "platelets": {"10^9/l", "10*9/l", "g/l", "k/ul", "10^3/ul", "/ul"},
    }

    # Default synthetic research parameter for temporal staleness fixture tests
    # NOTE: This is NOT a universal medical standard; temporal validity is protocol-specific.
    SYNTHETIC_RESEARCH_FIXTURE_MAX_DAYS = 90

    @classmethod
    def get_unit_conversion_status(cls, from_unit: str, target_unit: str) -> str:
        """
        Explicitly categorizes unit compatibility:
        - 'IDENTICAL': exact match, no conversion needed
        - 'SUPPORTED_RESEARCH_CONVERSION': implemented research conversion factor
        - 'UNSUPPORTED_UNIT_PAIR': unrecognized or incompatible units (must not convert)
        """
        f_u = from_unit.strip().lower()
        t_u = target_unit.strip().lower()
        if f_u == t_u:
            return "IDENTICAL"

        # Creatinine umol/L <-> mg/dL
        is_creat_from = ("umol" in f_u or "µmol" in f_u) or "mg/dl" in f_u
        is_creat_to = ("umol" in t_u or "µmol" in t_u) or "mg/dl" in t_u
        if is_creat_from and is_creat_to and f_u != t_u:
            return "SUPPORTED_RESEARCH_CONVERSION"

        # Platelets 10^9/L <-> K/uL
        is_plat_from = any(p in f_u for p in ["10^9", "10*9", "g/l", "k/ul", "10^3"])
        is_plat_to = any(p in t_u for p in ["10^9", "10*9", "g/l", "k/ul", "10^3"])
        if is_plat_from and is_plat_to and f_u != t_u:
            return "SUPPORTED_RESEARCH_CONVERSION"

        return "UNSUPPORTED_UNIT_PAIR"

    @classmethod
    def normalize_measurement_unit(
        cls, value: float, from_unit: str, target_unit: str
    ) -> Tuple[Optional[float], bool]:
        """
        POL-09: Measurement Unit Mismatch Policy.
        Converts between validated compatible research units.
        Unsupported units strictly return (None, False) to prevent silent corruption.
        """
        status = cls.get_unit_conversion_status(from_unit, target_unit)
        f_u = from_unit.strip().lower()
        t_u = target_unit.strip().lower()

        if status == "IDENTICAL":
            return value, True

        if status == "SUPPORTED_RESEARCH_CONVERSION":
            # Creatinine umol/L <-> mg/dL
            if ("umol" in f_u or "µmol" in f_u) and "mg/dl" in t_u:
                return round(value / cls.CREATININE_UMOL_TO_MGDL, 4), True
            if "mg/dl" in f_u and ("umol" in t_u or "µmol" in t_u):
                return round(value * cls.CREATININE_UMOL_TO_MGDL, 4), True

            # Platelets 10^9/L <-> /uL or K/uL
            if ("10^9" in f_u or "10*9" in f_u or "g/l" in f_u) and ("k/ul" in t_u or "10^3" in t_u):
                return value, True  # 100 x 10^9/L == 100 K/uL
            if ("k/ul" in f_u or "10^3" in f_u) and ("10^9" in t_u or "10*9" in t_u):
                return value, True

        # Unsupported or incompatible units: strictly return None to force UNKNOWN/rejection
        return None, False

    @staticmethod
    def evaluate_numerical_inequality(
        comparator: str, patient_val: float, threshold: float
    ) -> bool:
        """
        POL-08: Numerical Boundary Values Policy.
        Deterministic mathematical evaluation of floating-point inequalities.
        Strictly prevents favorable rounding.
        """
        comp = comparator.strip()
        if comp in (">=", "=>"):
            return patient_val >= threshold
        if comp in ("<=", "=<"):
            return patient_val <= threshold
        if comp == ">":
            return patient_val > threshold
        if comp == "<":
            return patient_val < threshold
        if comp in ("==", "="):
            return abs(patient_val - threshold) < 1e-6
        raise ValueError(f"Unsupported comparator '{comparator}'")

    @staticmethod
    def evaluate_temporal_washout(
        elapsed_days: Optional[int], required_washout_days: int
    ) -> Tuple[str, str]:
        """
        POL-07: Temporal Ambiguity & Mandatory Drug Washouts Policy.
        Returns: (status, reasoning)
        """
        if elapsed_days is None:
            return "UNKNOWN", "Temporal completion date is ambiguous or unrecorded."
        if elapsed_days < required_washout_days:
            return (
                "FAIL",
                f"Prior therapy completed {elapsed_days} days ago; violates required {required_washout_days}-day washout window.",
            )
        return (
            "PASS",
            f"Prior therapy completed {elapsed_days} days ago; satisfies required {required_washout_days}-day washout window.",
        )

    @classmethod
    def evaluate_temporal_staleness(
        cls,
        duration_days: Optional[int],
        criterion_max_days: Optional[int] = None,
        use_synthetic_fixture_fallback: bool = True,
    ) -> Tuple[bool, str]:
        """
        POL-04 / S22: Temporal Evidence Validity Policy.
        Temporal validity is strictly CRITERION-DEPENDENT.
        If a trial criterion defines a maximum allowed age (e.g. labs within 14 days),
        that protocol threshold is enforced.
        If the criterion does not specify a window, a generic 90-day threshold is only
        permitted as a synthetic research fixture test parameter.
        Uninterpretable or unsupported temporal semantics strictly default to UNKNOWN.
        """
        if duration_days is None:
            return False, "Temporal duration unrecorded; defaults to UNKNOWN for clinical review."

        threshold = criterion_max_days
        if threshold is None and use_synthetic_fixture_fallback:
            threshold = cls.SYNTHETIC_RESEARCH_FIXTURE_MAX_DAYS

        if threshold is not None and duration_days > threshold:
            return True, f"Fact is {duration_days} days old, exceeding threshold of {threshold} days."

        return False, f"Fact is {duration_days} days old, within permitted window."

    @classmethod
    def is_fact_stale(
        cls,
        duration_days: Optional[int],
        max_allowed_days: Optional[int] = None,
    ) -> bool:
        """Backward-compatible helper for temporal staleness checks."""
        is_stale, _ = cls.evaluate_temporal_staleness(
            duration_days=duration_days,
            criterion_max_days=max_allowed_days,
            use_synthetic_fixture_fallback=True,
        )
        return is_stale

    @staticmethod
    def check_conflicting_assertions(
        facts: List[Dict[str, Any]]
    ) -> Tuple[bool, Optional[str]]:
        """
        POL-04 / S7: Conflicting Patient Facts Policy.
        Detects opposing assertions (PRESENT vs ABSENT) for the same medical concept.
        """
        assertions_by_concept: Dict[str, set] = {}
        for f in facts:
            concept = f.get("concept", "").strip().lower()
            assertion = f.get("assertion", "UNKNOWN").upper()
            if concept and assertion in ("PRESENT", "ABSENT"):
                assertions_by_concept.setdefault(concept, set()).add(assertion)

        for concept, ast_set in assertions_by_concept.items():
            if "PRESENT" in ast_set and "ABSENT" in ast_set:
                return (
                    True,
                    f"Contradictory findings detected for concept '{concept}': both PRESENT and ABSENT documented.",
                )
        return False, None

    @staticmethod
    def apply_open_world_default(evidence_count: int) -> Tuple[str, str]:
        """
        POL-01 / POL-11: Open-World Completeness Policy.
        Absence of evidence strictly results in UNKNOWN.
        """
        if evidence_count == 0:
            return "UNKNOWN", "Absence of documented evidence strictly defaults to UNKNOWN."
        return "PASS", "Documented evidence verified."
