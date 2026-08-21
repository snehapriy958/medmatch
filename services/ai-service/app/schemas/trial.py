from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TrialCreate(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=500,
        description="Clinical trial title.",
    )

    brief_summary: str | None = Field(
        default=None,
        max_length=5000,
        description="Short summary of the clinical trial.",
    )

    condition: str | None = Field(
        default=None,
        max_length=255,
        description="Medical condition targeted by the trial.",
    )

    phase: str | None = Field(
        default=None,
        max_length=100,
        description="Clinical trial phase.",
    )

    status: str | None = Field(
        default=None,
        max_length=100,
        description="Recruitment status of the trial.",
    )

class TrialUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=500,
        description="Clinical trial title.",
    )

    brief_summary: str | None = Field(
        default=None,
        max_length=5000,
        description="Short summary of the clinical trial.",
    )

    condition: str | None = Field(
        default=None,
        max_length=255,
        description="Medical condition targeted by the trial.",
    )

    phase: str | None = Field(
        default=None,
        max_length=100,
        description="Clinical trial phase.",
    )

    status: str | None = Field(
        default=None,
        max_length=100,
        description="Recruitment status of the trial.",
    )


class CriterionResponse(BaseModel):
    id: UUID

    criteria_type: str = Field(
        max_length=50,
    )

    description: str = Field(
        min_length=1,
        max_length=2000,
    )

    model_config = ConfigDict(
        from_attributes=True,
    )


class TrialMetadata(BaseModel):
    id: UUID

    title: str

    condition: str | None

    phase: str | None

    status: str | None

    model_config = ConfigDict(
        from_attributes=True,
    )


class TrialResponse(BaseModel):
    id: UUID

    title: str

    brief_summary: str | None

    condition: str | None

    phase: str | None

    status: str | None

    created_at: datetime

    updated_at: datetime

    criteria: list[CriterionResponse] = Field(
        default_factory=list,
        max_length=200,
    )

    model_config = ConfigDict(
        from_attributes=True,
    )