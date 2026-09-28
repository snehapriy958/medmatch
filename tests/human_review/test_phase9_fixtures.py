"""
Tests executing all 18 Phase 9 synthetic development fixtures.
Verifies routing, prioritization, resolution, audit logging, and guardrails across every case.
"""

from scripts.human_review_experiment import HumanReviewExperimentHarness
from scripts.review_schema import ReviewPriority, ReviewStatus


def test_execute_all_18_fixtures():
    """Verify that every fixture in human_review_fixtures.json executes deterministically."""
    harness = HumanReviewExperimentHarness()
    results, metrics = harness.run_all()

    assert len(results) == 18
    assert metrics.total_cases_evaluated == 18
    assert metrics.unsupported_automatic_decision_rate == 0.0

    for res in results:
        case_id = res["case_id"]
        rec = res["review_record"]

        # Case 18 is the intentional guardrail failure test
        if case_id == "case-18-reviewer-override-without-evidence-rejected":
            assert res["error_captured"] is not None
            assert "requires at least one evidence reference" in res["error_captured"]
            continue

        # All other cases must match expected routing and priority
        assert res["initial_routing_status"] == res["expected_routing"], (
            f"Case {case_id} expected initial routing {res['expected_routing']}, got {res['initial_routing_status']}"
        )
        assert rec.priority == res["expected_priority"], (
            f"Case {case_id} expected priority {res['expected_priority']}, got {rec.priority}"
        )
        if res.get("expected_post_review_status"):
            assert rec.status == res["expected_post_review_status"], (
                f"Case {case_id} expected post-review status {res['expected_post_review_status']}, got {rec.status}"
            )
        else:
            assert rec.status == res["expected_routing"], (
                f"Case {case_id} expected final status {res['expected_routing']}, got {rec.status}"
            )


def test_specific_cases_key_verifications():
    """Detailed checks on key scenario archetypes."""
    harness = HumanReviewExperimentHarness()
    cases = harness.load_fixtures()
    cases_by_id = {c["case_id"]: c for c in cases}

    # Case 01: Clean eligible -> NOT_REQUIRED
    res1 = harness.run_case(cases_by_id["case-01-complete-evidence-eligible"])
    assert res1["review_record"].status == ReviewStatus.NOT_REQUIRED

    # Case 02: Clean ineligible -> NOT_REQUIRED
    res2 = harness.run_case(cases_by_id["case-02-complete-disqualifying-ineligible"])
    assert res2["review_record"].status == ReviewStatus.NOT_REQUIRED

    # Case 04: Conflicting allergy -> ESCALATED
    res4 = harness.run_case(cases_by_id["case-04-conflicting-patient-facts"])
    assert res4["review_record"].status == ReviewStatus.ESCALATED
    assert res4["review_record"].priority == ReviewPriority.ESCALATED

    # Case 09: Grounding unsupported -> PENDING_REVIEW (PRIORITY)
    res9 = harness.run_case(cases_by_id["case-09-grounding-unsupported-intercepted"])
    assert res9["review_record"].status == ReviewStatus.PENDING_REVIEW
    assert res9["review_record"].priority == ReviewPriority.PRIORITY

    # Case 10: Grounding contradiction -> ESCALATED
    res10 = harness.run_case(cases_by_id["case-10-grounding-contradicted-escalated"])
    assert res10["review_record"].status == ReviewStatus.ESCALATED

    # Case 11: Resolved with evidence
    res11 = harness.run_case(cases_by_id["case-11-reviewer-resolves-unknown"])
    assert res11["review_record"].status == ReviewStatus.RESOLVED
    assert len(res11["review_record"].evidence_references) > 0

    # Case 16: Audit preservation of machine output
    res16 = harness.run_case(cases_by_id["case-16-resolved-review-preserves-machine-output"])
    assert res16["review_record"].status == ReviewStatus.RESOLVED
    assert "machine_status" in res16["review_record"].original_machine_output
    assert res16["review_record"].original_machine_output["machine_status"] == "NEEDS_REVIEW"

    # Case 18: Evidence required
    res18 = harness.run_case(cases_by_id["case-18-reviewer-override-without-evidence-rejected"])
    assert "requires at least one evidence reference" in res18["error_captured"]
