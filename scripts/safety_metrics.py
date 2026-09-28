"""
MedMatch Clinical Safety Metrics Engine.
Phase 12: Clinical Safety.

Computes the 14 canonical safety metrics (M-S01 to M-S14) with strict zero-denominator safeguards,
along with detailed multi-tiered error injection breakdowns (prevention, detection, mitigation,
human-review routing, and missed injection rates).

CRITICAL METHODOLOGICAL GUIDANCE:
1. Gate Pass Rate is NOT a clinical safety score.
   A lower gate pass rate can be appropriate and expected when additional safety gates
   actively reject, mitigate, or escalate uncertain cases or non-compliant inputs.
   Ranking experimental configurations purely by gate pass rate is methodologically invalid.
2. Error injection outcomes MUST NOT collapse prevention, detection, and mitigation into a single
   indistinguishable number. Each tier must be reported separately alongside aggregate interception coverage.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
try:
    from scripts.safety_schema import ErrorInjectionResult, ErrorInjectionSummary, SafetyGateResult, SafetyMetrics
except ImportError:
    from safety_schema import ErrorInjectionResult, ErrorInjectionSummary, SafetyGateResult, SafetyMetrics


class SafetyMetricsEngine:
    """
    Deterministic calculation engine for Phase 12 Clinical Safety Metrics.
    """

    @staticmethod
    def compute_safety_metrics(
        gate_results: List[SafetyGateResult],
        trial_evaluations: List[Dict[str, Any]],
        criterion_evaluations: List[Dict[str, Any]],
        citations: List[Dict[str, Any]],
        overrides: List[Dict[str, Any]],
        explanations: List[Dict[str, Any]],
        tenant_requests: int = 1,
        tenant_violations: int = 0,
    ) -> SafetyMetrics:
        """
        Computes all 14 canonical safety metrics deterministically.
        NOTE: Gate pass rate reflects the proportion of criterion/fact assertions that satisfied
        all validity constraints without triggering a safety gate violation. It is NOT an overall
        clinical safety score.
        """
        # M-S01: Safety Gate Pass Rate
        total_gates = len(gate_results)
        passed_gates = sum(1 for g in gate_results if g.passed)
        sgpr = passed_gates / total_gates if total_gates > 0 else 1.0

        # M-S02: Unsafe Decision Rate
        total_decisions = len(trial_evaluations)
        unsafe_decisions = sum(1 for d in trial_evaluations if d.get("is_unsafe", False))
        udr = unsafe_decisions / total_decisions if total_decisions > 0 else 0.0

        # M-S03: Unsupported Definitive Decision Rate
        def_decisions = [d for d in trial_evaluations if d.get("status") in ("ELIGIBLE", "INELIGIBLE")]
        unsupp_def = sum(1 for d in def_decisions if d.get("evidence_coverage", 1.0) < 1.0)
        uddr = unsupp_def / len(def_decisions) if len(def_decisions) > 0 else 0.0

        # M-S04: UNKNOWN-to-PASS Violation Rate
        gold_unk_crits = [c for c in criterion_evaluations if c.get("gold_truth") == "UNKNOWN"]
        unk_to_pass = sum(1 for c in gold_unk_crits if c.get("predicted_status") == "PASS")
        upvr = unk_to_pass / len(gold_unk_crits) if len(gold_unk_crits) > 0 else 0.0

        # M-S05: Missing-to-Negative Violation Rate
        missing_entities = [c for c in criterion_evaluations if c.get("is_missing_entity", False)]
        missing_to_neg = sum(1 for c in missing_entities if c.get("inferred_assertion") == "ABSENT")
        mnvr = missing_to_neg / len(missing_entities) if len(missing_entities) > 0 else 0.0

        # M-S06: Evidence Support Rate
        total_crits = len(criterion_evaluations)
        supported_crits = sum(
            1 for c in criterion_evaluations
            if len(c.get("evidence", [])) > 0 or c.get("predicted_status") == "UNKNOWN"
        )
        esr = supported_crits / total_crits if total_crits > 0 else 1.0

        # M-S07: Provenance Validity Rate
        total_citations = len(citations)
        valid_citations = sum(1 for cit in citations if cit.get("is_valid", True))
        pvr = valid_citations / total_citations if total_citations > 0 else 1.0

        # M-S08: Contradiction Disclosure Rate
        conflict_cases = [c for c in criterion_evaluations if c.get("has_contradiction", False)]
        disclosed_conflicts = sum(1 for c in conflict_cases if c.get("predicted_status") == "UNKNOWN")
        cdr = disclosed_conflicts / len(conflict_cases) if len(conflict_cases) > 0 else 1.0

        # M-S09: Temporal Safety Rate
        temporal_crits = [c for c in criterion_evaluations if c.get("is_temporal", False)]
        safe_temporal = sum(1 for c in temporal_crits if c.get("temporal_safe", True))
        tsr = safe_temporal / len(temporal_crits) if len(temporal_crits) > 0 else 1.0

        # M-S10: Numerical Safety Rate
        numerical_crits = [c for c in criterion_evaluations if c.get("is_numerical", False)]
        safe_numerical = sum(1 for c in numerical_crits if c.get("numerical_safe", True))
        nsr = safe_numerical / len(numerical_crits) if len(numerical_crits) > 0 else 1.0

        # M-S11: Human Review Routing Recall
        ambiguous_cases = [
            d for d in trial_evaluations
            if d.get("unknown_count", 0) > 0 or d.get("has_conflicts", False) or d.get("status") == "NEEDS_REVIEW"
        ]
        routed_cases = sum(1 for d in ambiguous_cases if d.get("status") == "NEEDS_REVIEW")
        hrrr = routed_cases / len(ambiguous_cases) if len(ambiguous_cases) > 0 else 1.0

        # M-S12: Human Override Auditability Rate
        total_overrides = len(overrides)
        auditable_overrides = sum(
            1 for o in overrides
            if len(o.get("rationale", "").strip()) >= 10 and o.get("original_preserved", True)
        )
        hoar = auditable_overrides / total_overrides if total_overrides > 0 else 1.0

        # M-S13: Explanation Safety Rate
        total_explanations = len(explanations)
        safe_explanations = sum(1 for e in explanations if e.get("unsupported_claims_count", 0) == 0)
        esr_exp = safe_explanations / total_explanations if total_explanations > 0 else 1.0

        # M-S14: Tenant Isolation Violation Rate
        tivr = tenant_violations / tenant_requests if tenant_requests > 0 else 0.0

        return SafetyMetrics(
            safety_gate_pass_rate=round(sgpr, 4),
            unsafe_decision_rate=round(udr, 4),
            unsupported_definitive_decision_rate=round(uddr, 4),
            unknown_to_pass_violation_rate=round(upvr, 4),
            missing_to_negative_violation_rate=round(mnvr, 4),
            evidence_support_rate=round(esr, 4),
            provenance_validity_rate=round(pvr, 4),
            contradiction_disclosure_rate=round(cdr, 4),
            temporal_safety_rate=round(tsr, 4),
            numerical_safety_rate=round(nsr, 4),
            human_review_routing_recall=round(hrrr, 4),
            human_override_auditability_rate=round(hoar, 4),
            explanation_safety_rate=round(esr_exp, 4),
            tenant_isolation_violation_rate=round(tivr, 4),
            total_evaluations=total_decisions,
            total_gate_checks=total_gates,
        )

    @staticmethod
    def compute_error_injection_summary(
        results: List[ErrorInjectionResult],
    ) -> ErrorInjectionSummary:
        """
        Computes detailed multi-tiered error injection metrics.
        Distinguishes:
        - prevention (blocking before execution/emission)
        - detection (flagging/logging anomaly)
        - mitigation (applying conservative fallback like UNKNOWN)
        - human review routing (escalating to clinician)
        - missed injections (escaped all defense layers)
        - aggregate interception (any defense tier engaged)
        """
        n = len(results)
        if n == 0:
            return ErrorInjectionSummary(
                total_injections=0,
                prevented_count=0,
                prevention_rate=0.0,
                detected_count=0,
                detection_rate=0.0,
                mitigated_count=0,
                mitigation_rate=0.0,
                escalated_to_review_count=0,
                human_review_routing_rate=0.0,
                missed_count=0,
                missed_injection_rate=0.0,
                aggregate_interception_count=0,
                aggregate_interception_rate=0.0,
            )

        prevented_count = sum(1 for r in results if r.prevented)
        detected_count = sum(1 for r in results if r.detected)
        mitigated_count = sum(1 for r in results if r.mitigated)
        escalated_count = sum(1 for r in results if r.escalated_to_review)

        # An injection is missed if none of prevented, detected, mitigated, or escalated occurred
        missed_count = sum(
            1 for r in results
            if not (r.prevented or r.detected or r.mitigated or r.escalated_to_review)
        )
        intercepted_count = n - missed_count

        return ErrorInjectionSummary(
            total_injections=n,
            prevented_count=prevented_count,
            prevention_rate=round(prevented_count / n, 4),
            detected_count=detected_count,
            detection_rate=round(detected_count / n, 4),
            mitigated_count=mitigated_count,
            mitigation_rate=round(mitigated_count / n, 4),
            escalated_to_review_count=escalated_count,
            human_review_routing_rate=round(escalated_count / n, 4),
            missed_count=missed_count,
            missed_injection_rate=round(missed_count / n, 4),
            aggregate_interception_count=intercepted_count,
            aggregate_interception_rate=round(intercepted_count / n, 4),
        )
