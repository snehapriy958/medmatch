from uuid import uuid4

import pytest

from app.services.matching_service import MatchingService


def make_current_user(
    hospital_id: str,
) -> dict:
    return {
        "sub": str(uuid4()),
        "email": "researcher@example.com",
        "role": "RESEARCHER",
        "hospital_id": hospital_id,
    }


def make_service() -> MatchingService:
    return MatchingService.__new__(
        MatchingService
    )


def test_validate_user_hospital_allows_matching_hospital():
    hospital_id = uuid4()

    service = make_service()

    current_user = make_current_user(
        str(hospital_id)
    )

    result = service._validate_user_hospital(
        hospital_id=hospital_id,
        current_user=current_user,
    )

    assert result == hospital_id


def test_validate_user_hospital_rejects_different_hospital():
    service = make_service()

    requested_hospital_id = uuid4()

    current_user = make_current_user(
        str(uuid4())
    )

    with pytest.raises(
        ValueError,
        match="Hospital access mismatch",
    ):
        service._validate_user_hospital(
            hospital_id=requested_hospital_id,
            current_user=current_user,
        )


def test_validate_user_hospital_rejects_missing_hospital_id():
    service = make_service()

    current_user = {
        "sub": str(uuid4()),
        "email": "researcher@example.com",
        "role": "RESEARCHER",
    }

    with pytest.raises(
        ValueError,
        match="Current user does not contain a valid hospital ID",
    ):
        service._validate_user_hospital(
            hospital_id=uuid4(),
            current_user=current_user,
        )


def test_validate_user_hospital_rejects_invalid_hospital_id():
    service = make_service()

    current_user = make_current_user(
        "not-a-valid-uuid"
    )

    with pytest.raises(
        ValueError,
        match="Current user does not contain a valid hospital ID",
    ):
        service._validate_user_hospital(
            hospital_id=uuid4(),
            current_user=current_user,
        )


def test_validate_user_hospital_rejects_none_hospital_id():
    service = make_service()

    current_user = make_current_user(
        None
    )

    with pytest.raises(
        ValueError,
        match="Current user does not contain a valid hospital ID",
    ):
        service._validate_user_hospital(
            hospital_id=uuid4(),
            current_user=current_user,
        )