from uuid import UUID

from pydantic import BaseModel, Field


class MatchingResult(BaseModel):
    """
    Single semantic search result.
    """

    id: UUID
    trial_id: UUID
    criteria_type: str
    description: str

    distance: float = Field(
        ge=0.0,
        le=2.0,
        description="Cosine distance between embeddings.",
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
        description="Total number of matching criteria found.",
    )

    returned_matches: int = Field(
        ge=0,
        description="Number of criteria returned.",
    )

    similarity_threshold: float = Field(
        ge=0.0,
        le=2.0,
        description="Maximum cosine distance accepted.",
    )

    matches: list[MatchingResult]