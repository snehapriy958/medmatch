from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
)


CriterionText = Annotated[
    str,
    StringConstraints(
        min_length=1,
        max_length=2000,
    ),
]


class TrialExtraction(BaseModel):
    """
    Structured information extracted from a clinical trial protocol.
    """

    title: str = Field(
        default="",
        min_length=1,
        max_length=500,
        description="Official title of the clinical trial.",
    )

    phase: str = Field(
        default="",
        max_length=100,
        description="Clinical trial phase (e.g. Phase I, Phase II).",
    )

    condition: str = Field(
        default="",
        max_length=255,
        description="Disease or medical condition under study.",
    )

    sponsor: str = Field(
        default="",
        max_length=255,
        description="Organization sponsoring the trial.",
    )

    recruitment_status: str = Field(
        default="",
        max_length=100,
        description="Current recruitment status.",
    )

    inclusion_criteria: list[CriterionText] = Field(
        default_factory=list,
        max_length=100,
        description="List of inclusion criteria.",
    )

    exclusion_criteria: list[CriterionText] = Field(
        default_factory=list,
        max_length=100,
        description="List of exclusion criteria.",
    )

    model_config = ConfigDict(
        extra="forbid",
    )