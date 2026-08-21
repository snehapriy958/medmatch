import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AuditLogCreate(BaseModel):
    performed_by_id: uuid.UUID | None = None

    performed_by_username: str | None = None

    performed_by_role: str | None = None

    hospital_id: uuid.UUID | None = None

    hospital_name: str | None = None

    action: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    resource_type: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    resource_id: uuid.UUID | None = None

    details: str | None = Field(
        default=None,
        max_length=5000,
    )


class AuditLogResponse(BaseModel):
    id: uuid.UUID

    performed_by_id: uuid.UUID | None

    performed_by_username: str | None

    performed_by_role: str | None

    hospital_id: uuid.UUID | None

    hospital_name: str | None

    action: str

    resource_type: str

    resource_id: uuid.UUID | None

    details: str | None

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)