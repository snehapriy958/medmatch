import uuid

from pydantic import BaseModel, ConfigDict, Field


class PatientCreate(BaseModel):
    """
    Schema used when creating a new patient.
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=150,
        description="Patient full name",
    )

    age: int = Field(
        ...,
        ge=0,
        le=150,
        description="Patient age",
    )

    gender: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Patient gender",
    )

    diagnosis: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Primary diagnosis",
    )


class PatientResponse(BaseModel):
    """
    Schema returned to clients.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: uuid.UUID

    name: str

    age: int

    gender: str

    diagnosis: str

    hospital_id: uuid.UUID


class PatientListResponse(BaseModel):
    """
    Schema for returning multiple patients.
    """

    patients: list[PatientResponse] = Field(
        default_factory=list,
        max_length=1000,
    )