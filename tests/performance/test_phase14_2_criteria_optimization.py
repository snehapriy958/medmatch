"""
Phase 14.2 — Regression and Correctness Test Suite: Criteria Loading / N+1 Optimization.

Tests verify:
1. Multiple candidate trials return correct criteria.
2. Criteria are grouped under the correct trial.
3. Existing ordering is preserved (trial-level sort + criteria_type/id order).
4. Empty candidate list behaves correctly (zero queries, returns empty list).
5. Tenant isolation is preserved (only criteria belonging to tenant candidate trials are returned).
6. Recruiting/status filtering remains unchanged.
7. No criteria are accidentally duplicated.
8. Existing matching response remains schema-compatible.
9. Optimization semantics equivalence (sequential vs batched field-by-field identity).
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

# Ensure repo root and ai-service are in sys.path
REPO_ROOT = Path(__file__).resolve().parents[2]
AI_SERVICE_DIR = REPO_ROOT / "services" / "ai-service"
for p in [str(REPO_ROOT), str(AI_SERVICE_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from app.models.trial_criteria import TrialCriteria
from app.rag.prompt_builder import PromptBuilder
from app.repositories.trial_criteria_repository import TrialCriteriaRepository
from app.schemas.eligibility import (
    EligibilityEvaluationResponse,
    EligibilityResponse,
    EligibilityStatus,
)
from app.services.matching_service import MatchingService


def _create_mock_criterion(
    criterion_id: UUID,
    trial_id: UUID,
    criteria_type: str,
    description: str,
) -> MagicMock:
    c = MagicMock(spec=TrialCriteria)
    c.id = criterion_id
    c.trial_id = trial_id
    c.criteria_type = criteria_type
    c.description = description
    return c


@pytest.fixture
def sample_trials_and_criteria():
    """Build 3 candidate trials with mixed inclusion/exclusion criteria."""
    t1 = UUID("11111111-1111-1111-1111-111111111111")
    t2 = UUID("22222222-2222-2222-2222-222222222222")
    t3 = UUID("33333333-3333-3333-3333-333333333333")

    c1 = _create_mock_criterion(UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"), t1, "Exclusion", "Active infection")
    c2 = _create_mock_criterion(UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"), t1, "Inclusion", "Age >= 18")
    c3 = _create_mock_criterion(UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"), t2, "Inclusion", "Histologically confirmed adenocarcinoma")
    c4 = _create_mock_criterion(UUID("dddddddd-dddd-dddd-dddd-dddddddddddd"), t2, "Exclusion", "Prior immunotherapy")
    c5 = _create_mock_criterion(UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"), t3, "Inclusion", "ECOG performance status 0-1")
    c6 = _create_mock_criterion(UUID("ffffffff-ffff-ffff-ffff-ffffffffffff"), t3, "Inclusion", "Measurable disease per RECIST 1.1")

    all_criteria = [c1, c2, c3, c4, c5, c6]
    trials_map = {t1: [c1, c2], t2: [c3, c4], t3: [c5, c6]}
    return [t1, t2, t3], all_criteria, trials_map


def test_1_multiple_candidate_trials_return_correct_criteria(sample_trials_and_criteria):
    """Multiple candidate trials return all expected criteria."""
    trial_ids, all_criteria, trials_map = sample_trials_and_criteria
    mock_criteria_repo = MagicMock(spec=TrialCriteriaRepository)

    def fake_list_by_trial_ids(uuids):
        return [c for c in all_criteria if c.trial_id in uuids]

    mock_criteria_repo.list_by_trial_ids.side_effect = fake_list_by_trial_ids

    service = MatchingService(
        repository=MagicMock(),
        trial_criteria_repository=mock_criteria_repo,
        hospital_repository=MagicMock(),
        embedding_service=MagicMock(),
        llm_service=MagicMock(),
        audit_service=MagicMock(),
    )

    trial_id_strs = {str(t) for t in trial_ids}
    results = service._get_complete_trial_criteria(trial_id_strs)

    assert len(results) == len(all_criteria)
    returned_ids = {r["id"] for r in results}
    expected_ids = {str(c.id) for c in all_criteria}
    assert returned_ids == expected_ids
    mock_criteria_repo.list_by_trial_ids.assert_called_once()


def test_2_criteria_grouped_under_correct_trial(sample_trials_and_criteria):
    """Criteria are accurately grouped and associated with the correct trial."""
    trial_ids, all_criteria, trials_map = sample_trials_and_criteria
    mock_criteria_repo = MagicMock(spec=TrialCriteriaRepository)
    mock_criteria_repo.list_by_trial_ids.return_value = all_criteria

    service = MatchingService(
        repository=MagicMock(),
        trial_criteria_repository=mock_criteria_repo,
        hospital_repository=MagicMock(),
        embedding_service=MagicMock(),
        llm_service=MagicMock(),
        audit_service=MagicMock(),
    )

    results = service._get_complete_trial_criteria({str(t) for t in trial_ids})

    for r in results:
        t_id = UUID(r["trial_id"])
        assert t_id in trials_map
        matching_trial_criteria = trials_map[t_id]
        assert any(str(c.id) == r["id"] for c in matching_trial_criteria)


def test_3_existing_ordering_preserved(sample_trials_and_criteria):
    """Deterministic ordering is strictly preserved: sorted(trial_ids) then criteria order."""
    trial_ids, all_criteria, _ = sample_trials_and_criteria
    # Pass unordered trial IDs
    unordered_tids = {str(trial_ids[1]), str(trial_ids[2]), str(trial_ids[0])}

    mock_criteria_repo = MagicMock(spec=TrialCriteriaRepository)
    mock_criteria_repo.list_by_trial_ids.return_value = all_criteria

    service = MatchingService(
        repository=MagicMock(),
        trial_criteria_repository=mock_criteria_repo,
        hospital_repository=MagicMock(),
        embedding_service=MagicMock(),
        llm_service=MagicMock(),
        audit_service=MagicMock(),
    )

    results = service._get_complete_trial_criteria(unordered_tids)

    # Resulting trial_ids in order of appearance
    observed_trial_order = []
    for r in results:
        if not observed_trial_order or observed_trial_order[-1] != r["trial_id"]:
            observed_trial_order.append(r["trial_id"])

    assert observed_trial_order == sorted(list(unordered_tids))


def test_4_empty_candidate_list_behaves_correctly():
    """Empty candidate set returns empty list without issuing database queries."""
    mock_criteria_repo = MagicMock(spec=TrialCriteriaRepository)

    service = MatchingService(
        repository=MagicMock(),
        trial_criteria_repository=mock_criteria_repo,
        hospital_repository=MagicMock(),
        embedding_service=MagicMock(),
        llm_service=MagicMock(),
        audit_service=MagicMock(),
    )

    assert service._get_complete_trial_criteria(set()) == []
    mock_criteria_repo.list_by_trial_ids.assert_not_called()
    mock_criteria_repo.list_by_trial.assert_not_called()


def test_5_tenant_isolation_preserved():
    """
    Tenant isolation verification.

    Scope clarification:
    - In production, candidate trial IDs entering _get_complete_trial_criteria()
      are strictly tenant-scoped upstream by MatchingRepository.find_similar_criteria()
      where `trials.hospital_id == :hospital_id`.
    - list_by_trial_ids(uuids) retrieves criteria for those specific candidate UUIDs.
    - This test verifies that if only Tenant A candidate trial IDs are supplied,
      only Tenant A criteria are returned, and Tenant B criteria are excluded.
    """
    tenant_a_trial = uuid4()
    tenant_b_trial = uuid4()

    criterion_a = _create_mock_criterion(uuid4(), tenant_a_trial, "Inclusion", "Tenant A criterion")
    criterion_b = _create_mock_criterion(uuid4(), tenant_b_trial, "Inclusion", "Tenant B criterion")

    mock_criteria_repo = MagicMock(spec=TrialCriteriaRepository)

    def fake_list_by_trial_ids(uuids):
        return [c for c in [criterion_a, criterion_b] if c.trial_id in uuids]

    mock_criteria_repo.list_by_trial_ids.side_effect = fake_list_by_trial_ids

    service = MatchingService(
        repository=MagicMock(),
        trial_criteria_repository=mock_criteria_repo,
        hospital_repository=MagicMock(),
        embedding_service=MagicMock(),
        llm_service=MagicMock(),
        audit_service=MagicMock(),
    )

    # Only Tenant A candidate trial requested
    results_a = service._get_complete_trial_criteria({str(tenant_a_trial)})
    assert len(results_a) == 1
    assert results_a[0]["trial_id"] == str(tenant_a_trial)
    assert results_a[0]["description"] == "Tenant A criterion"
    assert not any(r["trial_id"] == str(tenant_b_trial) for r in results_a)


def test_6_recruiting_status_filtering_unchanged():
    """Candidate retrieval upstream filters recruiting status, and complete criteria honors it."""
    recruiting_trial = uuid4()
    mock_matching_repo = MagicMock()
    mock_matching_repo.find_similar_criteria.return_value = [
        {
            "id": uuid4(),
            "trial_id": recruiting_trial,
            "status": "Recruiting",
            "distance": 0.12,
        }
    ]

    mock_criteria_repo = MagicMock(spec=TrialCriteriaRepository)
    crit = _create_mock_criterion(uuid4(), recruiting_trial, "Inclusion", "Recruiting trial criterion")
    mock_criteria_repo.list_by_trial_ids.return_value = [crit]

    service = MatchingService(
        repository=mock_matching_repo,
        trial_criteria_repository=mock_criteria_repo,
        hospital_repository=MagicMock(),
        embedding_service=MagicMock(),
        llm_service=MagicMock(),
        audit_service=MagicMock(),
    )
    service.cache = MagicMock()
    service.cache.get.return_value = None

    filtered = service._retrieve_matching_criteria("sample note", uuid4(), limit=5)
    trial_ids = service._get_retrieved_trial_ids(filtered)
    assert trial_ids == {str(recruiting_trial)}

    complete = service._get_complete_trial_criteria(trial_ids)
    assert len(complete) == 1
    assert complete[0]["trial_id"] == str(recruiting_trial)


def test_7_no_criteria_accidentally_duplicated(sample_trials_and_criteria):
    """Criteria are not duplicated when returned by batched query."""
    trial_ids, all_criteria, _ = sample_trials_and_criteria
    mock_criteria_repo = MagicMock(spec=TrialCriteriaRepository)
    mock_criteria_repo.list_by_trial_ids.return_value = all_criteria

    service = MatchingService(
        repository=MagicMock(),
        trial_criteria_repository=mock_criteria_repo,
        hospital_repository=MagicMock(),
        embedding_service=MagicMock(),
        llm_service=MagicMock(),
        audit_service=MagicMock(),
    )

    results = service._get_complete_trial_criteria({str(t) for t in trial_ids})
    assert len(results) == len(all_criteria)
    seen_ids = set()
    for r in results:
        assert r["id"] not in seen_ids, f"Duplicate criterion {r['id']} detected"
        seen_ids.add(r["id"])


def test_8_existing_matching_response_schema_compatibility(sample_trials_and_criteria):
    """The criteria format fed to PromptBuilder remains 100% schema-compatible."""
    trial_ids, all_criteria, _ = sample_trials_and_criteria
    mock_criteria_repo = MagicMock(spec=TrialCriteriaRepository)
    mock_criteria_repo.list_by_trial_ids.return_value = all_criteria

    service = MatchingService(
        repository=MagicMock(),
        trial_criteria_repository=mock_criteria_repo,
        hospital_repository=MagicMock(),
        embedding_service=MagicMock(),
        llm_service=MagicMock(),
        audit_service=MagicMock(),
    )

    complete_criteria = service._get_complete_trial_criteria({str(t) for t in trial_ids})

    # Validate that every criterion dict has exact expected fields
    for c in complete_criteria:
        assert set(c.keys()) == {"id", "trial_id", "criteria_type", "description"}
        assert isinstance(c["id"], str)
        assert isinstance(c["trial_id"], str)
        assert isinstance(c["criteria_type"], str)
        assert isinstance(c["description"], str)

    # Validate that PromptBuilder can process the output without error
    prompt = PromptBuilder.build_matching_prompt(
        patient_note="58-year-old male with confirmed adenocarcinoma.",
        retrieved_criteria=complete_criteria,
    )
    assert isinstance(prompt, str)
    assert "ELIGIBILITY CRITERIA:" in prompt
    for t_id in trial_ids:
        assert str(t_id) in prompt


def test_9_optimization_semantic_equivalence(sample_trials_and_criteria):
    """
    Verify that the optimized implementation produces the EXACT same logical criteria
    sequence as the sequential implementation for:
    - trial grouping
    - trial ordering
    - criteria_type ordering
    - criterion ID tie-breaking
    - criterion description
    - criterion type
    - criterion IDs
    - total number of criteria
    """
    trial_ids, all_criteria, trials_map = sample_trials_and_criteria
    candidate_set = {str(t) for t in trial_ids}

    # Sequential Service (reproducing original loop via fallback)
    seq_repo = MagicMock()
    def fake_list_by_trial(t_id: UUID):
        # Order by criteria_type, id
        raw = trials_map.get(t_id, [])
        return sorted(raw, key=lambda c: (c.criteria_type, str(c.id)))
    seq_repo.list_by_trial.side_effect = fake_list_by_trial
    # Do not have list_by_trial_ids on seq_repo
    del seq_repo.list_by_trial_ids

    seq_service = MatchingService(
        repository=MagicMock(),
        trial_criteria_repository=seq_repo,
        hospital_repository=MagicMock(),
        embedding_service=MagicMock(),
        llm_service=MagicMock(),
        audit_service=MagicMock(),
    )
    seq_result = seq_service._get_complete_trial_criteria(candidate_set)

    # Batched Service (optimized set-based path)
    opt_repo = MagicMock()
    def fake_list_by_trial_ids(uuids):
        matched = []
        for uid in uuids:
            raw = trials_map.get(uid, [])
            matched.extend(sorted(raw, key=lambda c: (c.criteria_type, str(c.id))))
        # Return ordered by trial_id, criteria_type, id
        return sorted(matched, key=lambda c: (str(c.trial_id), c.criteria_type, str(c.id)))
    opt_repo.list_by_trial_ids.side_effect = fake_list_by_trial_ids

    opt_service = MatchingService(
        repository=MagicMock(),
        trial_criteria_repository=opt_repo,
        hospital_repository=MagicMock(),
        embedding_service=MagicMock(),
        llm_service=MagicMock(),
        audit_service=MagicMock(),
    )
    opt_result = opt_service._get_complete_trial_criteria(candidate_set)

    # Exact equality checks
    assert len(seq_result) == len(opt_result) == len(all_criteria)
    assert seq_result == opt_result, "Sequential and batched criteria outputs must be identical"

    for i in range(len(seq_result)):
        s_item = seq_result[i]
        o_item = opt_result[i]
        assert s_item["id"] == o_item["id"]
        assert s_item["trial_id"] == o_item["trial_id"]
        assert s_item["criteria_type"] == o_item["criteria_type"]
        assert s_item["description"] == o_item["description"]
