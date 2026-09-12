from unittest.mock import Mock

import pytest

from app.exceptions.llm import (
    InvalidLLMResponseError,
)
from app.schemas.eligibility import (
    EligibilityResponse,
)
from app.services.llm_service import LLMService


def make_service() -> LLMService:
    return LLMService.__new__(
        LLMService
    )


def valid_result(
    trial_id: str,
) -> dict:
    return {
        "eligibility": "Possibly Eligible",
        "confidence": 0.75,
        "trial_ids_evaluated": [
            trial_id
        ],
        "summary": (
            "Patient may meet eligibility criteria."
        ),
        "matched_inclusion": [],
        "failed_inclusion": [],
        "satisfied_exclusion": [],
        "triggered_exclusion": [],
        "missing_information": [
            "Additional laboratory information."
        ],
        "recommendation": (
            "Review additional clinical information."
        ),
        "matched_criteria": [],
        "failed_criteria": [],
        "reasoning": (
            "Available information is insufficient "
            "for a definitive eligibility decision."
        ),
    }


def test_evaluate_eligibility_returns_valid_result():
    service = make_service()

    trial_id = (
        "11111111-1111-1111-1111-111111111111"
    )

    service._generate_raw_json = Mock(
        return_value=[
            valid_result(trial_id)
        ]
    )

    results = service.evaluate_eligibility(
        prompt="Test prompt"
    )

    assert len(results) == 1

    assert isinstance(
        results[0],
        EligibilityResponse,
    )

    assert (
        results[0].trial_ids_evaluated
        == [trial_id]
    )


def test_evaluate_eligibility_rejects_non_list_response():
    service = make_service()

    service._generate_raw_json = Mock(
        return_value={
            "eligibility": "Eligible"
        }
    )

    with pytest.raises(
        InvalidLLMResponseError,
        match="Expected a JSON array",
    ):
        service.evaluate_eligibility(
            prompt="Test prompt"
        )


def test_evaluate_eligibility_rejects_empty_list():
    service = make_service()

    service._generate_raw_json = Mock(
        return_value=[]
    )

    with pytest.raises(
        InvalidLLMResponseError,
        match="no eligibility evaluations",
    ):
        service.evaluate_eligibility(
            prompt="Test prompt"
        )


def test_evaluate_eligibility_rejects_non_object_item():
    service = make_service()

    service._generate_raw_json = Mock(
        return_value=[
            "invalid result"
        ]
    )

    with pytest.raises(
        InvalidLLMResponseError,
        match="invalid eligibility result",
    ):
        service.evaluate_eligibility(
            prompt="Test prompt"
        )


def test_evaluate_eligibility_rejects_multiple_trial_ids():
    service = make_service()

    result = valid_result(
        "11111111-1111-1111-1111-111111111111"
    )

    result["trial_ids_evaluated"] = [
        "11111111-1111-1111-1111-111111111111",
        "22222222-2222-2222-2222-222222222222",
    ]

    service._generate_raw_json = Mock(
        return_value=[result]
    )

    with pytest.raises(
        InvalidLLMResponseError,
        match="exactly one clinical trial",
    ):
        service.evaluate_eligibility(
            prompt="Test prompt"
        )


def test_evaluate_eligibility_rejects_invalid_schema():
    service = make_service()

    invalid_result = {
        "eligibility": "Possibly Eligible",
        "confidence": 2.0,
        "trial_ids_evaluated": [
            "11111111-1111-1111-1111-111111111111"
        ],
        "reasoning": "Invalid confidence score.",
    }

    service._generate_raw_json = Mock(
        return_value=[
            invalid_result
        ]
    )

    with pytest.raises(
        InvalidLLMResponseError,
        match="invalid eligibility result",
    ):
        service.evaluate_eligibility(
            prompt="Test prompt"
        )