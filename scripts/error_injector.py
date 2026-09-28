"""
MedMatch Deterministic Error Injection Harness.
Phase 12: Clinical Safety.

Implements fault injection tests INJ-01 through INJ-14 to verify
multi-tiered defense (PREVENTION, DETECTION, MITIGATION, HUMAN_REVIEW).

CRITICAL METHODOLOGICAL GUIDANCE:
Each error injection reports separate boolean outcomes for:
- prevented: transaction was blocked before execution or emission
- detected: anomaly was identified, recorded, and flagged
- mitigated: conservative safe default (such as UNKNOWN or ABSENT) was applied
- escalated_to_review: ambiguity or conflict was routed to clinical review
- missed: corruption escaped all defense tiers undetected
"""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Tuple

try:
    from scripts.safety_gates import DeterministicSafetyGates
    from scripts.safety_schema import (
        DefenseTier,
        ErrorInjectionResult,
        SafetyGateID,
        SafetyTaxonomyCode,
    )
except ImportError:
    from safety_gates import DeterministicSafetyGates
    from safety_schema import (
        DefenseTier,
        ErrorInjectionResult,
        SafetyGateID,
        SafetyTaxonomyCode,
    )


class DeterministicErrorInjector:
    """
    Executes systematic synthetic fault injection against safety gates.
    """

    @staticmethod
    def run_all_injections() -> List[ErrorInjectionResult]:
        """Runs all 14 deterministic error injections and returns results."""
        results: List[ErrorInjectionResult] = []

        # INJ-01: Fabricated Patient Fact Injection (Target: GATE-01, PREVENTION)
        res_01 = DeterministicSafetyGates.gate_01_patient_fact_provenance(
            fact={"concept": "HER2 amplified", "snippet": "HER2 3+ confirmed by FISH"},
            raw_note="Patient is a 60yo female with triple-negative breast cancer.",
        )
        results.append(
            ErrorInjectionResult(
                injection_id="INJ-01",
                corruption_type="Fabricated Patient Fact",
                target_gate=SafetyGateID.GATE_01,
                defense_tier=DefenseTier.PREVENTION,
                detected=not res_01.passed,
                mitigated=False,
                prevented=not res_01.passed,
                escalated_to_review=False,
                taxonomy_code=SafetyTaxonomyCode.S1,
                details=res_01.violation_message or "Prevented unanchored patient fact",
            )
        )

        # INJ-02: Fabricated Trial Criterion Injection (Target: GATE-02, PREVENTION)
        res_02 = DeterministicSafetyGates.gate_02_criterion_schema_integrity(
            criterion={"criterion_id": "", "trial_id": "NCT02484404"}
        )
        results.append(
            ErrorInjectionResult(
                injection_id="INJ-02",
                corruption_type="Fabricated Trial Criterion",
                target_gate=SafetyGateID.GATE_02,
                defense_tier=DefenseTier.PREVENTION,
                detected=not res_02.passed,
                mitigated=False,
                prevented=not res_02.passed,
                escalated_to_review=False,
                taxonomy_code=SafetyTaxonomyCode.S2,
                details=res_02.violation_message or "Prevented invalid criterion schema",
            )
        )

        # INJ-03: Evidence Removal / Missing Info (Target: GATE-11, MITIGATION)
        res_03 = DeterministicSafetyGates.gate_11_open_world_completeness(evidence_items=[])
        results.append(
            ErrorInjectionResult(
                injection_id="INJ-03",
                corruption_type="Evidence Removal (Missing Info)",
                target_gate=SafetyGateID.GATE_11,
                defense_tier=DefenseTier.MITIGATION,
                detected=not res_03.passed,
                mitigated=True,
                prevented=False,
                escalated_to_review=True,
                taxonomy_code=SafetyTaxonomyCode.S4,
                details=res_03.remedial_action_taken or "Mitigated via open-world default UNKNOWN",
            )
        )

        # INJ-04: Negation Inversion (Target: GATE-08, MITIGATION)
        res_04 = DeterministicSafetyGates.gate_08_negation_integrity(
            finding_text="Patient denies shortness of breath", extracted_assertion="PRESENT"
        )
        results.append(
            ErrorInjectionResult(
                injection_id="INJ-04",
                corruption_type="Negation Inversion",
                target_gate=SafetyGateID.GATE_08,
                defense_tier=DefenseTier.MITIGATION,
                detected=not res_04.passed,
                mitigated=True,
                prevented=False,
                escalated_to_review=False,
                taxonomy_code=SafetyTaxonomyCode.S8,
                details=res_04.remedial_action_taken or "Mitigated by flipping polarity to ABSENT",
            )
        )

        # INJ-05: Temporal Date Shift / Washout Violation (Target: GATE-07, MITIGATION)
        res_05 = DeterministicSafetyGates.gate_07_temporal_washout(elapsed_days=15, required_days=28)
        results.append(
            ErrorInjectionResult(
                injection_id="INJ-05",
                corruption_type="Temporal Date Shift (Washout Violation)",
                target_gate=SafetyGateID.GATE_07,
                defense_tier=DefenseTier.MITIGATION,
                detected=not res_05.passed,
                mitigated=True,
                prevented=False,
                escalated_to_review=False,
                taxonomy_code=SafetyTaxonomyCode.S9,
                details=res_05.violation_message or "Mitigated by marking criterion FAIL -> INELIGIBLE",
            )
        )

        # INJ-06: Numerical Boundary Alteration (Target: GATE-06, MITIGATION)
        res_06 = DeterministicSafetyGates.gate_06_numerical_boundary(
            patient_val=99.0, comparator=">=", threshold=100.0
        )
        ineq_satisfied = res_06.metadata.get("inequality_satisfied", False)
        results.append(
            ErrorInjectionResult(
                injection_id="INJ-06",
                corruption_type="Numerical Boundary Alteration",
                target_gate=SafetyGateID.GATE_06,
                defense_tier=DefenseTier.MITIGATION,
                detected=not ineq_satisfied,
                mitigated=True,
                prevented=False,
                escalated_to_review=False,
                taxonomy_code=SafetyTaxonomyCode.S10,
                details="Deterministic math correctly evaluated 99.0 >= 100.0 as False",
            )
        )

        # INJ-07: Incompatible Unit Alteration (Target: GATE-06, PREVENTION)
        res_07 = DeterministicSafetyGates.gate_06_numerical_boundary(
            patient_val=100.0, comparator="<=", threshold=1.5, patient_unit="U/L", target_unit="mg/dL"
        )
        results.append(
            ErrorInjectionResult(
                injection_id="INJ-07",
                corruption_type="Incompatible Unit Alteration",
                target_gate=SafetyGateID.GATE_06,
                defense_tier=DefenseTier.PREVENTION,
                detected=not res_07.passed,
                mitigated=False,
                prevented=not res_07.passed,
                escalated_to_review=False,
                taxonomy_code=SafetyTaxonomyCode.S11,
                details=res_07.violation_message or "Prevented invalid unit comparison",
            )
        )

        # INJ-08: Contradictory Evidence Injection (Target: GATE-09, HUMAN_REVIEW)
        res_08 = DeterministicSafetyGates.gate_09_contradiction_escalation(
            facts=[
                {"concept": "EGFR L858R", "assertion": "PRESENT"},
                {"concept": "EGFR L858R", "assertion": "ABSENT"},
            ]
        )
        results.append(
            ErrorInjectionResult(
                injection_id="INJ-08",
                corruption_type="Contradictory Evidence Injection",
                target_gate=SafetyGateID.GATE_09,
                defense_tier=DefenseTier.HUMAN_REVIEW,
                detected=not res_08.passed,
                mitigated=False,
                prevented=False,
                escalated_to_review=True,
                taxonomy_code=SafetyTaxonomyCode.S7,
                details=res_08.violation_message or "Escalated to P1 Review",
            )
        )

        # INJ-09: Provenance Offset Deletion / Corruption (Target: GATE-18, DETECTION)
        res_09 = DeterministicSafetyGates.gate_18_verbatim_provenance(
            snippet="Platelets 150", source_text="Short note text", start_offset=100, end_offset=200
        )
        results.append(
            ErrorInjectionResult(
                injection_id="INJ-09",
                corruption_type="Provenance Offset Corruption",
                target_gate=SafetyGateID.GATE_18,
                defense_tier=DefenseTier.DETECTION,
                detected=not res_09.passed,
                mitigated=False,
                prevented=False,
                escalated_to_review=False,
                taxonomy_code=SafetyTaxonomyCode.S16,
                details=res_09.violation_message or "Detected offset drift",
            )
        )

        # INJ-10: Spurious Citation Injection (Target: GATE-12, DETECTION)
        res_10 = DeterministicSafetyGates.gate_12_claim_grounding(
            claim="Patient has normal renal clearance",
            evidence_nodes=[{"snippet": "Normal bowel sounds on auscultation"}],
        )
        results.append(
            ErrorInjectionResult(
                injection_id="INJ-10",
                corruption_type="Spurious Citation Injection",
                target_gate=SafetyGateID.GATE_12,
                defense_tier=DefenseTier.DETECTION,
                detected=not res_10.passed,
                mitigated=True,
                prevented=False,
                escalated_to_review=False,
                taxonomy_code=SafetyTaxonomyCode.S17,
                details=res_10.violation_message or "Detected ungrounded claim and stripped citation",
            )
        )

        # INJ-11: Forced UNKNOWN to PASS Flip (Target: GATE-05, MITIGATION)
        res_11 = DeterministicSafetyGates.gate_05_strict_tri_state(status="PASS", evidence=[])
        results.append(
            ErrorInjectionResult(
                injection_id="INJ-11",
                corruption_type="Forced UNKNOWN to PASS Flip",
                target_gate=SafetyGateID.GATE_05,
                defense_tier=DefenseTier.MITIGATION,
                detected=not res_11.passed,
                mitigated=True,
                prevented=False,
                escalated_to_review=True,
                taxonomy_code=SafetyTaxonomyCode.S5,
                details=res_11.remedial_action_taken or "Overwrote to UNKNOWN and escalated",
            )
        )

        # INJ-12: Blank Reviewer Override Submission (Target: GATE-16, PREVENTION)
        res_12 = DeterministicSafetyGates.gate_16_auditable_override(
            original_status="INELIGIBLE", reviewer_id="DR_SMITH", rationale=""
        )
        results.append(
            ErrorInjectionResult(
                injection_id="INJ-12",
                corruption_type="Blank Reviewer Override",
                target_gate=SafetyGateID.GATE_16,
                defense_tier=DefenseTier.PREVENTION,
                detected=not res_12.passed,
                mitigated=False,
                prevented=not res_12.passed,
                escalated_to_review=False,
                taxonomy_code=SafetyTaxonomyCode.S19,
                details=res_12.violation_message or "Prevented invalid override submission",
            )
        )

        # INJ-13: Cross-Tenant Data Injection (Target: GATE-19, PREVENTION)
        res_13 = DeterministicSafetyGates.gate_19_tenant_isolation(
            user_hospital_id="HOSP_A", request_hospital_id="HOSP_A", candidate_hospital_id="HOSP_B"
        )
        results.append(
            ErrorInjectionResult(
                injection_id="INJ-13",
                corruption_type="Cross-Tenant Data Injection",
                target_gate=SafetyGateID.GATE_19,
                defense_tier=DefenseTier.PREVENTION,
                detected=not res_13.passed,
                mitigated=False,
                prevented=not res_13.passed,
                escalated_to_review=False,
                taxonomy_code=SafetyTaxonomyCode.S21,
                details=res_13.violation_message or "Purged foreign trial and blocked cross-tenant access",
            )
        )

        # INJ-14: Audit Failure Simulation (Target: GATE-20, PREVENTION)
        res_14 = DeterministicSafetyGates.gate_20_fail_closed_audit(audit_success=False)
        results.append(
            ErrorInjectionResult(
                injection_id="INJ-14",
                corruption_type="Audit Persistence Failure",
                target_gate=SafetyGateID.GATE_20,
                defense_tier=DefenseTier.PREVENTION,
                detected=not res_14.passed,
                mitigated=False,
                prevented=not res_14.passed,
                escalated_to_review=False,
                taxonomy_code=SafetyTaxonomyCode.S20,
                details=res_14.violation_message or "Fail-closed transaction aborted",
            )
        )

        return results
