import logging
import uuid

from app.schemas import AuditLogCreate, AuditLogResponse
from app.repositories.audit_log_repository import AuditLogRepository

logger = logging.getLogger(__name__)


class AuditService:

    def __init__(self, repository: AuditLogRepository):
        self.repository = repository

    def log(
        self,
        action: str,
        resource_type: str,
        performed_by_id: uuid.UUID | None = None,
        performed_by_username: str | None = None,
        performed_by_role: str | None = None,
        hospital_id: uuid.UUID | None = None,
        hospital_name: str | None = None,
        resource_id: uuid.UUID | None = None,
        details: str | None = None,
    ) -> AuditLogResponse | None:

        try:

            audit_log = AuditLogCreate(
                performed_by_id=performed_by_id,
                performed_by_username=performed_by_username,
                performed_by_role=performed_by_role,
                hospital_id=hospital_id,
                hospital_name=hospital_name,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details,
            )

            created = self.repository.create(audit_log)
            self.repository.commit()

            return AuditLogResponse.model_validate(created)

        except Exception:
            logger.exception("Failed to write audit log.")

            self.repository.rollback()

            return None