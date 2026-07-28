from uuid import UUID
import logging

from app.models.patient import Patient
from app.repositories.patient_repository import PatientRepository
from app.repositories.hospital_repository import HospitalRepository
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
        hospital_repository: HospitalRepository,
        audit_service: AuditService,
    ) -> None:
        self.repository = repository
        self.hospital_repository = hospital_repository
        self.audit_service = audit_service

    def create_patient(
        self,
        patient_data: PatientCreate,
        hospital_id: UUID,
        current_user: dict,
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
            self.repository.create_patient(patient)

            self.repository.commit()

            self.repository.refresh(patient)

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
                    action="PATIENT_CREATED",
                    resource_type="Patient",
                    performed_by_id=UUID(current_user["sub"]),
                    performed_by_username=current_user["email"],
                    performed_by_role=current_user["role"],
                    hospital_id=hospital_id,
                    hospital_name=hospital_name,
                    resource_id=patient.id,
                    details=f"Patient '{patient.name}' created.",
                )

            except Exception:
                logger.exception(
                    "Failed to write patient audit log."
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
        hospital_id: UUID,
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
        hospital_id: UUID,
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
        hospital_id: UUID,
        current_user: dict,
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
            self.repository.delete_patient(patient)

            self.repository.commit()

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
                    action="PATIENT_DELETED",
                    resource_type="Patient",
                    performed_by_id=UUID(current_user["sub"]),
                    performed_by_username=current_user["email"],
                    performed_by_role=current_user["role"],
                    hospital_id=hospital_id,
                    hospital_name=hospital_name,
                    resource_id=patient.id,
                    details=f"Patient '{patient.name}' deleted.",
                )

            except Exception:
                logger.exception(
                    "Failed to write patient deletion audit log."
                )

            return True

        except Exception:
            self.repository.rollback()

            logger.exception(
                "Failed to delete patient %s",
                patient_id,
            )

            raise