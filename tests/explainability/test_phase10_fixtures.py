"""
Tests for Phase 10 Development Fixtures Execution & Invariant Verification.
Validates all 18 synthetic scenarios.
"""

from scripts.explainability_experiment import ExplainabilityExperimentHarness


def test_execute_all_18_fixtures():
    """Verify that all 18 fixtures run through harness matching expected validity."""
    harness = ExplainabilityExperimentHarness()
    results, metrics = harness.run_all()

    assert len(results) == 18

    for res in results:
        fid = res["fixture_id"]
        is_valid_exp = res["is_valid_expected"]
        exp_errors = res["expected_errors"]

        gv = res["graph_validation"]
        ev = res["explanation_validation"]

        if is_valid_exp:
            assert gv.is_valid is True, f"Fixture {fid} expected valid graph but got errors: {gv.errors}"
            if ev:
                assert ev.is_valid is True, f"Fixture {fid} expected valid explanation but got errors: {ev.errors}"
        else:
            # Either graph validation failed or explanation validation failed
            has_error = (not gv.is_valid) or (ev and not ev.is_valid)
            assert has_error is True, f"Fixture {fid} expected validation errors {exp_errors} but passed."
            
            all_actual_errors = [e.error_code.value for e in gv.errors]
            if ev:
                all_actual_errors.extend(e.error_code.value for e in ev.errors)
            
            for expected_err in exp_errors:
                assert expected_err in all_actual_errors, (
                    f"Fixture {fid} missing expected error {expected_err}. Found: {all_actual_errors}"
                )


def test_specific_fixtures_key_checks():
    """Verify specific invariants on key test fixtures."""
    harness = ExplainabilityExperimentHarness()
    fixtures = {f["fixture_id"]: f for f in harness.load_fixtures()}

    # Case 14: dangling reference
    res14 = harness.run_case(fixtures["case-14-invalid-dangling-reference"])
    assert res14["graph_validation"].is_valid is False
    assert any(e.error_code.value == "X3_DANGLING_GRAPH_REFERENCE" for e in res14["graph_validation"].errors)

    # Case 15: fabricated provenance
    res15 = harness.run_case(fixtures["case-15-invalid-fabricated-provenance"])
    assert res15["graph_validation"].is_valid is False
    assert any(e.error_code.value == "X2_INVALID_PROVENANCE" for e in res15["graph_validation"].errors)

    # Case 16: unsupported explanation claim
    res16 = harness.run_case(fixtures["case-16-invalid-unsupported-explanation-claim"])
    assert res16["explanation_validation"].is_valid is False
    assert any(e.error_code.value == "X9_UNSUPPORTED_EXPLANATION_CLAIM" for e in res16["explanation_validation"].errors)

    # Case 18: machine output preserved after review
    res18 = harness.run_case(fixtures["case-18-machine-output-preserved-after-review"])
    assert res18["graph_validation"].is_valid is True
    res_node = res18["graph"].get_node("RES-RES-18")
    assert res_node is not None
    assert "original_machine_output" in res_node.properties
    assert res_node.properties["original_machine_output"]["overall_status"] == "NEEDS_REVIEW"
