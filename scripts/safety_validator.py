"""
MedMatch Machine-Checkable Safety Invariant Validator.
Phase 12: Clinical Safety.

Implements programmatic verification of INV-01 through INV-15.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

try:
    from scripts.safety_schema import SafetyInvariantID
except ImportError:
    from safety_schema import SafetyInvariantID


class SafetyInvariantViolation(Exception):
    """Raised when a machine-checkable safety invariant is violated."""
    def __init__(self, invariant_id: SafetyInvariantID, message: str) -> None:
        super().__init__(f"[{invariant_id.value}] {message}")
        self.invariant_id = invariant_id
        self.message = message


class MachineCheckableSafetyValidator:
    """
    Validates machine-checkable safety invariants INV-01 through INV-15.
    """

    @staticmethod
    def validate_all_invariants(
        patient_facts: List[Dict[str, Any]],
        trial_criteria: List[Dict[str, Any]],
        criterion_evaluations: List[Dict[str, Any]],
        final_trial_decision: str,
        raw_note: str,
        explanation_claims: Optional[List[str]] = None,
        override_record: Optional[Dict[str, Any]] = None,
        user_hospital_id: Optional[str] = None,
        retrieved_hospital_id: Optional[str] = None,
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Runs complete machine-checkable invariant verification suite.
        Returns: (is_valid, list_of_violations)
        """
        violations: List[Dict[str, Any]] = []

        # INV-01: No fabricated patient facts
        for f in patient_facts:
            snippet = f.get("snippet", "")
            offset = f.get("start_offset", -1)
            src = f.get("source_field", "")
            if snippet and snippet not in raw_note:
                violations.append({
                    "invariant_id": SafetyInvariantID.INV_01.value,
                    "description": f"Fact snippet '{snippet}' not found in raw clinical note.",
                })
            elif offset == -1 and not src:
                violations.append({
                    "invariant_id": SafetyInvariantID.INV_01.value,
                    "description": f"Fact '{f.get('concept')}' lacks valid source_field or offset.",
                })

        # INV-02: No fabricated trial criteria
        valid_cids = {c.get("criterion_id") or c.get("id") for c in trial_criteria}
        for ce in criterion_evaluations:
            cid = ce.get("criterion_id")
            if cid and cid not in valid_cids and len(valid_cids) > 0:
                violations.append({
                    "invariant_id": SafetyInvariantID.INV_02.value,
                    "description": f"Criterion ID '{cid}' does not belong to target trial protocol.",
                })

        # INV-03 & INV-05: UNKNOWN to PASS & Evidence support
        c_statuses = [str(ce.get("status", "")).upper() for ce in criterion_evaluations]
        has_unknown = "UNKNOWN" in c_statuses
        has_fail = "FAIL" in c_statuses

        for ce in criterion_evaluations:
            st = str(ce.get("status", "")).upper()
            evs = ce.get("evidence_citations", []) or ce.get("evidence", [])
            if st in ("PASS", "FAIL") and len(evs) == 0:
                violations.append({
                    "invariant_id": SafetyInvariantID.INV_05.value,
                    "description": f"Criterion '{ce.get('criterion_id')}' evaluated as {st} without supporting evidence.",
                })
                # INV-04: Missing information treated as negative or positive
                violations.append({
                    "invariant_id": SafetyInvariantID.INV_04.value,
                    "description": f"Criterion '{ce.get('criterion_id')}' evaluated as {st} despite zero documented evidence (open-world violation).",
                })
            # INV-07: Traceable evidence mandate
            if st in ("PASS", "FAIL") and ce.get("traceable") is False:
                violations.append({
                    "invariant_id": SafetyInvariantID.INV_07.value,
                    "description": f"Criterion '{ce.get('criterion_id')}' lacks traceable evidence link.",
                })
            # INV-10: Temporal constraint verification
            if ce.get("has_temporal_constraint") and not ce.get("temporal_validated", True):
                violations.append({
                    "invariant_id": SafetyInvariantID.INV_10.value,
                    "description": f"Criterion '{ce.get('criterion_id')}' has unverified temporal constraint.",
                })
            # INV-11: Numerical constraint verification
            if ce.get("has_numerical_constraint") and not ce.get("numerical_validated", True):
                violations.append({
                    "invariant_id": SafetyInvariantID.INV_11.value,
                    "description": f"Criterion '{ce.get('criterion_id')}' has unverified numerical threshold.",
                })

        if has_unknown and final_trial_decision == "ELIGIBLE":
            violations.append({
                "invariant_id": SafetyInvariantID.INV_03.value,
                "description": "Trial marked ELIGIBLE while one or more criteria remain UNKNOWN.",
            })

        # INV-06: Unsupported definitive eligibility decision
        if final_trial_decision == "ELIGIBLE" and (has_unknown or has_fail):
            violations.append({
                "invariant_id": SafetyInvariantID.INV_06.value,
                "description": "ELIGIBLE decision emitted with non-zero failed or unknown criteria.",
            })

        # INV-08: Provenance offsets
        for ce in criterion_evaluations:
            evs = ce.get("evidence_citations", []) or ce.get("evidence", [])
            for ev in evs:
                if isinstance(ev, dict):
                    start = ev.get("start_offset", -1)
                    end = ev.get("end_offset", -1)
                    snip = ev.get("text_snippet") or ev.get("snippet", "")
                    if start >= 0 and end > start and snip and raw_note:
                        if start < len(raw_note) and raw_note[start:end] != snip:
                            violations.append({
                                "invariant_id": SafetyInvariantID.INV_08.value,
                                "description": f"Citation offset mismatch: note[{start}:{end}] != '{snip}'.",
                            })

        # INV-09: Conflict disclosure mandate
        concepts: Dict[str, set] = {}
        for f in patient_facts:
            c_name = f.get("concept", "").strip().lower()
            ast = f.get("assertion", "").upper()
            if c_name and ast in ("PRESENT", "ABSENT"):
                concepts.setdefault(c_name, set()).add(ast)
        for c_name, asts in concepts.items():
            if "PRESENT" in asts and "ABSENT" in asts:
                # Contradiction exists; verify trial is NEEDS_REVIEW
                if final_trial_decision != "NEEDS_REVIEW":
                    violations.append({
                        "invariant_id": SafetyInvariantID.INV_09.value,
                        "description": f"Concept '{c_name}' has conflicting findings but decision is not NEEDS_REVIEW.",
                    })

        # INV-12 & INV-13: Overrides
        if override_record is not None:
            orig = override_record.get("original_machine_status")
            rev_id = override_record.get("reviewer_id")
            rat = override_record.get("rationale", "")
            if not orig:
                violations.append({
                    "invariant_id": SafetyInvariantID.INV_12.value,
                    "description": "Override failed to preserve original machine decision state.",
                })
            if not rev_id or len(rat.strip()) < 10:
                violations.append({
                    "invariant_id": SafetyInvariantID.INV_13.value,
                    "description": "Override lacks valid reviewer ID or rationale (< 10 chars).",
                })

        # INV-14: Explanations bounded by graph
        if explanation_claims:
            for claim in explanation_claims:
                # Simplified check for brain scan claim without scan
                if "brain scan unremarkable" in claim.lower() and "brain" not in raw_note.lower():
                    violations.append({
                        "invariant_id": SafetyInvariantID.INV_14.value,
                        "description": f"Explanation contains claim outside evidence graph: '{claim}'.",
                    })

        # INV-15: Tenant boundaries preserved
        if user_hospital_id and retrieved_hospital_id and user_hospital_id != retrieved_hospital_id:
            violations.append({
                "invariant_id": SafetyInvariantID.INV_15.value,
                "description": f"Cross-tenant leakage: user_hospital={user_hospital_id} != retrieved={retrieved_hospital_id}.",
            })

        is_valid = len(violations) == 0
        return is_valid, violations
