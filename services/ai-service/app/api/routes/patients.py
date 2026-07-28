from typing import Annotated, Any
from app.config.settings import settings
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)

from app.api.deps import (
    get_current_hospital_id,
    get_patient_note_service,
    get_patient_service,
    require_admin,
    require_admin_or_doctor,
)
from app.config.rate_limit import limiter

from app.schemas import (
    PatientCreate,
    PatientListResponse,
    PatientResponse,
)

from app.schemas.patient_note import (
    PatientNoteCreate,
    PatientNoteResponse,
)
from app.services.patient_note_service import (
    PatientNoteService,
)
from app.services.patient_service import PatientService


router = APIRouter(
    prefix=f"{settings.API_PREFIX}/patients",
    tags=["Patients"],
)


@router.post(
    "",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("30/minute")
def create_patient(
    request: Request,
    patient: PatientCreate,
    current_user: Annotated[
        dict[str, Any],
        Depends(require_admin_or_doctor()),
    ],
    service: Annotated[
        PatientService,
        Depends(get_patient_service),
    ],
    hospital_id: Annotated[
        UUID,
        Depends(get_current_hospital_id),
    ],
) -> PatientResponse:
    """
    Create a new patient inside the authenticated hospital.
    """

    return service.create_patient(
        patient_data=patient,
        hospital_id=hospital_id,
        current_user=current_user,
    )


@router.get(
    "",
    response_model=PatientListResponse,
)
@limiter.limit("60/minute")
def list_patients(
    request: Request,
    current_user: Annotated[
        dict[str, Any],
        Depends(require_admin_or_doctor()),
    ],
    service: Annotated[
        PatientService,
        Depends(get_patient_service),
    ],
    hospital_id: Annotated[
        UUID,
        Depends(get_current_hospital_id),
    ],
) -> PatientListResponse:
    """
    Retrieve all patients belonging to the authenticated hospital.
    """

    patients = service.list_patients(
        hospital_id=hospital_id,
    )

    return PatientListResponse(
        patients=patients,
    )


@router.get(
    "/{patient_id}",
    response_model=PatientResponse,
)
@limiter.limit("60/minute")
def get_patient(
    request: Request,
    patient_id: UUID,
    current_user: Annotated[
        dict[str, Any],
        Depends(require_admin_or_doctor()),
    ],
    service: Annotated[
        PatientService,
        Depends(get_patient_service),
    ],
    hospital_id: Annotated[
        UUID,
        Depends(get_current_hospital_id),
    ],
) -> PatientResponse:
    """
    Retrieve a patient from the authenticated hospital.
    """

    patient = service.get_patient(
        patient_id=patient_id,
        hospital_id=hospital_id,
    )

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found.",
        )

    return patient


@router.delete(
    "/{patient_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
@limiter.limit("10/minute")
def delete_patient(
    request: Request,
    patient_id: UUID,
    current_user: Annotated[
        dict[str, Any],
        Depends(require_admin()),
    ],
    service: Annotated[
        PatientService,
        Depends(get_patient_service),
    ],
    hospital_id: Annotated[
        UUID,
        Depends(get_current_hospital_id),
    ],
) -> None:
    """
    Delete a patient.

    Only administrators can delete patient records.
    """

    deleted = service.delete_patient(
        patient_id=patient_id,
        hospital_id=hospital_id,
        current_user=current_user,
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found.",
        )


@router.post(
    "/{patient_id}/notes",
    response_model=PatientNoteResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("30/minute")
def create_patient_note(
    request: Request,
    patient_id: UUID,
    note: PatientNoteCreate,
    current_user: Annotated[
        dict[str, Any],
        Depends(require_admin_or_doctor()),
    ],
    service: Annotated[
        PatientNoteService,
        Depends(get_patient_note_service),
    ],
    hospital_id: Annotated[
        UUID,
        Depends(get_current_hospital_id),
    ],
) -> PatientNoteResponse:
    """
    Create a patient note and generate its embedding.

    Hospital ownership validation is handled
    inside the service/repository layer.
    """

    return service.create_note(
        patient_id=patient_id,
        note_data=note,
        hospital_id=hospital_id,
        current_user=current_user,
    )