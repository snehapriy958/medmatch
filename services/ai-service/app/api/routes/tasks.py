from celery.result import AsyncResult
from fastapi import APIRouter

router = APIRouter(
	prefix="/api/tasks",
	tags=["Tasks"],
)


@router.get("/{task_id}")
def get_task_status(
	task_id: str,
) -> dict:
	"""
	Get the status of a background task.
	"""

	result = AsyncResult(task_id)

	response = {
		"task_id": task_id,
		"status": result.status,
	}

	if result.successful():
		response["result"] = result.result

	elif result.failed():
		response["error"] = str(result.result)

	return response