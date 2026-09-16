from unittest.mock import MagicMock
from uuid import uuid4

from app.models.trial_embedding import TrialEmbedding
from app.repositories.trial_embedding_repository import (
    TrialEmbeddingRepository,
)


TRIAL_ID = uuid4()
EMBEDDING = [0.1] * 384
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def build_repository(existing: TrialEmbedding | None):
    """
    Build a TrialEmbeddingRepository backed by a mocked Session.

    The mocked query().filter().first() chain returns `existing`,
    simulating either "no embedding yet" (None) or "an embedding
    already exists for this trial" (a TrialEmbedding instance).
    """

    db = MagicMock()

    query = MagicMock()
    db.query.return_value = query
    query.filter.return_value = query
    query.first.return_value = existing

    return TrialEmbeddingRepository(db), db


def test_table_name_matches_matching_repository_sql():
    """
    MatchingRepository's raw SQL joins a table literally named
    'trial_embeddings'. If this ever drifts, retrieval silently
    breaks even though the ORM model still "looks" correct.
    """

    assert TrialEmbedding.__tablename__ == "trial_embeddings"


def test_get_by_trial_id_returns_none_when_absent():
    repository, db = build_repository(
        existing=None
    )

    result = repository.get_by_trial_id(
        TRIAL_ID
    )

    assert result is None
    db.query.assert_called_once_with(TrialEmbedding)


def test_upsert_embedding_creates_when_absent():
    """
    First-time embedding for a trial: no existing row, so a new
    TrialEmbedding must be constructed and added to the session.
    """

    repository, db = build_repository(
        existing=None
    )

    result = repository.upsert_embedding(
        trial_id=TRIAL_ID,
        embedding=EMBEDDING,
        model_name=MODEL_NAME,
    )

    assert isinstance(result, TrialEmbedding)
    assert result.trial_id == TRIAL_ID
    assert result.embedding == EMBEDDING
    assert result.model_name == MODEL_NAME

    db.add.assert_called_once()
    added_entity = db.add.call_args[0][0]
    assert added_entity is result


def test_upsert_embedding_updates_in_place_when_present():
    """
    Re-processing a trial (e.g. after an update, or a retried
    Celery task) must update the existing row rather than create
    a second one for the same trial_id.
    """

    existing = TrialEmbedding(
        trial_id=TRIAL_ID,
        embedding=[0.0] * 384,
        model_name="old-model",
    )

    repository, db = build_repository(
        existing=existing
    )

    new_embedding = [0.9] * 384

    result = repository.upsert_embedding(
        trial_id=TRIAL_ID,
        embedding=new_embedding,
        model_name=MODEL_NAME,
    )

    assert result is existing
    assert result.embedding == new_embedding
    assert result.model_name == MODEL_NAME

    # No new row should be created for an existing trial_id.
    db.add.assert_not_called()


def test_repeated_upserts_do_not_duplicate_rows():
    """
    Calling upsert_embedding twice in a row for the same trial_id
    (simulating a retried task or a duplicate matching_service call)
    must never result in more than one db.add() call.
    """

    repository, db = build_repository(
        existing=None
    )

    first = repository.upsert_embedding(
        trial_id=TRIAL_ID,
        embedding=EMBEDDING,
        model_name=MODEL_NAME,
    )

    # Simulate the row now existing on the second call.
    db.query.return_value.filter.return_value.first.return_value = (
        first
    )

    second = repository.upsert_embedding(
        trial_id=TRIAL_ID,
        embedding=[0.5] * 384,
        model_name=MODEL_NAME,
    )

    assert second is first
    db.add.assert_called_once()
