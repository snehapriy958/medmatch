import logging
from pathlib import Path
from uuid import UUID

from celery.exceptions import MaxRetriesExceededError

from app.celery.celery_app import celery_app
from app.db.session import SessionLocal
from app.exceptions.llm import LLMCommunicationError
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.criteria_embedding_repository import (
    CriteriaEmbeddingRepository,
)
from app.repositories.patient_note_embedding_repository import (
    PatientNoteEmbeddingRepository,
)
from app.repositories.trial_criteria_repository import (
    TrialCriteriaRepository,
)
from app.repositories.trial_repository import TrialRepository
from app.repositories.trial_embedding_repository import (
    TrialEmbeddingRepository,
)
from app.services.audit_service import AuditService
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService
from app.services.pdf_service import PDFService
from app.services.text_cleaner import TextCleaner
from app.services.trial_service import TrialService


logger = logging.getLogger(__name__)


def _delete_uploaded_file(
    file_path: str,
) -> None:
    """
    Remove a temporary uploaded PDF.

    Cleanup failures are logged but must not change the outcome
    of trial processing.
    """

    path = Path(file_path)

    try:
        if path.exists() and path.is_file():
            path.unlink()

            logger.info(
                "Deleted uploaded file '%s'.",
                path,
            )

    except OSError:
        logger.exception(
            "Failed to delete uploaded file '%s'.",
            path,
        )


@celery_app.task(
    bind=True,
    name="process_trial",
    max_retries=3,
)
def process_trial(
    self,
    file_path: str,
    hospital_id: str,
) -> dict[str, str]:
    """
    Process a clinical trial PDF in a Celery worker.

    The hospital ID is received as a string because Celery uses
    JSON serialization and is converted to UUID inside the worker.

    LLM communication failures are treated as transient and retried.
    The uploaded PDF remains available during retries and is deleted
    only after successful processing or permanent task failure.
    """

    try:
        hospital_uuid = UUID(hospital_id)

    except (TypeError, ValueError) as exc:
        logger.error(
            "Invalid hospital ID received by trial processing task: %r",
            hospital_id,
        )

        _delete_uploaded_file(
            file_path
        )

        raise ValueError(
            "Invalid hospital ID supplied to process_trial."
        ) from exc

    db = SessionLocal()

    try:
        logger.info(
            "Processing trial PDF '%s' for hospital %s. "
            "Task ID: %s. Retry count: %d",
            file_path,
            hospital_uuid,
            self.request.id,
            self.request.retries,
        )

        trial_repository = TrialRepository(
            db
        )

        criteria_repository = (
            TrialCriteriaRepository(db)
        )

        criteria_embedding_repository = (
            CriteriaEmbeddingRepository(db)
        )

        patient_note_embedding_repository = (
            PatientNoteEmbeddingRepository(db)
        )

        trial_embedding_repository = (
            TrialEmbeddingRepository(db)
        )

        audit_repository = AuditLogRepository(
            db
        )

        pdf_service = PDFService()

        text_cleaner = TextCleaner()

        llm_service = LLMService()

        audit_service = AuditService(
            audit_repository,
        )

        embedding_service = EmbeddingService(
            criteria_repository=(
                criteria_embedding_repository
            ),
            patient_note_repository=(
                patient_note_embedding_repository
            ),
            trial_repository=(
                trial_embedding_repository
            ),
        )

        trial_service = TrialService(
            repository=trial_repository,
            criteria_repository=criteria_repository,
            pdf_service=pdf_service,
            text_cleaner=text_cleaner,
            llm_service=llm_service,
            embedding_service=embedding_service,
            audit_service=audit_service,
        )

        result = trial_service.process_pdf(
            file_path=file_path,
            hospital_id=hospital_uuid,
        )

        logger.info(
            "Successfully processed trial PDF '%s'. "
            "Task ID: %s",
            file_path,
            self.request.id,
        )

        _delete_uploaded_file(
            file_path
        )

        return result

    except LLMCommunicationError as exc:
        logger.warning(
            "Transient LLM communication failure while "
            "processing trial PDF '%s'. "
            "Task ID: %s. Retry count: %d",
            file_path,
            self.request.id,
            self.request.retries,
            exc_info=True,
        )

        try:
            raise self.retry(
                exc=exc,
                countdown=min(
                    60,
                    2 ** self.request.retries,
                ),
            )

        except MaxRetriesExceededError:
            logger.exception(
                "Maximum LLM retries exceeded for trial PDF '%s'. "
                "Task ID: %s",
                file_path,
                self.request.id,
            )

            _delete_uploaded_file(
                file_path
            )

            raise

    except Exception:
        logger.exception(
            "Failed processing trial PDF '%s'. "
            "Task ID: %s",
            file_path,
            self.request.id,
        )

        _delete_uploaded_file(
            file_path
        )

        raise

    finally:
        db.close()