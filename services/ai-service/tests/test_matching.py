from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest

from app.schemas.eligibility import (
    EligibilityResponse,
    EligibilityStatus,
)
from app.services.matching_service import MatchingService


HOSPITAL_ID = uuid4()
USER_ID = uuid4()
TRIAL_ID_1 = uuid4()
TRIAL_ID_2 = uuid4()


def build_service():
    repository = Mock()
    trial_criteria_repository = Mock()
    hospital_repository = Mock()
    embedding_service = Mock()
    llm_service = Mock()
    audit_service = Mock()

    service = MatchingService(
        repository=repository,
        trial_criteria_repository=(
            trial_criteria_repository
        ),
        hospital_repository=(
            hospital_repository
        ),
        embedding_service=embedding_service,
        llm_service=llm_service,
        audit_service=audit_service,
    )

    return (
        service,
        repository,
        trial_criteria_repository,
        hospital_repository,
        embedding_service,
        llm_service,
        audit_service,
    )


def build_current_user():
    return {
        "sub": str(USER_ID),
        "email": "admin@test.com",
        "role": "ADMIN",
        "hospital_id": str(HOSPITAL_ID),
    }


def build_retrieved_criterion(
    trial_id,
    distance=0.1,
):
    return {
        "trial_id": trial_id,
        "distance": distance,
        "title": "Test Clinical Trial",
        "condition": "Type 2 Diabetes",
        "phase": "Phase 2",
        "status": "Recruiting",
        "brief_summary": "Test trial summary.",
    }


def build_complete_criterion(
    trial_id,
    criteria_type="Inclusion",
    description="Patient must have Type 2 Diabetes.",
):
    criterion = Mock()

    criterion.id = uuid4()
    criterion.trial_id = trial_id
    criterion.criteria_type = criteria_type
    criterion.description = description

    return criterion


def build_eligibility_result(
    trial_id,
    eligibility=EligibilityStatus.POSSIBLY_ELIGIBLE,
):
    return EligibilityResponse(
        eligibility=eligibility,
        confidence=0.8,
        trial_ids_evaluated=[
            str(trial_id)
        ],
        summary="Test eligibility evaluation.",
        matched_inclusion=[
            "Test inclusion criterion."
        ],
        failed_inclusion=[],
        satisfied_exclusion=[],
        triggered_exclusion=[],
        missing_information=[],
        recommendation="Review clinical details.",
        matched_criteria=[],
        failed_criteria=[],
        reasoning="Test reasoning.",
    )


def test_evaluate_eligibility_rejects_empty_patient_note():
    (
        service,
        _,
        _,
        _,
        _,
        _,
        _,
    ) = build_service()

    with pytest.raises(
        ValueError,
        match="Patient note cannot be empty.",
    ):
        service.evaluate_eligibility(
            patient_note="   ",
            hospital_id=HOSPITAL_ID,
            current_user=build_current_user(),
        )


def test_evaluate_eligibility_returns_safe_abstention_when_no_trials_retrieved(
    monkeypatch,
):
    (
        service,
        _,
        _,
        _,
        _,
        llm_service,
        _,
    ) = build_service()

    monkeypatch.setattr(
        service,
        "_retrieve_matching_criteria",
        Mock(return_value=[]),
    )

    response = service.evaluate_eligibility(
        patient_note=(
            "35-year-old patient with a wrist fracture "
            "following a sports injury."
        ),
        hospital_id=HOSPITAL_ID,
        current_user=build_current_user(),
    )

    assert len(response.results) == 1

    result = response.results[0]

    assert (
        result.eligibility
        == EligibilityStatus.POSSIBLY_ELIGIBLE
    )

    assert result.confidence == 0.0

    assert result.trial_ids_evaluated == []

    llm_service.evaluate_eligibility.assert_not_called()


def test_evaluate_eligibility_returns_valid_llm_results(
    monkeypatch,
):
    (
        service,
        _,
        _,
        _,
        _,
        llm_service,
        _,
    ) = build_service()

    retrieved_criteria = [
        build_retrieved_criterion(
            TRIAL_ID_1
        ),
    ]

    complete_criteria = [
        {
            "id": str(uuid4()),
            "trial_id": str(TRIAL_ID_1),
            "criteria_type": "Inclusion",
            "description": (
                "Patient must have Type 2 Diabetes."
            ),
        }
    ]

    monkeypatch.setattr(
        service,
        "_retrieve_matching_criteria",
        Mock(
            return_value=retrieved_criteria
        ),
    )

    monkeypatch.setattr(
        service,
        "_get_complete_trial_criteria",
        Mock(
            return_value=complete_criteria
        ),
    )

    valid_result = build_eligibility_result(
        TRIAL_ID_1
    )

    llm_service.evaluate_eligibility.return_value = [
        valid_result
    ]

    response = service.evaluate_eligibility(
        patient_note=(
            "54-year-old patient diagnosed with "
            "Type 2 Diabetes."
        ),
        hospital_id=HOSPITAL_ID,
        current_user=build_current_user(),
    )

    assert len(response.results) == 1

    assert (
        response.results[0].trial_ids_evaluated
        == [str(TRIAL_ID_1)]
    )

    assert (
        response.results[0].eligibility
        == EligibilityStatus.POSSIBLY_ELIGIBLE
    )

    llm_service.evaluate_eligibility.assert_called_once()


def test_evaluate_eligibility_returns_safe_abstention_for_unexpected_trial(
    monkeypatch,
):
    (
        service,
        _,
        _,
        _,
        _,
        llm_service,
        _,
    ) = build_service()

    unexpected_trial_id = uuid4()

    retrieved_criteria = [
        build_retrieved_criterion(
            TRIAL_ID_1
        ),
    ]

    complete_criteria = [
        {
            "id": str(uuid4()),
            "trial_id": str(TRIAL_ID_1),
            "criteria_type": "Inclusion",
            "description": (
                "Patient must have Type 2 Diabetes."
            ),
        }
    ]

    monkeypatch.setattr(
        service,
        "_retrieve_matching_criteria",
        Mock(
            return_value=retrieved_criteria
        ),
    )

    monkeypatch.setattr(
        service,
        "_get_complete_trial_criteria",
        Mock(
            return_value=complete_criteria
        ),
    )

    llm_service.evaluate_eligibility.return_value = [
        build_eligibility_result(
            unexpected_trial_id
        )
    ]

    response = service.evaluate_eligibility(
        patient_note=(
            "Patient has Type 2 Diabetes."
        ),
        hospital_id=HOSPITAL_ID,
        current_user=build_current_user(),
    )

    assert len(response.results) == 1

    result = response.results[0]

    assert (
        result.eligibility
        == EligibilityStatus.POSSIBLY_ELIGIBLE
    )

    assert result.confidence == 0.0

    assert result.trial_ids_evaluated == []


def test_evaluate_eligibility_returns_safe_abstention_for_duplicate_trials(
    monkeypatch,
):
    (
        service,
        _,
        _,
        _,
        _,
        llm_service,
        _,
    ) = build_service()

    retrieved_criteria = [
        build_retrieved_criterion(
            TRIAL_ID_1
        ),
    ]

    complete_criteria = [
        {
            "id": str(uuid4()),
            "trial_id": str(TRIAL_ID_1),
            "criteria_type": "Inclusion",
            "description": (
                "Patient must have Type 2 Diabetes."
            ),
        }
    ]

    monkeypatch.setattr(
        service,
        "_retrieve_matching_criteria",
        Mock(
            return_value=retrieved_criteria
        ),
    )

    monkeypatch.setattr(
        service,
        "_get_complete_trial_criteria",
        Mock(
            return_value=complete_criteria
        ),
    )

    llm_service.evaluate_eligibility.return_value = [
        build_eligibility_result(
            TRIAL_ID_1
        ),
        build_eligibility_result(
            TRIAL_ID_1
        ),
    ]

    response = service.evaluate_eligibility(
        patient_note=(
            "Patient has Type 2 Diabetes."
        ),
        hospital_id=HOSPITAL_ID,
        current_user=build_current_user(),
    )

    assert len(response.results) == 1

    result = response.results[0]

    assert (
        result.eligibility
        == EligibilityStatus.POSSIBLY_ELIGIBLE
    )

    assert result.confidence == 0.0

    assert result.trial_ids_evaluated == []


def test_evaluate_eligibility_returns_safe_abstention_for_missing_trial(
    monkeypatch,
):
    (
        service,
        _,
        _,
        _,
        _,
        llm_service,
        _,
    ) = build_service()

    retrieved_criteria = [
        build_retrieved_criterion(
            TRIAL_ID_1
        ),
        build_retrieved_criterion(
            TRIAL_ID_2
        ),
    ]

    complete_criteria = [
        {
            "id": str(uuid4()),
            "trial_id": str(TRIAL_ID_1),
            "criteria_type": "Inclusion",
            "description": "First trial criterion.",
        },
        {
            "id": str(uuid4()),
            "trial_id": str(TRIAL_ID_2),
            "criteria_type": "Inclusion",
            "description": "Second trial criterion.",
        },
    ]

    monkeypatch.setattr(
        service,
        "_retrieve_matching_criteria",
        Mock(
            return_value=retrieved_criteria
        ),
    )

    monkeypatch.setattr(
        service,
        "_get_complete_trial_criteria",
        Mock(
            return_value=complete_criteria
        ),
    )

    llm_service.evaluate_eligibility.return_value = [
        build_eligibility_result(
            TRIAL_ID_1
        )
    ]

    response = service.evaluate_eligibility(
        patient_note=(
            "Patient has Type 2 Diabetes."
        ),
        hospital_id=HOSPITAL_ID,
        current_user=build_current_user(),
    )

    assert len(response.results) == 1

    result = response.results[0]

    assert (
        result.eligibility
        == EligibilityStatus.POSSIBLY_ELIGIBLE
    )

    assert result.confidence == 0.0

    assert result.trial_ids_evaluated == []