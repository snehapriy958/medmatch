from collections.abc import Generator
import logging

from sqlalchemy.orm import Session

from app.db.database import SessionLocal


logger = logging.getLogger(__name__)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session.
    """
    db = SessionLocal()

    logger.warning(
        "DB SESSION CREATED: session_id=%s",
        id(db),
    )

    try:
        yield db

    finally:
        logger.warning(
            "DB SESSION CLOSED: session_id=%s",
            id(db),
        )

        db.close()