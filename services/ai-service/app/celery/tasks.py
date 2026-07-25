import logging

from app.celery.celery_app import celery_app
from app.db.session import SessionLocal
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
from app.services.audit_service import AuditService
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService
from app.services.pdf_service import PDFService
from app.services.text_cleaner import TextCleaner
from app.services.trial_service import TrialService

logger = logging.getLogger(__name__)


@celery_app.task(name="process_trial")
def process_trial(
    file_path: str,
    hospital_id: int,
) -> dict[str, str]:
    db = SessionLocal()

    try:
        logger.info(
            "Processing trial PDF '%s' for hospital %s",
            file_path,
            hospital_id,
        )

        trial_repository = TrialRepository(db)
        criteria_repository = TrialCriteriaRepository(db)

        criteria_embedding_repository = (
            CriteriaEmbeddingRepository(db)
        )

        patient_note_embedding_repository = (
            PatientNoteEmbeddingRepository(db)
        )

        audit_repository = AuditLogRepository(db)

        pdf_service = PDFService()
        text_cleaner = TextCleaner()
        llm_service = LLMService()

        audit_service = AuditService(
            audit_repository,
        )

        embedding_service = EmbeddingService(
            criteria_repository=criteria_embedding_repository,
            patient_note_repository=patient_note_embedding_repository,
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
            hospital_id=hospital_id,
        )

        logger.info(
            "Successfully processed trial PDF '%s'",
            file_path,
        )

        return result

    except Exception:
        logger.exception(
            "Failed processing trial PDF '%s'",
            file_path,
        )
        raise

    finally:
        db.close()