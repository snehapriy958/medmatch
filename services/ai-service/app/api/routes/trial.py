import logging
from typing import Annotated, Any
from uuid import UUID
from celery.result import AsyncResult

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Request,
    UploadFile,
    status,
)

logger = logging.getLogger(__name__)

from app.api.deps import (
    get_current_hospital_id,
    get_pdf_service,
    get_trial_service,
    require_admin_or_researcher,
)
from app.celery.tasks import process_trial
from app.config.rate_limit import limiter
from app.schemas.trial import (
    TrialCreate,
    TrialResponse,
    TrialUpdate,
)
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
        UUID,
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

    print(
        "========== CREATE TRIAL ROUTE HIT ==========",
        flush=True,
    )

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
        UUID,
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

    return service.list_trials(
        hospital_id
    )


@router.get(
    "/upload/status/{task_id}",
)
@limiter.limit("60/minute")
def get_trial_upload_status(
    request: Request,
    task_id: str,
    _: Annotated[
        dict[str, Any],
        Depends(require_admin_or_researcher()),
    ],
) -> dict[str, Any]:
    """
    Retrieve the status of an asynchronous trial PDF upload.
    """

    task_result = AsyncResult(
        task_id,
        app=process_trial.app,
    )

    response: dict[str, Any] = {
        "task_id": task_id,
        "status": task_result.status,
    }

    if task_result.successful():
        response["result"] = task_result.result

    elif task_result.failed():
        response["error"] = (
            "Trial PDF processing failed."
        )

    return response


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
        UUID,
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
            detail="Trial not found.",
        )

    return trial


@router.patch(
    "/{trial_id}",
    response_model=TrialResponse,
)
@limiter.limit("20/minute")
def update_trial(
    request: Request,
    trial_id: UUID,
    trial: TrialUpdate,
    _: Annotated[
        dict[str, Any],
        Depends(require_admin_or_researcher()),
    ],
    hospital_id: Annotated[
        UUID,
        Depends(get_current_hospital_id),
    ],
    service: Annotated[
        TrialService,
        Depends(get_trial_service),
    ],
) -> TrialResponse:
    """
    Update an existing clinical trial.
    """

    updated_trial = service.update_trial(
        trial_id=trial_id,
        hospital_id=hospital_id,
        trial_data=trial,
    )

    if updated_trial is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trial not found.",
        )

    return updated_trial


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
        UUID,
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
            detail="Trial not found.",
        )


@router.post(
    "/upload",
    status_code=status.HTTP_202_ACCEPTED,
)
@limiter.limit("5/minute")
def upload_trial_pdf(
    request: Request,
    _: Annotated[
        dict[str, Any],
        Depends(require_admin_or_researcher()),
    ],
    hospital_id: Annotated[
        UUID,
        Depends(get_current_hospital_id),
    ],
    pdf_service: Annotated[
        PDFService,
        Depends(get_pdf_service),
    ],
    file: UploadFile = File(...),
) -> dict[str, str]:
    """
    Upload a clinical trial PDF and queue asynchronous processing.

    The endpoint validates and stores the PDF before submitting the
    processing job to Celery.
    """

    try:
        file_path = pdf_service.save_pdf(
            file
        )

    except ValueError as exc:
        message = str(exc)

        if "maximum allowed size" in message.lower():
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=message,
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        ) from exc

    finally:
        file.file.close()

    try:
        task = process_trial.delay(
            file_path=str(file_path),
            hospital_id=str(hospital_id),
        )

    except Exception as exc:
        try:
            file_path.unlink(
                missing_ok=True
            )

        except OSError:
            logger.exception(
                "Failed to delete uploaded PDF after "
                "Celery task submission failure: %s",
                file_path,
            )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Unable to queue the trial for processing. "
                "Please try again."
            ),
        ) from exc

    return {
        "task_id": task.id,
        "status": "queued",
    }