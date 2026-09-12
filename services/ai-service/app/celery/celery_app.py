from celery import Celery

from app.config.settings import settings


celery_app = Celery(
    "medmatch",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)


celery_app.conf.update(
    # ==========================================================
    # Serialization
    # ==========================================================
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # ==========================================================
    # Time
    # ==========================================================
    timezone="UTC",
    enable_utc=True,

    # ==========================================================
    # Worker
    # ==========================================================
    worker_concurrency=settings.CELERY_CONCURRENCY,

    # Long-running PDF and AI tasks should be distributed fairly
    # instead of being heavily prefetched by workers.
    worker_prefetch_multiplier=1,

    # ==========================================================
    # Task Safety
    # ==========================================================

    # A task is acknowledged after successful completion rather
    # than immediately when the worker receives it.
    task_acks_late=True,

    # If a worker process is unexpectedly lost, return the task
    # to the queue rather than silently losing it.
    task_reject_on_worker_lost=True,

    # Track task lifecycle for monitoring/debugging.
    task_track_started=True,

    # ==========================================================
    # Task Time Limits
    # ==========================================================
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,

    # ==========================================================
    # Result Management
    # ==========================================================

    # Do not retain task results forever.
    result_expires=60 * 60 * 24,
)


celery_app.conf.imports = (
    "app.celery.tasks",
)