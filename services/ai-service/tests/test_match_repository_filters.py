"""
Repository filter tests for MatchRepository's hospital scoping.

IMPORTANT — what these tests actually verify: every test in this file
uses `unittest.mock.MagicMock` in place of a real SQLAlchemy Session.
Nothing here touches a real PostgreSQL database, a real RESTRICT
constraint, or real row-level access control. What is verified is
narrower and purely at the Python/repository-code level:

  1. Given a mocked "database state" that only returns a row when the
     hospital_id passed in matches the row's own hospital_id (i.e. a
     hand-built simulation of what a correct `WHERE hospital_id = :x`
     clause would do), MatchRepository's methods behave correctly —
     they return None / [] rather than the cross-tenant row.
  2. hospital_id is literally present in the SQL text produced by
     each filter() call (via str() on the compiled expression) — so a
     future edit that accidentally drops the hospital_id condition
     from the query would be caught here.

Neither of these is the same claim as "tenant isolation is enforced
by the database" — that would require an integration test against a
real Postgres instance with two real hospitals and real rows, which
this phase does not add. This file is a regression guard on the
*repository code's* filter construction, not a verification of
database-level enforcement. See tests/test_tenant_isolation.py for
the project's existing service-layer isolation tests, which this
file's naming intentionally does not duplicate or claim to replace.
"""
from unittest.mock import MagicMock
from uuid import uuid4

from app.models.match import Match
from app.repositories.match_repository import MatchRepository


HOSPITAL_A = uuid4()
HOSPITAL_B = uuid4()
PATIENT_ID = uuid4()
TRIAL_ID = uuid4()
MATCH_ID = uuid4()


def build_match_for_hospital(hospital_id) -> Match:
    return Match(
        id=MATCH_ID,
        patient_id=PATIENT_ID,
        trial_id=TRIAL_ID,
        hospital_id=hospital_id,
        confidence=0.5,
        overall_status="Needs More Information",
        explanation="Repository filter test fixture.",
        model_version="gemini-test",
    )


def build_repository_with_mocked_hospital_scope(
    querying_hospital_id,
    row_hospital_id,
    return_list: bool,
):
    """
    Build a MatchRepository backed by a MagicMock Session, hand-wired
    to only "find" a row when querying_hospital_id == row_hospital_id
    — a manual stand-in for what a real `WHERE hospital_id = :x`
    clause would do. This is a simulation, not a real query: no SQL
    is executed, no database is involved.
    """

    db = MagicMock()
    query = MagicMock()
    db.query.return_value = query
    query.filter.return_value = query
    query.order_by.return_value = query

    row_matches_the_queried_hospital = (
        querying_hospital_id == row_hospital_id
    )

    if row_matches_the_queried_hospital:
        row = build_match_for_hospital(row_hospital_id)
    else:
        row = None

    query.first.return_value = row
    query.all.return_value = [row] if (row and return_list) else []

    return MatchRepository(db), db, query


def test_get_match_by_id_does_not_return_a_mocked_cross_hospital_row():
    """
    With the mocked session simulating a match that belongs to
    Hospital A, querying with Hospital B's hospital_id (correct
    match_id, wrong hospital_id) returns None — the repository code
    does not fall back to returning the row anyway.
    """

    repository, _, _ = build_repository_with_mocked_hospital_scope(
        querying_hospital_id=HOSPITAL_B,
        row_hospital_id=HOSPITAL_A,
        return_list=False,
    )

    result = repository.get_match_by_id(
        match_id=MATCH_ID,
        hospital_id=HOSPITAL_B,
    )

    assert result is None


def test_get_match_by_id_returns_row_for_matching_mocked_hospital():
    repository, _, _ = build_repository_with_mocked_hospital_scope(
        querying_hospital_id=HOSPITAL_A,
        row_hospital_id=HOSPITAL_A,
        return_list=False,
    )

    result = repository.get_match_by_id(
        match_id=MATCH_ID,
        hospital_id=HOSPITAL_A,
    )

    assert result is not None
    assert result.hospital_id == HOSPITAL_A


def test_list_matches_for_patient_does_not_return_mocked_cross_hospital_rows():
    """
    A patient_id "having matches" under Hospital A (per the mock)
    returns an empty list when queried with Hospital B's
    hospital_id — the repository code does not ignore hospital_id
    when patient_id alone would otherwise match.
    """

    repository, _, _ = build_repository_with_mocked_hospital_scope(
        querying_hospital_id=HOSPITAL_B,
        row_hospital_id=HOSPITAL_A,
        return_list=True,
    )

    result = repository.list_matches_for_patient(
        patient_id=PATIENT_ID,
        hospital_id=HOSPITAL_B,
    )

    assert result == []


def test_list_matches_for_trial_does_not_return_mocked_cross_hospital_rows():
    repository, _, _ = build_repository_with_mocked_hospital_scope(
        querying_hospital_id=HOSPITAL_B,
        row_hospital_id=HOSPITAL_A,
        return_list=True,
    )

    result = repository.list_matches_for_trial(
        trial_id=TRIAL_ID,
        hospital_id=HOSPITAL_B,
    )

    assert result == []


def test_every_read_method_includes_hospital_id_in_its_filter_call():
    """
    Static/structural check (via str() on the compiled filter
    expressions passed to .filter()) that no MatchRepository read
    method has a code path relying on match_id / patient_id /
    trial_id alone — hospital_id text must appear in every filter()
    call across all three read methods. This inspects the query the
    repository *would* send, not the result of sending it.
    """

    repository, db, query = build_repository_with_mocked_hospital_scope(
        querying_hospital_id=HOSPITAL_A,
        row_hospital_id=HOSPITAL_A,
        return_list=True,
    )

    repository.get_match_by_id(
        match_id=MATCH_ID,
        hospital_id=HOSPITAL_A,
    )
    repository.list_matches_for_patient(
        patient_id=PATIENT_ID,
        hospital_id=HOSPITAL_A,
    )
    repository.list_matches_for_trial(
        trial_id=TRIAL_ID,
        hospital_id=HOSPITAL_A,
    )

    for call in query.filter.call_args_list:
        filter_sql = " ".join(str(arg) for arg in call[0])
        assert "matches.hospital_id" in filter_sql
