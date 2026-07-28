import logging
from uuid import UUID

from fastapi import HTTPException, status

from app.models.trial import Trial
from app.models.trial_criteria import TrialCriteria
from app.repositories.trial_criteria_repository import (
    TrialCriteriaRepository,
)
from app.repositories.trial_repository import TrialRepository
from app.schemas.trial import TrialCreate
from app.services.audit_service import AuditService
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService
from app.services.pdf_service import PDFService
from app.services.text_cleaner import TextCleaner

logger = logging.getLogger(__name__)


class TrialService:
    """
    Business logic for clinical trials.
    """

    def __init__(
        self,
        repository: TrialRepository,
        criteria_repository: TrialCriteriaRepository,
        pdf_service: PDFService,
        text_cleaner: TextCleaner,
        llm_service: LLMService,
        embedding_service: EmbeddingService,
        audit_service: AuditService,
    ) -> None:
        self.repository = repository
        self.criteria_repository = criteria_repository
        self.pdf_service = pdf_service
        self.text_cleaner = text_cleaner
        self.llm_service = llm_service
        self.embedding_service = embedding_service
        self.audit_service = audit_service

    def create_trial(
        self,
        trial_data: TrialCreate,
        hospital_id: UUID,
    ) -> Trial:
        """
        Create a new clinical trial.
        """

        trial = Trial(
            title=trial_data.title,
            brief_summary=trial_data.brief_summary,
            condition=trial_data.condition,
            phase=trial_data.phase,
            status=trial_data.status,
            hospital_id=hospital_id,
        )

        try:
            self.repository.create_trial(trial)
            self.repository.commit()

            self.repository.refresh(trial)

            try:
                self.audit_service.log(
                    action="CREATE_TRIAL",
                    resource_type="Trial",
                    resource_id=trial.id,
                    details=f"Trial '{trial.title}' created.",
                )
            except Exception:
                logger.exception(
                    "Failed to write audit log for trial %s.",
                    trial.id,
                )

            return trial

        except Exception:
            self.repository.rollback()

            logger.exception(
                "Failed to create trial '%s'.",
                trial_data.title,
            )

            raise

    def get_trial(
        self,
        trial_id: UUID,
        hospital_id: UUID,
    ) -> Trial | None:
        """
        Retrieve a trial by ID.
        """
        return self.repository.get_trial_by_id(
            trial_id,
            hospital_id,
        )

    def list_trials(
        self,
        hospital_id: UUID,
    ) -> list[Trial]:
        """
        Retrieve all clinical trials.
        """
        return self.repository.list_trials(hospital_id)

    def delete_trial(
        self,
        trial_id: UUID,
        hospital_id: UUID,
    ) -> bool:
        """
        Delete a clinical trial.
        """

        trial = self.repository.get_trial_by_id(
            trial_id,
            hospital_id,
        )

        if trial is None:
            return False

        try:
            self.repository.delete_trial(trial)
            self.repository.commit()

            try:
                self.audit_service.log(
                    action="DELETE_TRIAL",
                    resource_type="Trial",
                    resource_id=trial.id,
                    details=f"Trial '{trial.title}' deleted.",
                )
            except Exception:
                logger.exception(
                    "Failed to write audit log for deleted trial %s.",
                    trial.id,
                )

            return True

        except Exception as exc:
            self.repository.rollback()

            logger.exception(
                "Failed to delete trial %s.",
                trial_id,
            )

            raise

    def process_pdf(
        self,
        file_path: str,
        hospital_id: UUID,
    ) -> dict[str, str]:
        """
        Process a saved clinical trial PDF.
        """

        try:
            raw_text = self.pdf_service.extract_text(file_path)

        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc

        clean_text = self.text_cleaner.clean(raw_text)

        extraction = self.llm_service.extract_trial_information(
            clean_text
        )

        trial = Trial(
            title=extraction.title,
            brief_summary="",
            condition=extraction.condition,
            phase=extraction.phase,
            status=extraction.recruitment_status,
            hospital_id=hospital_id,
        )

        try:
            self.repository.create_trial(trial)
            self.repository.commit()
            self.repository.refresh(trial)

            try:
                self.audit_service.log(
                    action="CREATE_TRIAL",
                    resource_type="Trial",
                    resource_id=trial.id,
                    details=f"Trial '{trial.title}' imported from PDF.",
                )
            except Exception:
                logger.exception(
                    "Failed to write audit log for imported trial %s.",
                    trial.id,
                )

            created_criteria: list[TrialCriteria] = []

            for inclusion_text in extraction.inclusion_criteria:
                entity = TrialCriteria(
                    trial_id=trial.id,
                    criteria_type="INCLUSION",
                    description=inclusion_text,
                )

                self.criteria_repository.create(entity)
                created_criteria.append(entity)

            for exclusion_text in extraction.exclusion_criteria:
                entity = TrialCriteria(
                    trial_id=trial.id,
                    criteria_type="EXCLUSION",
                    description=exclusion_text,
                )

                self.criteria_repository.create(entity)
                created_criteria.append(entity)

            self.criteria_repository.commit()

            for created_criterion in created_criteria:
                self.criteria_repository.refresh(created_criterion)

            for created_criterion in created_criteria:
                self.embedding_service.create_trial_embedding(
                    criteria_id=created_criterion.id,
                    text=created_criterion.description,
                )

            return {
                "trial_id": str(trial.id),
                "message": "Trial imported successfully.",
            }

        except Exception as exc:
            self.repository.rollback()

            logger.exception(
                "Failed to process PDF '%s'.",
                file_path,
            )

            raise