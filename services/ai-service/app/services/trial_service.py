import logging
from uuid import UUID

from app.models.trial import Trial
from app.models.trial_criteria import TrialCriteria
from app.repositories.trial_criteria_repository import (
    TrialCriteriaRepository,
)
from app.repositories.trial_repository import TrialRepository
from app.schemas.trial import (
    TrialCreate,
    TrialUpdate,
)
from app.services.audit_service import AuditService
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService
from app.services.pdf_service import PDFService
from app.services.text_cleaner import TextCleaner
from app.exceptions.api_exceptions import BadRequestException

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

    def _build_trial_embedding_text(
        self,
        trial: Trial,
        inclusion_criteria: list[str] | None = None,
        exclusion_criteria: list[str] | None = None,
    ) -> str:
        """
        Build a canonical text representation of a clinical trial.

        This text is embedded for first-stage semantic trial retrieval.
        """

        text_parts = [
            f"Title: {trial.title}",
            f"Condition: {trial.condition or ''}",
            f"Summary: {trial.brief_summary or ''}",
            f"Phase: {trial.phase or ''}",
            f"Status: {trial.status or ''}",
        ]

        if inclusion_criteria:
            text_parts.append(
                "Inclusion criteria: "
                + " ".join(inclusion_criteria)
            )

        if exclusion_criteria:
            text_parts.append(
                "Exclusion criteria: "
                + " ".join(exclusion_criteria)
            )

        return "\n".join(
            part
            for part in text_parts
            if part.strip()
        )

    def create_trial(
        self,
        trial_data: TrialCreate,
        hospital_id: UUID,
    ) -> Trial:
        """
        Create a new clinical trial.
        """

        try:
            print("\n========== TRIAL TRANSACTION DEBUG ==========")

            print(
                "Trial repository session:",
                id(self.repository.db),
            )

            print(
                "Trial embedding repository session:",
                id(self.embedding_service.trial_repository.db),
            )

            print(
                "Criteria embedding repository session:",
                id(self.embedding_service.criteria_repository.db),
            )

            print(
                "Audit repository session:",
                id(self.audit_service.repository.db),
            )

            existing_trial = (
                self.repository.find_existing_trial(
                    hospital_id=hospital_id,
                    title=trial_data.title,
                    condition=trial_data.condition,
                    phase=trial_data.phase,
                )
            )

            if existing_trial is not None:
                return existing_trial

            trial = Trial(
                title=trial_data.title,
                brief_summary=(
                    trial_data.brief_summary or ""
                ),
                condition=trial_data.condition,
                phase=trial_data.phase,
                status=trial_data.status,
                hospital_id=hospital_id,
            )

            self.repository.create_trial(trial)

            print(
                "After add - trial session:",
                id(self.repository.db),
            )

            self.repository.flush()

            print(
                "After flush - trial ID:",
                trial.id,
            )

            trial_embedding_text = (
                self._build_trial_embedding_text(
                    trial=trial,
                )
            )

            self.embedding_service.create_or_update_trial_embedding(
                trial_id=trial.id,
                text=trial_embedding_text,
            )

            self.audit_service.log(
                action="CREATE_TRIAL",
                resource_type="Trial",
                resource_id=trial.id,
                hospital_id=hospital_id,
                details=(
                    f"Trial '{trial.title}' created."
                ),
            )

            print(
                "Before commit - trial session:",
                id(self.repository.db),
            )

            self.repository.commit()

            print(
                "COMMIT COMPLETED"
            )

            self.repository.refresh(trial)

            print(
                "After refresh - trial ID:",
                trial.id,
            )

            print(
                "============================================\n"
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


    def update_trial(
        self,
        trial_id: UUID,
        hospital_id: UUID,
        trial_data: TrialUpdate,
    ) -> Trial | None:
        """
        Update an existing clinical trial.
        """

        trial = self.repository.get_trial_by_id(
            trial_id,
            hospital_id,
        )

        if trial is None:
            return None

        update_data = trial_data.model_dump(
            exclude_unset=True,
            exclude_none=True,
        )

        if not update_data:
            return trial

        try:
            self.repository.update_trial(
                trial,
                update_data,
            )

            self.repository.flush()

            trial_embedding_text = (
                self._build_trial_embedding_text(
                    trial=trial,
                )
            )

            self.embedding_service.create_or_update_trial_embedding(
                trial_id=trial.id,
                text=trial_embedding_text,
            )

            self.audit_service.log(
                action="UPDATE_TRIAL",
                resource_type="Trial",
                resource_id=trial.id,
                hospital_id=hospital_id,
                details=(
                    f"Trial '{trial.title}' updated."
                ),
            )

            self.repository.commit()

            self.repository.refresh(
                trial
            )

            return trial

        except Exception:
            self.repository.rollback()

            logger.exception(
                "Failed to update trial %s.",
                trial_id,
            )

            raise

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

        trial_title = trial.title

        try:
            self.repository.delete_trial(
                trial
            )

            self.repository.flush()

            self.audit_service.log(
                action="DELETE_TRIAL",
                resource_type="Trial",
                resource_id=trial_id,
                hospital_id=hospital_id,
                details=(
                    f"Trial '{trial_title}' deleted."
                ),
            )

            self.repository.commit()

            return True

        except Exception:
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

        The PDF is extracted and converted into structured trial
        information. Before creating anything in the database,
        an existing trial is checked using hospital + title +
        condition + phase.

        If the trial already exists, the import is skipped so that
        duplicate trials, criteria, and embeddings are not created.
        """

        try:
            raw_text = self.pdf_service.extract_text(file_path)

        except ValueError as exc:
            raise BadRequestException(
                str(exc)
            ) from exc

        clean_text = self.text_cleaner.clean(raw_text)

        extraction = self.llm_service.extract_trial_information(
            clean_text
        )

        # ------------------------------------------------------------
        # DUPLICATE CHECK
        # ------------------------------------------------------------

        existing_trial = self.repository.find_existing_trial(
            hospital_id=hospital_id,
            title=extraction.title,
            condition=extraction.condition,
            phase=extraction.phase,
        )

        if existing_trial is not None:
            logger.info(
                "Trial already exists. Skipping duplicate PDF import. "
                "trial_id=%s hospital_id=%s title='%s'",
                existing_trial.id,
                hospital_id,
                existing_trial.title,
            )

            return {
                "trial_id": str(existing_trial.id),
                "message": (
                    "Trial already exists. "
                    "Duplicate import skipped."
                ),
            }

        # ------------------------------------------------------------
        # CREATE TRIAL + CRITERIA + EMBEDDINGS
        #
        # One database transaction owns the entire PDF import.
        # ------------------------------------------------------------

        try:
            trial = Trial(
                title=extraction.title,
                brief_summary="",
                condition=extraction.condition,
                phase=extraction.phase,
                status=extraction.recruitment_status,
                hospital_id=hospital_id,
            )

            # --------------------------------------------------------
            # CREATE TRIAL
            # --------------------------------------------------------

            self.repository.create_trial(trial)

            self.repository.flush()

            # --------------------------------------------------------
            # CREATE CRITERIA
            # --------------------------------------------------------

            created_criteria: list[TrialCriteria] = []

            for inclusion_text in extraction.inclusion_criteria:

                entity = TrialCriteria(
                    trial_id=trial.id,
                    criteria_type="INCLUSION",
                    description=inclusion_text,
                )

                self.criteria_repository.create(
                    entity
                )

                created_criteria.append(
                    entity
                )

            for exclusion_text in extraction.exclusion_criteria:

                entity = TrialCriteria(
                    trial_id=trial.id,
                    criteria_type="EXCLUSION",
                    description=exclusion_text,
                )

                self.criteria_repository.create(
                    entity
                )

                created_criteria.append(
                    entity
                )

            # Flush criteria so database-generated IDs exist
            self.criteria_repository.flush()

            # --------------------------------------------------------
            # CREATE CRITERIA EMBEDDINGS
            # --------------------------------------------------------

            for created_criterion in created_criteria:

                self.embedding_service.create_trial_embedding(
                    criteria_id=created_criterion.id,
                    text=created_criterion.description,
                )


            # --------------------------------------------------------
            # CREATE TRIAL-LEVEL EMBEDDING
            #
            # This embedding represents the clinical identity of the
            # entire trial and is used during first-stage candidate
            # trial retrieval.
            # --------------------------------------------------------

            inclusion_criteria = [
                criterion.description
                for criterion in created_criteria
                if criterion.criteria_type == "INCLUSION"
            ]

            exclusion_criteria = [
                criterion.description
                for criterion in created_criteria
                if criterion.criteria_type == "EXCLUSION"
            ]

            trial_embedding_text = (
                self._build_trial_embedding_text(
                    trial=trial,
                    inclusion_criteria=inclusion_criteria,
                    exclusion_criteria=exclusion_criteria,
                )
            )

            self.embedding_service.create_or_update_trial_embedding(
                trial_id=trial.id,
                text=trial_embedding_text,
            )


            # --------------------------------------------------------
            # CREATE AUDIT LOG
            #
            # The audit log is added to the same database session and
            # transaction as the trial, criteria, and embeddings.
            # --------------------------------------------------------

            self.audit_service.log(
                action="CREATE_TRIAL",
                resource_type="Trial",
                resource_id=trial.id,
                hospital_id=hospital_id,
                details=(
                    f"Trial '{trial.title}' "
                    "created from PDF import."
                ),
            )

            # --------------------------------------------------------
            # COMMIT ENTIRE IMPORT
            #
            # Trial + criteria + embeddings + audit log are committed
            # atomically.
            # --------------------------------------------------------

            self.repository.commit()

            logger.info(
                "Trial PDF processed successfully. "
                "trial_id=%s criteria_count=%s",
                trial.id,
                len(created_criteria),
            )

            return {
                "trial_id": str(trial.id),
                "message": "Trial imported successfully.",
            }

        except Exception:

            self.repository.rollback()

            logger.exception(
                "Failed to process PDF '%s'.",
                file_path,
            )

            raise