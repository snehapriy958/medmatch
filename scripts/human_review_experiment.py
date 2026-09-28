"""
MedMatch Phase 9 Human Review & Uncertainty Experiment Harness.
Phase 9: Formal Uncertainty & Human Review Foundation.

Coordinates:
- Uncertainty profiling across patient and protocol records
- Deterministic review routing (ReviewRoutingPolicy)
- Explainable priority triage (ReviewPrioritizer)
- Human reviewer adjudication and audit logging (ReviewResolutionManager)
- Preservation of original machine decisions
- Metric computation (UncertaintyMetricsCalculator)

Enforces strict empirical benchmark guardrails:
- Development validation only; no empirical benchmark claims without validated ingested datasets.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from scripts.uncertainty_schema import (
        UncertaintyProfile,
        UncertaintyRecord,
        UncertaintySeverity,
        UncertaintyStatus,
        UncertaintyType,
    )
    from scripts.review_schema import (
        HumanReviewRecord,
        ReviewPriority,
        ReviewResolutionRequest,
        ReviewStatus,
        ReviewerDecision,
        ReviewerIdentity,
    )
    from scripts.review_policy import ReviewRoutingPolicy
    from scripts.review_priority import ReviewPrioritizer
    from scripts.review_audit import AuditEventType, ReviewAuditTrail, ReviewResolutionManager
    from scripts.uncertainty_metrics import (
        UncertaintyMetricsCalculator,
        UncertaintyMetricsReport,
    )
    from scripts.eligibility_schema import (
        CriterionEvaluationRecord,
        CriterionEvaluationStatus,
        CriterionType,
        EvidenceCitation,
        TrialEligibilityEvaluation,
        TrialEligibilityStatus,
    )
    from scripts.grounding_schema import (
        ClaimType,
        ContradictionStatus,
        GroundingClaim,
        GroundingEvaluation,
        HallucinationCategory,
        SupportStatus,
    )
except ImportError:
    from uncertainty_schema import (
        UncertaintyProfile,
        UncertaintyRecord,
        UncertaintySeverity,
        UncertaintyStatus,
        UncertaintyType,
    )
    from review_schema import (
        HumanReviewRecord,
        ReviewPriority,
        ReviewResolutionRequest,
        ReviewStatus,
        ReviewerDecision,
        ReviewerIdentity,
    )
    from review_policy import ReviewRoutingPolicy
    from review_priority import ReviewPrioritizer
    from review_audit import AuditEventType, ReviewAuditTrail, ReviewResolutionManager
    from uncertainty_metrics import (
        UncertaintyMetricsCalculator,
        UncertaintyMetricsReport,
    )
    from eligibility_schema import (
        CriterionEvaluationRecord,
        CriterionEvaluationStatus,
        CriterionType,
        EvidenceCitation,
        TrialEligibilityEvaluation,
        TrialEligibilityStatus,
    )
    from grounding_schema import (
        ClaimType,
        ContradictionStatus,
        GroundingClaim,
        GroundingEvaluation,
        HallucinationCategory,
        SupportStatus,
    )


def has_validated_benchmark() -> bool:
    """
    Guardrail function: returns True only if an external validated research
    benchmark with human expert ground truth has been formally ingested.
    """
    return False


class HumanReviewExperimentHarness:
    """
    Evaluation harness executing Phase 9 uncertainty and human review workflows.
    """

    def __init__(self, fixtures_path: Optional[Path] = None):
        self.fixtures_path = fixtures_path or Path("data/fixtures/phase9/human_review_fixtures.json")
        self.audit_trails: Dict[str, ReviewAuditTrail] = {}

    def load_fixtures(self) -> List[Dict[str, Any]]:
        """
        Loads Phase 9 development test cases.
        """
        if not self.fixtures_path.exists():
            raise FileNotFoundError(f"Fixture file not found: {self.fixtures_path}")
        with open(self.fixtures_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("cases", [])

    def run_case(self, case: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes a single test case through the complete Phase 9 workflow:
        1. Parse criterion evaluations into TrialEligibilityEvaluation
        2. Parse uncertainty records into UncertaintyProfile
        3. Evaluate routing and create HumanReviewRecord
        4. Initialize ReviewAuditTrail
        5. If reviewer_action present, execute resolution
        6. Return execution context for metrics
        """
        case_id = case["case_id"]
        trial_id = case["trial_id"]
        patient_id = case["patient_id"]

        # 1. Reconstruct TrialEligibilityEvaluation
        criterion_records: List[CriterionEvaluationRecord] = []
        for c in case.get("criteria", []):
            c_status = CriterionEvaluationStatus(c["status"])
            fact_refs = [f"FACT-{c['criterion_id']}"] if c_status in (CriterionEvaluationStatus.PASS, CriterionEvaluationStatus.FAIL) else []
            criterion_records.append(
                CriterionEvaluationRecord(
                    criterion_id=c["criterion_id"],
                    trial_id=trial_id,
                    criterion_type=CriterionType.INCLUSION,
                    criterion_text=f"Criterion text for {c['criterion_id']}",
                    status=c_status,
                    reasoning=c["reasoning"],
                    evidence_citations=[],
                    patient_fact_references=fact_refs,
                )
            )

        trial_status = TrialEligibilityStatus(case["expected_trial_status"])
        trial_eval = TrialEligibilityEvaluation(
            trial_id=trial_id,
            status=trial_status,
            criterion_evaluations=criterion_records,
            total_criteria_evaluated=len(criterion_records),
            passed_count=sum(1 for e in criterion_records if e.status == CriterionEvaluationStatus.PASS),
            failed_count=sum(1 for e in criterion_records if e.status == CriterionEvaluationStatus.FAIL),
            unknown_count=sum(1 for e in criterion_records if e.status == CriterionEvaluationStatus.UNKNOWN),
            clinical_summary="Test case aggregation summary",
        )

        # 2. Reconstruct UncertaintyProfile
        unc_records: List[UncertaintyRecord] = []
        for u in case.get("uncertainties", []):
            unc_records.append(UncertaintyRecord.model_validate(u))

        unc_profile = UncertaintyProfile(
            case_id=case_id,
            trial_id=trial_id,
            records=unc_records,
        )

        # 3. Reconstruct GroundingEvaluation if present
        grounding_eval = None
        if case.get("grounding"):
            g = case["grounding"]
            sup_cnt = g.get("supported_claim_count", 0)
            unsup_cnt = g.get("unsupported_claim_count", 0)
            contra_cnt = g.get("contradicted_claim_count", 0)
            reconstructed_claims: List[GroundingClaim] = []
            for i in range(sup_cnt):
                reconstructed_claims.append(
                    GroundingClaim(
                        claim_id=f"CLM-SUP-{i+1}",
                        claim_text=f"Supported claim {i+1}",
                        claim_type=ClaimType.PATIENT_FACT,
                        support_status=SupportStatus.SUPPORTED,
                        contradiction_status=ContradictionStatus.NO_CONTRADICTION,
                        confidence=1.0,
                    )
                )
            for i in range(unsup_cnt):
                reconstructed_claims.append(
                    GroundingClaim(
                        claim_id=f"CLM-UNSUP-{i+1}",
                        claim_text=f"Unsupported claim {i+1}",
                        claim_type=ClaimType.PATIENT_FACT,
                        support_status=SupportStatus.UNSUPPORTED,
                        contradiction_status=ContradictionStatus.NO_CONTRADICTION,
                        confidence=0.5,
                        hallucination_category=HallucinationCategory.H1_FABRICATED_PATIENT_FACT,
                    )
                )
            for i in range(contra_cnt):
                reconstructed_claims.append(
                    GroundingClaim(
                        claim_id=f"CLM-CONTRA-{i+1}",
                        claim_text=f"Contradicted claim {i+1}",
                        claim_type=ClaimType.PATIENT_FACT,
                        support_status=SupportStatus.CONTRADICTED,
                        contradiction_status=ContradictionStatus.DIRECT_CONTRADICTION,
                        confidence=0.5,
                        hallucination_category=HallucinationCategory.H6_CONTRADICTION_OF_SOURCE_EVIDENCE,
                    )
                )
            total_claims = len(reconstructed_claims)
            evaluable = max(1, total_claims)
            grounding_eval = GroundingEvaluation(
                evaluation_id=f"GEVAL-{case_id}",
                trial_id=trial_id,
                criterion_id=criterion_records[0].criterion_id if criterion_records else "CRIT-01",
                raw_reasoning_text="Reasoning evaluated for grounding",
                claims=reconstructed_claims,
                citations_audited=[],
                total_claims=total_claims,
                supported_claim_count=sup_cnt,
                partially_supported_claim_count=0,
                unsupported_claim_count=unsup_cnt,
                contradicted_claim_count=contra_cnt,
                insufficient_evidence_count=0,
                claim_support_rate=round(sup_cnt / evaluable, 4),
                unsupported_claim_rate=round(unsup_cnt / evaluable, 4),
                contradiction_rate=round(contra_cnt / evaluable, 4),
                citation_validity_rate=1.0,
                evidence_coverage=1.0,
                grounding_score=g.get("grounding_score", 0.0),
                hallucination_rate=g.get("hallucination_score", 0.0),
                evaluator_version="1.0.0-phase8-research",
            )

        # 4. Evaluate Review Routing and Create Review Record
        review_record = ReviewRoutingPolicy.create_review_record(
            review_id=f"REV-{case_id}",
            case_id=case_id,
            trial_id=trial_id,
            trial_evaluation=trial_eval,
            uncertainty_profile=unc_profile,
            grounding_evaluation=grounding_eval,
        )
        initial_routing_status = review_record.status

        # 5. Initialize Audit Trail
        audit_trail = ReviewAuditTrail(review_id=review_record.review_id)
        audit_trail.append_event(
            event_type=AuditEventType.REVIEW_REQUESTED,
            actor="SYSTEM",
            previous_state=None,
            new_state=review_record.status.value,
            details={"priority": review_record.priority.value},
        )
        self.audit_trails[review_record.review_id] = audit_trail

        # 6. Apply Reviewer Action if present
        reviewer_action = case.get("reviewer_action")
        if reviewer_action:
            # Check if an intentional validation error is expected
            if case.get("expected_error"):
                try:
                    req = ReviewResolutionRequest(
                        review_id=review_record.review_id,
                        reviewer_id=reviewer_action["reviewer_id"],
                        decision=ReviewerDecision(reviewer_action["decision"]),
                        rationale=reviewer_action["rationale"],
                        evidence_references=reviewer_action.get("evidence_references", []),
                        escalation_reason=reviewer_action.get("escalation_reason"),
                    )
                    ReviewResolutionManager.resolve_review(
                        record=review_record,
                        request=req,
                        audit_trail=audit_trail,
                        uncertainty_profile=unc_profile,
                    )
                except ValueError as e:
                    # Expected error occurred; capture in result
                    return {
                        "case_id": case_id,
                        "criteria_count": len(criterion_records),
                        "trial_eval": trial_eval,
                        "uncertainty_profile": unc_profile,
                        "review_record": review_record,
                        "initial_routing_status": initial_routing_status,
                        "expected_routing": ReviewStatus(case["expected_review_status"]),
                        "expected_post_review_status": ReviewStatus(case["expected_post_review_status"]) if "expected_post_review_status" in case else None,
                        "expected_priority": ReviewPriority(case["expected_priority"]),
                        "error_captured": str(e),
                    }

            req = ReviewResolutionRequest(
                review_id=review_record.review_id,
                reviewer_id=reviewer_action["reviewer_id"],
                decision=ReviewerDecision(reviewer_action["decision"]),
                rationale=reviewer_action["rationale"],
                evidence_references=reviewer_action.get("evidence_references", []),
                escalation_reason=reviewer_action.get("escalation_reason"),
            )
            # Advance to IN_REVIEW first
            ReviewResolutionManager.start_review(
                record=review_record,
                reviewer_id=reviewer_action["reviewer_id"],
                audit_trail=audit_trail,
            )
            # Then resolve
            ReviewResolutionManager.resolve_review(
                record=review_record,
                request=req,
                audit_trail=audit_trail,
                uncertainty_profile=unc_profile,
            )

        return {
            "case_id": case_id,
            "criteria_count": len(criterion_records),
            "trial_eval": trial_eval,
            "uncertainty_profile": unc_profile,
            "review_record": review_record,
            "initial_routing_status": initial_routing_status,
            "expected_routing": ReviewStatus(case["expected_review_status"]),
            "expected_post_review_status": ReviewStatus(case["expected_post_review_status"]) if "expected_post_review_status" in case else None,
            "expected_priority": ReviewPriority(case["expected_priority"]),
            "error_captured": None,
        }

    def run_all(self) -> Tuple[List[Dict[str, Any]], UncertaintyMetricsReport]:
        """
        Executes all loaded test fixtures and computes summary metrics.
        """
        cases = self.load_fixtures()
        results = [self.run_case(c) for c in cases]
        metrics = UncertaintyMetricsCalculator.calculate_metrics(results)
        return results, metrics


def main() -> None:
    print("================================================================================")
    print("MEDMATCH PHASE 9: UNCERTAINTY & HUMAN REVIEW EXPERIMENT HARNESS")
    print("================================================================================")
    harness = HumanReviewExperimentHarness()
    results, metrics = harness.run_all()
    print(f"Loaded and executed {len(results)} development test fixtures.")

    for res in results:
        cid = res["case_id"]
        status = res["review_record"].status.value
        init_status = res["initial_routing_status"].value
        priority = res["review_record"].priority.value
        err = f" [REJECTED: {res['error_captured']}]" if res["error_captured"] else ""
        print(f" - {cid:<8} | Initial: {init_status:<14} | Final: {status:<14} | Priority: {priority:<10}{err}")

    print("\n--------------------------------------------------------------------------------")
    print("PHASE 9 UNCERTAINTY & HUMAN REVIEW METRICS (DEVELOPMENT FIXTURES ONLY)")
    print("--------------------------------------------------------------------------------")
    print(f"Total Cases Evaluated:               {metrics.total_cases_evaluated}")
    print(f"Total Criteria Evaluated:            {metrics.total_criteria_evaluated}")
    print(f"Total Uncertainties Logged:          {metrics.total_uncertainties_logged}")
    print(f"Uncertainty Rate (UR):               {metrics.uncertainty_rate:.4f}")
    print(f"Missing Information Rate (MIR):      {metrics.missing_information_rate:.4f}")
    print(f"Conflict Rate (CR):                  {metrics.conflict_rate:.4f}")
    print(f"Ambiguity Rate (AR):                 {metrics.ambiguity_rate:.4f}")
    print(f"Insufficient Evidence Rate (IER):    {metrics.insufficient_evidence_rate:.4f}")
    print(f"Review Routing Rate (RRR):           {metrics.review_routing_rate:.4f}")
    print(f"Resolution Rate (ResR):              {metrics.review_resolution_rate:.4f}")
    print(f"Escalation Rate (ER):                {metrics.escalation_rate:.4f}")
    print(f"Appropriate Review Routing (ARRR):   {metrics.appropriate_review_routing_rate:.4f}")
    print(f"Unsupported Auto Decision (UADR):    {metrics.unsupported_automatic_decision_rate:.4f}")
    print(f"Evidence-Backed Resolution (EBRR):   {metrics.evidence_backed_resolution_rate:.4f}")

    print("\n================================================================================")
    print("EMPIRICAL BENCHMARK GUARDRAIL STATUS")
    print("================================================================================")
    print(f"External Research Benchmark Ingested: {has_validated_benchmark()}")
    print("Notice: The above metrics evaluate synthetic development test fixtures only.")
    print("Empirical clinical performance claims are strictly prohibited until a validated")
    print("external clinical decision-support benchmark is formally ingested.")
    print("================================================================================")


if __name__ == "__main__":
    main()
