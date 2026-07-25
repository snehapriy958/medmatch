from celery import Celery

from app.config.settings import settings


celery_app = Celery(
    "medmatch",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)


celery_app.conf.imports = (
    "app.celery.tasks",
)