from uuid import UUID
import logging

from fastapi import HTTPException, status

from app.models.patient_note import PatientNote
from app.repositories.patient_note_repository import (
    PatientNoteRepository,
)
from app.repositories.patient_repository import (
    PatientRepository,
)
from app.schemas.patient_note import PatientNoteCreate
from app.services.audit_service import AuditService
from app.services.embedding_service import EmbeddingService


logger = logging.getLogger(__name__)


class PatientNoteService:
    """
    Business logic for patient notes.
    """

    def __init__(
        self,
        patient_repository: PatientRepository,
        note_repository: PatientNoteRepository,
        embedding_service: EmbeddingService,
        audit_service: AuditService,
    ) -> None:
        self.patient_repository = patient_repository
        self.note_repository = note_repository
        self.embedding_service = embedding_service
        self.audit_service = audit_service

    def create_note(
        self,
        patient_id: UUID,
        note_data: PatientNoteCreate,
        hospital_id: UUID,
    ) -> PatientNote:
        """
        Create a patient note and generate its embedding.
        """

        patient = self.patient_repository.get_patient_by_id(
            patient_id,
            hospital_id,
        )

        if patient is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found.",
            )

        note = PatientNote(
            patient_id=patient_id,
            note=note_data.note,
        )

        try:
            self.note_repository.create(note)

            self.note_repository.commit()

            self.note_repository.refresh(note)

            self.embedding_service.create_patient_note_embedding(
                note_id=note.id,
                text=note.note,
            )

            self.audit_service.log(
                action="PATIENT_NOTE_CREATED",
                resource_type="PatientNote",
                resource_id=note.id,
                details=(
                    f"Patient note created "
                    f"for patient {patient_id}."
                ),
            )

            return note

        except Exception:
            self.note_repository.rollback()

            logger.exception(
                "Failed to create patient note "
                "for patient %s",
                patient_id,
            )

            raise