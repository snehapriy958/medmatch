import logging

from app.config.settings import settings
from app.db.base import Base
from app.db.database import engine

# Import all models
from app.models import (
    AuditLog,
    CriteriaEmbedding,
    Hospital,
    Patient,
    PatientNote,
    PatientNoteEmbedding,
    Trial,
    TrialCriteria,
)


logger = logging.getLogger(__name__)


def init_db() -> None:
    """
    Initialize database tables.

    Used for development/testing.
    Production deployments should use Alembic migrations.
    """

    if settings.ENVIRONMENT == "production":
        logger.warning(
            "Skipping automatic table creation in production. "
            "Use Alembic migrations."
        )
        return

    logger.info("Creating database tables...")

    Base.metadata.create_all(
        bind=engine,
    )

    logger.info(
        "Database tables initialized successfully."
    )