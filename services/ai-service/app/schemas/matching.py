from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MatchingResult(BaseModel):
    """
    Single semantic search result.
    """

    id: UUID

    trial_id: UUID

    title: str

    condition: str | None = None

    phase: str | None = None

    status: str | None = None

    brief_summary: str | None = None

    criteria_type: str

    description: str

    distance: float = Field(
        ge=0.0,
        le=2.0,
        description="Cosine distance between embeddings.",
    )

    model_config = ConfigDict(
        from_attributes=True,
    )


class MatchingResponse(BaseModel):
    """
    Semantic search response.
    """

    query: str = Field(
        description="Patient note used for semantic retrieval.",
    )

    total_matches: int = Field(
        ge=0,
        description="Total number of unique matching trials found.",
    )

    returned_matches: int = Field(
        ge=0,
        description="Number of unique trial matches returned.",
    )

    similarity_threshold: float = Field(
        ge=0.0,
        le=2.0,
        description="Maximum cosine distance accepted.",
    )

    matches: list[MatchingResult]

    model_config = ConfigDict(
        from_attributes=True,
    )