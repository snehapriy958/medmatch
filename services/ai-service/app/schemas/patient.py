from datetime import datetime
import uuid

from pydantic import BaseModel, ConfigDict, Field


class PatientCreate(BaseModel):
    """
    Schema used when creating a new patient.
    """

    mrn: str = Field(
        ...,
        min_length=1,
        max_length=50,
    )

    first_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    last_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    age: int = Field(
        ...,
        ge=0,
        le=150,
    )

    gender: str = Field(
        ...,
        min_length=1,
        max_length=20,
    )

    diagnosis: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    cancer_type: str | None = None

    stage: str | None = None

    phone: str | None = None

    email: str | None = None


class PatientUpdate(BaseModel):
    """
    Schema used when updating a patient.
    """

    first_name: str | None = None

    last_name: str | None = None

    age: int | None = Field(
        default=None,
        ge=0,
        le=150,
    )

    gender: str | None = None

    diagnosis: str | None = None

    cancer_type: str | None = None

    stage: str | None = None

    phone: str | None = None

    email: str | None = None

    status: str | None = None

class PatientResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

    id: uuid.UUID

    mrn: str

    firstName: str = Field(alias="first_name")

    lastName: str = Field(alias="last_name")

    age: int

    gender: str

    diagnosis: str

    cancerType: str | None = Field(
        default=None,
        alias="cancer_type",
    )

    stage: str | None = None

    phone: str | None = None

    email: str | None = None

    hospitalId: uuid.UUID = Field(
        alias="hospital_id",
    )

    status: str

    matchCount: int = Field(
        alias="match_count",
    )

    createdAt: datetime = Field(
        alias="created_at",
    )

    updatedAt: datetime = Field(
        alias="updated_at",
    )


class PatientListResponse(BaseModel):
    """
    Schema for returning multiple patients.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )

    patients: list[PatientResponse] = Field(
        default_factory=list,
    )

    total: int

    page: int

    pageSize: int = Field(alias="page_size")