from uuid import UUID

from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.models.patient_note import PatientNote
from app.repositories.base_repository import BaseRepository


class PatientNoteRepository(BaseRepository):
    """
    Repository responsible for PatientNote database operations.
    """

    def __init__(
        self,
        db: Session,
    ) -> None:
        super().__init__(db)

    def create(
        self,
        note: PatientNote,
    ) -> PatientNote:
        """
        Persist a new patient note.
        """
        self.db.add(note)
        return note

    def get_by_id(
        self,
        note_id: UUID,
        hospital_id: int,
    ) -> PatientNote | None:
        """
        Retrieve a patient note by its ID within the authenticated hospital.
        """
        return (
            self.db.query(PatientNote)
            .join(Patient)
            .filter(
                PatientNote.id == note_id,
                Patient.hospital_id == hospital_id,
            )
            .first()
        )

    def list_by_patient(
        self,
        patient_id: UUID,
        hospital_id: int,
    ) -> list[PatientNote]:
        return (
            self.db.query(PatientNote)
            .join(Patient)
            .filter(
                Patient.id == patient_id,
                Patient.hospital_id == hospital_id,
            )
            .order_by(PatientNote.created_at.desc())
            .all()
        )