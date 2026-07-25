from typing import Annotated, Any
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Request,
    UploadFile,
    status,
)

from app.api.deps import (
    get_current_hospital_id,
    get_pdf_service,
    get_trial_service,
    require_admin_or_researcher,
)
from app.celery.tasks import process_trial
from app.config.rate_limit import limiter
from app.schemas.trial import TrialCreate, TrialResponse
from app.services.pdf_service import PDFService
from app.services.trial_service import TrialService

router = APIRouter(
    prefix="/api/trials",
    tags=["Trials"],
)


@router.post(
    "",
    response_model=TrialResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("20/minute")
def create_trial(
    request: Request,
    trial: TrialCreate,
    _: Annotated[
        dict[str, Any],
        Depends(require_admin_or_researcher()),
    ],
    hospital_id: Annotated[
        int,
        Depends(get_current_hospital_id),
    ],
    service: Annotated[
        TrialService,
        Depends(get_trial_service),
    ],
) -> TrialResponse:
    """
    Create a new clinical trial.
    """

    return service.create_trial(
        trial_data=trial,
        hospital_id=hospital_id,
    )


@router.get(
    "",
    response_model=list[TrialResponse],
)
@limiter.limit("60/minute")
def list_trials(
    request: Request,
    _: Annotated[
        dict[str, Any],
        Depends(require_admin_or_researcher()),
    ],
    hospital_id: Annotated[
        int,
        Depends(get_current_hospital_id),
    ],
    service: Annotated[
        TrialService,
        Depends(get_trial_service),
    ],
) -> list[TrialResponse]:
    """
    List all trials for the authenticated user's hospital.
    """

    return service.list_trials(hospital_id)


@router.get(
    "/{trial_id}",
    response_model=TrialResponse,
)
@limiter.limit("60/minute")
def get_trial(
    request: Request,
    trial_id: UUID,
    _: Annotated[
        dict[str, Any],
        Depends(require_admin_or_researcher()),
    ],
    hospital_id: Annotated[
        int,
        Depends(get_current_hospital_id),
    ],
    service: Annotated[
        TrialService,
        Depends(get_trial_service),
    ],
) -> TrialResponse:
    """
    Retrieve a trial by its ID.
    """

    trial = service.get_trial(
        trial_id=trial_id,
        hospital_id=hospital_id,
    )

    if trial is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trial not found",
        )

    return trial


@router.delete(
    "/{trial_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
@limiter.limit("10/minute")
def delete_trial(
    request: Request,
    trial_id: UUID,
    _: Annotated[
        dict[str, Any],
        Depends(require_admin_or_researcher()),
    ],
    hospital_id: Annotated[
        int,
        Depends(get_current_hospital_id),
    ],
    service: Annotated[
        TrialService,
        Depends(get_trial_service),
    ],
) -> None:
    """
    Delete a trial.
    """

    deleted = service.delete_trial(
        trial_id=trial_id,
        hospital_id=hospital_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trial not found",
        )


@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("5/minute")
def upload_trial_pdf(
    request: Request,
    _: Annotated[
        dict[str, Any],
        Depends(require_admin_or_researcher()),
    ],
    hospital_id: Annotated[
        int,
        Depends(get_current_hospital_id),
    ],
    pdf_service: Annotated[
        PDFService,
        Depends(get_pdf_service),
    ],
    file: UploadFile = File(...),
) -> dict[str, str]:
    """
    Upload a clinical trial PDF for asynchronous processing.
    """

    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF files are allowed.",
        )

    try:
        file_path = pdf_service.save_pdf(file)
    finally:
        file.file.close()

    task = process_trial.delay(
        str(file_path),
        hospital_id,
    )

    return {
        "task_id": task.id,
        "status": "queued",
    }