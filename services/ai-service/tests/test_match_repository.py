from unittest.mock import MagicMock
from uuid import uuid4

from app.models.match import Match
from app.repositories.match_repository import MatchRepository


HOSPITAL_ID = uuid4()
OTHER_HOSPITAL_ID = uuid4()
PATIENT_ID = uuid4()
TRIAL_ID = uuid4()
MATCH_ID = uuid4()


def build_match(
    hospital_id=HOSPITAL_ID,
    patient_id=PATIENT_ID,
    trial_id=TRIAL_ID,
) -> Match:
    """
    Build a Match instance without touching a real database.
    """

    return Match(
        id=MATCH_ID,
        patient_id=patient_id,
        trial_id=trial_id,
        hospital_id=hospital_id,
        confidence=0.82,
        overall_status="Possibly Eligible",
        explanation="Retrieved criteria were partially satisfied.",
        model_version="gemini-test",
    )


def build_repository(
    query_result,
    list_result=None,
):
    """
    Build a MatchRepository backed by a mocked Session.

    `query_result` backs the .first() terminal call used by
    get_match_by_id. `list_result` backs the .all() terminal call
    used by list_matches_for_patient / list_matches_for_trial.
    """

    db = MagicMock()

    query = MagicMock()
    db.query.return_value = query
    query.filter.return_value = query
    query.order_by.return_value = query
    query.first.return_value = query_result
    query.all.return_value = list_result if list_result is not None else []

    return MatchRepository(db), db, query


def test_table_name_matches_model_convention():
    """
    Guards against table-name drift the same way the existing
    TrialEmbedding repository test does.
    """

    assert Match.__tablename__ == "matches"


def test_create_match_adds_entity_to_session():
    repository, db, _ = build_repository(
        query_result=None,
    )

    match = build_match()

    result = repository.create_match(match)

    assert result is match

    db.add.assert_called_once_with(match)


def test_get_match_by_id_returns_match_when_present():
    match = build_match()

    repository, db, query = build_repository(
        query_result=match,
    )

    result = repository.get_match_by_id(
        match_id=MATCH_ID,
        hospital_id=HOSPITAL_ID,
    )

    assert result is match

    db.query.assert_called_once_with(Match)
    query.filter.assert_called_once()


def test_get_match_by_id_filter_includes_id_and_hospital_id():
    """
    The filter call must reference both Match.id and
    Match.hospital_id. Inspecting the compiled filter expressions
    (rather than only checking the return value) catches a
    regression where hospital_id is accidentally dropped from the
    query even though a superficial "does it return None" test
    would still pass by coincidence.
    """

    repository, db, query = build_repository(
        query_result=None,
    )

    repository.get_match_by_id(
        match_id=MATCH_ID,
        hospital_id=HOSPITAL_ID,
    )

    filter_args = query.filter.call_args[0]
    filter_sql = " ".join(str(arg) for arg in filter_args)

    assert "matches.id" in filter_sql
    assert "matches.hospital_id" in filter_sql


def test_get_match_by_id_returns_none_when_absent():
    repository, db, _ = build_repository(
        query_result=None,
    )

    result = repository.get_match_by_id(
        match_id=MATCH_ID,
        hospital_id=HOSPITAL_ID,
    )

    assert result is None


def test_list_matches_for_patient_filter_includes_patient_and_hospital_id():
    repository, db, query = build_repository(
        query_result=None,
        list_result=[],
    )

    repository.list_matches_for_patient(
        patient_id=PATIENT_ID,
        hospital_id=HOSPITAL_ID,
    )

    filter_args = query.filter.call_args[0]
    filter_sql = " ".join(str(arg) for arg in filter_args)

    assert "matches.patient_id" in filter_sql
    assert "matches.hospital_id" in filter_sql


def test_list_matches_for_patient_returns_matches():
    match = build_match()

    repository, db, _ = build_repository(
        query_result=None,
        list_result=[match],
    )

    result = repository.list_matches_for_patient(
        patient_id=PATIENT_ID,
        hospital_id=HOSPITAL_ID,
    )

    assert result == [match]


def test_list_matches_for_trial_filter_includes_trial_and_hospital_id():
    repository, db, query = build_repository(
        query_result=None,
        list_result=[],
    )

    repository.list_matches_for_trial(
        trial_id=TRIAL_ID,
        hospital_id=HOSPITAL_ID,
    )

    filter_args = query.filter.call_args[0]
    filter_sql = " ".join(str(arg) for arg in filter_args)

    assert "matches.trial_id" in filter_sql
    assert "matches.hospital_id" in filter_sql


def test_list_matches_for_trial_returns_matches():
    match = build_match()

    repository, db, _ = build_repository(
        query_result=None,
        list_result=[match],
    )

    result = repository.list_matches_for_trial(
        trial_id=TRIAL_ID,
        hospital_id=HOSPITAL_ID,
    )

    assert result == [match]


def test_json_list_fields_default_to_empty_list_not_none():
    """
    matched_criteria / failed_criteria / missing_information must
    default to [] rather than None, preserving the existing
    EligibilityResponse convention (default_factory=list, never
    None).

    default=list only fires when SQLAlchemy flushes an object to a
    session (it is not a plain-Python-object-construction default),
    so this is asserted against the actual column configuration
    rather than a bare, unflushed Match() instance — consistent
    with the rest of this test file's no-live-database approach.
    """

    columns = Match.__table__.columns

    for field_name in (
        "matched_criteria",
        "failed_criteria",
        "missing_information",
    ):
        column = columns[field_name]

        assert column.nullable is False

        assert column.default is not None
        assert column.default.is_callable is True

        assert column.server_default is not None
        assert "'[]'::jsonb" in str(
            column.server_default.arg
        )


def test_commit_rollback_refresh_delegate_to_session():
    repository, db, _ = build_repository(
        query_result=None,
    )

    repository.commit()
    db.commit.assert_called_once()

    repository.rollback()
    db.rollback.assert_called_once()

    instance = object()
    repository.refresh(instance)
    db.refresh.assert_called_once_with(instance)
