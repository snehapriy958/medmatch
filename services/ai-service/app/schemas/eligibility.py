from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class EligibilityStatus(str, Enum):
    """
    Supported eligibility decisions returned by the language model.
    """

    ELIGIBLE = "Eligible"
    NOT_ELIGIBLE = "Not Eligible"
    POSSIBLY_ELIGIBLE = "Possibly Eligible"


class EligibilityResponse(BaseModel):
    """
    Structured eligibility assessment produced by the language model.
    """

    eligibility: EligibilityStatus = Field(
        description="Final eligibility decision.",
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score for the eligibility decision.",
    )

    matched_criteria: list[str] = Field(
        default_factory=list,
        max_length=50,
        description="Eligibility criteria satisfied by the patient.",
    )

    failed_criteria: list[str] = Field(
        default_factory=list,
        max_length=50,
        description="Eligibility criteria not satisfied or lacking sufficient evidence.",
    )

    reasoning: str = Field(
        min_length=1,
        max_length=3000,
        description="Concise explanation supporting the eligibility decision.",
    )

    model_config = ConfigDict(
        extra="forbid",
    )