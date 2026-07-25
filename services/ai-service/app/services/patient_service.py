from uuid import UUID
import logging

from app.models.patient import Patient
from app.repositories.patient_repository import PatientRepository
from app.schemas.patient import PatientCreate
from app.services.audit_service import AuditService


logger = logging.getLogger(__name__)


class PatientService:
    """
    Business logic for patients.
    """

    def __init__(
        self,
        repository: PatientRepository,
        audit_service: AuditService,
    ) -> None:
        self.repository = repository
        self.audit_service = audit_service

    def create_patient(
        self,
        patient_data: PatientCreate,
        hospital_id: int,
    ) -> Patient:
        """
        Create a new patient inside the authenticated hospital.
        """

        patient = Patient(
            name=patient_data.name,
            age=patient_data.age,
            gender=patient_data.gender,
            diagnosis=patient_data.diagnosis,
            hospital_id=hospital_id,
        )

        try:
            self.repository.create_patient(
                patient
            )

            self.repository.commit()

            self.repository.refresh(
                patient
            )

            self.audit_service.log(
                action="PATIENT_CREATED",
                resource="Patient",
                resource_id=patient.id,
                details=(
                    f"Patient '{patient.name}' "
                    "created."
                ),
            )

            return patient

        except Exception:
            self.repository.rollback()

            logger.exception(
                "Failed to create patient."
            )

            raise

    def get_patient(
        self,
        patient_id: UUID,
        hospital_id: int,
    ) -> Patient | None:
        """
        Retrieve a patient belonging to the hospital.
        """

        return self.repository.get_patient_by_id(
            patient_id,
            hospital_id,
        )

    def list_patients(
        self,
        hospital_id: int,
    ) -> list[Patient]:
        """
        Retrieve all patients belonging to the hospital.
        """

        return self.repository.list_patients(
            hospital_id,
        )

    def delete_patient(
        self,
        patient_id: UUID,
        hospital_id: int,
    ) -> bool:
        """
        Delete a patient belonging to the hospital.
        """

        patient = self.repository.get_patient_by_id(
            patient_id,
            hospital_id,
        )

        if patient is None:
            return False

        try:
            self.repository.delete_patient(
                patient
            )

            self.repository.commit()

            self.audit_service.log(
                action="PATIENT_DELETED",
                resource="Patient",
                resource_id=patient.id,
                details=(
                    f"Patient '{patient.name}' "
                    "deleted."
                ),
            )

            return True

        except Exception:
            self.repository.rollback()

            logger.exception(
                "Failed to delete patient %s",
                patient_id,
            )

            raise