import logging


logger = logging.getLogger(__name__)


def init_db() -> None:
    """
    Database schema initialization is managed by Alembic migrations.

    This function is intentionally retained so application startup
    remains compatible with the existing lifecycle structure.
    """

    logger.info(
        "Database schema is managed by Alembic migrations."
    )