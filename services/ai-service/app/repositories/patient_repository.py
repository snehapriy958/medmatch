import logging
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session, selectinload

from app.models.patient import Patient


logger = logging.getLogger(__name__)


class PatientRepository:
    """
    Handles all database operations for patients.
    """

    def __init__(
        self,
        db: Session,
    ) -> None:
        self.db = db

    def create_patient(
        self,
        patient: Patient,
    ) -> Patient:
        """
        Add a new patient entity.
        """

        self.db.add(patient)

        return patient

    def get_patient_by_id(
        self,
        patient_id: UUID,
        hospital_id: UUID,
    ) -> Patient | None:
        """
        Retrieve a patient only from the authenticated hospital.
        """

        return (
            self.db.query(Patient)
            .options(
                selectinload(Patient.notes)
            )
            .filter(
                Patient.id == patient_id,
                Patient.hospital_id == hospital_id,
            )
            .first()
        )

    def list_patients(
        self,
        hospital_id: UUID,
    ) -> list[Patient]:
        """
        Retrieve all patients belonging to a hospital.
        """

        return (
            self.db.query(Patient)
            .filter(
                Patient.hospital_id == hospital_id,
            )
            .order_by(
                Patient.name.asc()
            )
            .all()
        )

    def delete_patient(
        self,
        patient: Patient,
    ) -> None:
        """
        Delete a patient entity.
        """

        self.db.delete(patient)

    def commit(self) -> None:
        """
        Commit database transaction.
        """

        self.db.commit()

    def rollback(self) -> None:
        """
        Rollback database transaction.
        """

        self.db.rollback()

    def refresh(
        self,
        instance: Any,
    ) -> None:
        """
        Refresh entity from database.
        """

        self.db.refresh(instance)