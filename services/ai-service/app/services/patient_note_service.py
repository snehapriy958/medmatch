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
from app.repositories.hospital_repository import HospitalRepository

logger = logging.getLogger(__name__)


class PatientNoteService:
    """
    Business logic for patient notes.
    """

    def __init__(
        self,
        patient_repository: PatientRepository,
        note_repository: PatientNoteRepository,
        hospital_repository: HospitalRepository,
        embedding_service: EmbeddingService,
        audit_service: AuditService,
    ) -> None:
        self.patient_repository = patient_repository
        self.note_repository = note_repository
        self.hospital_repository = hospital_repository
        self.embedding_service = embedding_service
        self.audit_service = audit_service

    def create_note(
        self,
        patient_id: UUID,
        note_data: PatientNoteCreate,
        hospital_id: UUID,
        current_user: dict,
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

            hospital = self.hospital_repository.get_by_id(
                hospital_id
            )

            hospital_name = (
                hospital.name
                if hospital is not None
                else "Unknown Hospital"
            )

            try:
                self.audit_service.log(
                    action="PATIENT_NOTE_CREATED",
                    resource_type="PatientNote",
                    performed_by_id=UUID(current_user["sub"]),
                    performed_by_username=current_user["email"],
                    performed_by_role=current_user["role"],
                    hospital_id=hospital_id,
                    hospital_name=hospital_name,
                    resource_id=note.id,
                    details=(
                        f"Patient note created "
                        f"for patient {patient_id}."
                    ),
                )

            except Exception:
                logger.exception(
                    "Failed to write patient note audit log."
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

    def list_notes(
        self,
        patient_id: UUID,
        hospital_id: UUID,
    ) -> list[PatientNote]:
        """
        Retrieve all clinical notes for a patient
        within the authenticated hospital.
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

        return self.note_repository.list_by_patient(
            patient_id,
            hospital_id,
        )