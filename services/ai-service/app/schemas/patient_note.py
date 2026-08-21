from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PatientNoteCreate(BaseModel):
    """
    Request body for creating a patient note.
    """

    note: str = Field(
        ...,
        min_length=10,
        max_length=10000,
        description="Clinical patient note used for trial matching.",
    )


class PatientNoteResponse(BaseModel):
    """
    Response returned after creating or retrieving a patient note.
    """

    id: UUID

    patient_id: UUID

    note: str = Field(
        max_length=10000,
        description="Clinical patient note.",
    )

    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )