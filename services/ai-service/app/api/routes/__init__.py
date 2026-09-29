from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.api.routes.patients import router as patients_router
from app.api.routes.trial import router as trials_router
from app.api.routes.matching import router as matching_router
from app.api.routes.tasks import router as tasks_router
from app.api.routes.evaluation import router as evaluation_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(trials_router)
api_router.include_router(patients_router)
api_router.include_router(matching_router)
api_router.include_router(tasks_router)
api_router.include_router(evaluation_router)