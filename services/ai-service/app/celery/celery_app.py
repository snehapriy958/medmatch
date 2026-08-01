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

    worker_concurrency=settings.CELERY_CONCURRENCY,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
)

celery_app.conf.imports = (
    "app.celery.tasks",
)