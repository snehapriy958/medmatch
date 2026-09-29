from typing import Annotated, Any
from uuid import UUID

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_hospital_id, get_current_user
from app.services.task_registry import get_task_tenant

router = APIRouter(
    prefix="/api/tasks",
    tags=["Tasks"],
)


@router.get("/{task_id}")
def get_task_status(
    task_id: str,
    current_user: Annotated[
        dict[str, Any],
        Depends(get_current_user),
    ],
    current_hospital_id: Annotated[
        UUID,
        Depends(get_current_hospital_id),
    ],
) -> dict:
    """
    Get the status of a background task. Enforces hospital tenant isolation.
    """
    task_tenant = get_task_tenant(task_id)

    # 1. Fail-closed nonexistent / unmapped task check:
    # Every legitimate task must have a registered tenant. If no tenant is found,
    # return 404 rather than leaking task existence or Celery's default PENDING state.
    if task_tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # 2. Enforce tenant ownership:
    if str(task_tenant).lower() != str(current_hospital_id).lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: task belongs to another hospital tenant",
        )

    result = AsyncResult(task_id)

    response: dict[str, Any] = {
        "task_id": task_id,
        "status": result.status,
    }

    if result.successful():
        res = result.result
        if isinstance(res, dict):
            response["result"] = {k: v for k, v in res.items() if k != "hospital_id"}
        else:
            response["result"] = res

    elif result.failed():
        # Do not leak internal exception traces, raw Python reprs, or DB connection details
        response["error"] = "Task processing failed"

    return response