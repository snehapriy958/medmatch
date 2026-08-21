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

    trial_ids_evaluated: list[str] = Field(
        default_factory=list,
        max_length=50,
        description="Clinical trial IDs evaluated during eligibility assessment.",
    )

    summary: str = Field(
        default="",
        max_length=1000,
        description="Short clinical summary of the eligibility assessment.",
    )


    matched_inclusion: list[str] = Field(
        default_factory=list,
        max_length=50,
        description="Inclusion criteria satisfied by the patient.",
    )

    failed_inclusion: list[str] = Field(
        default_factory=list,
        max_length=50,
        description="Required inclusion criteria that were not satisfied.",
    )

    satisfied_exclusion: list[str] = Field(
        default_factory=list,
        max_length=50,
        description="Exclusion criteria confirmed to be absent.",
    )

    triggered_exclusion: list[str] = Field(
        default_factory=list,
        max_length=50,
        description="Exclusion criteria present in the patient.",
    )

    missing_information: list[str] = Field(
        default_factory=list,
        max_length=50,
        description="Information required before a final decision can be made.",
    )

    recommendation: str = Field(
        default="",
        max_length=1500,
        description="Recommended next clinical steps.",
    )

    # Keep these for backward compatibility
    matched_criteria: list[str] = Field(
        default_factory=list,
        max_length=50,
        description="Legacy matched criteria.",
    )

    failed_criteria: list[str] = Field(
        default_factory=list,
        max_length=50,
        description="Legacy failed criteria.",
    )

    reasoning: str = Field(
        min_length=1,
        max_length=3000,
        description="Detailed clinical reasoning.",
    )

    model_config = ConfigDict(
        extra="forbid",
    )

class EligibilityEvaluationResponse(BaseModel):
    """
    Collection of independent eligibility assessments,
    one for each evaluated clinical trial.
    """

    results: list[EligibilityResponse] = Field(
        default_factory=list,
        description="Independent eligibility assessment for each evaluated trial.",
    )

    model_config = ConfigDict(
        extra="forbid",
    )