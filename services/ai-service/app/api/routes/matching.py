from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict, Field

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
        min_length=20,
        max_length=10000,
        description="Clinical note used for semantic trial matching.",
        examples=[
            (
                "54-year-old male with Stage II colon cancer. "
                "Completed surgery. ECOG 0. "
                "No liver disease. Creatinine normal."
            )
        ],
    )

    limit: int = Field(
        default=settings.TOP_K_RESULTS,
        ge=1,
        le=100,
        description="Maximum number of criteria to retrieve.",
        examples=[10],
    )

    model_config = ConfigDict(
        extra="forbid",
    )


router = APIRouter(
    prefix=f"{settings.API_PREFIX}/matching",
    tags=["Matching"],
)


@router.post(
    "/search",
    response_model=MatchingResponse,
    summary="Semantic Trial Search",
    description=(
        "Retrieve the most relevant clinical trial "
        "criteria using vector similarity search."
    ),
)
@limiter.limit(settings.SEARCH_RATE_LIMIT)
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
    summary="Evaluate Clinical Trial Eligibility",
    description=(
        "Evaluate patient eligibility using semantic "
        "retrieval followed by Gemini reasoning."
    ),
)
@limiter.limit(settings.EVALUATE_RATE_LIMIT)
def evaluate_patient_eligibility(
    request: Request,
    body: MatchingRequest,
    current_user: Annotated[
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
        current_user=current_user,
        limit=body.limit,
    )