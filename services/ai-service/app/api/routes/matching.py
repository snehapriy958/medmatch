from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from app.api.deps import (
    get_current_hospital_id,
    get_matching_service,
    require_admin_or_doctor,
    require_roles,
)
from app.config.rate_limit import limiter
from app.config.settings import settings
from app.schemas import MatchingResponse
from app.schemas.eligibility import EligibilityResponse
from app.services.matching_service import MatchingService


class MatchingRequest(BaseModel):
    patient_note: str = Field(
        description="Clinical note used for semantic trial matching.",
    )

    limit: int = Field(
        default=settings.TOP_K_RESULTS,
        ge=1,
        le=100,
        description="Maximum number of criteria to retrieve.",
    )


router = APIRouter(
    prefix=f"{settings.API_PREFIX}/matching",
    tags=["Matching"],
)


@router.post(
    "/search",
    response_model=MatchingResponse,
)
@limiter.limit("30/minute")
def search_matching_trials(
    request: Request,
    body: MatchingRequest,
    _: Annotated[
        dict[str, Any],
        Depends(require_roles("ADMIN", "DOCTOR", "RESEARCHER")),
    ],
    service: Annotated[
        MatchingService,
        Depends(get_matching_service),
    ],
    hospital_id: Annotated[
        UUID,
        Depends(get_current_hospital_id),
    ],
) -> MatchingResponse:
    """
    Search for the most similar trial criteria.
    """

    return service.find_matching_criteria(
        patient_note=body.patient_note,
        hospital_id=hospital_id,
        limit=body.limit,
    )


@router.post(
    "/evaluate",
    response_model=EligibilityResponse,
)
@limiter.limit("20/minute")
def evaluate_patient_eligibility(
    request: Request,
    body: MatchingRequest,
    _: Annotated[
        dict[str, Any],
        Depends(require_admin_or_doctor()),
    ],
    service: Annotated[
        MatchingService,
        Depends(get_matching_service),
    ],
    hospital_id: Annotated[
        UUID,
        Depends(get_current_hospital_id),
    ],
) -> EligibilityResponse:
    """
    Evaluate a patient's eligibility for a clinical trial using
    semantic retrieval followed by LLM reasoning.
    """

    return service.evaluate_eligibility(
        patient_note=body.patient_note,
        hospital_id=hospital_id,
        limit=body.limit,
    )