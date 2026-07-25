from sqlalchemy.orm import Session

from app.models import AuditLog
from app.repositories.base_repository import BaseRepository
from app.schemas import AuditLogCreate


class AuditLogRepository(BaseRepository):

    def __init__(self, db: Session):
        super().__init__(db)

    def create(self, audit_log: AuditLogCreate) -> AuditLog:

        db_audit_log = AuditLog(
            performed_by_id=audit_log.performed_by_id,
            performed_by_username=audit_log.performed_by_username,
            performed_by_role=audit_log.performed_by_role,
            hospital_id=audit_log.hospital_id,
            hospital_name=audit_log.hospital_name,
            action=audit_log.action,
            resource_type=audit_log.resource_type,
            resource_id=audit_log.resource_id,
            details=audit_log.details,
        )

        self.db.add(db_audit_log)

        self.db.flush()
        self.db.refresh(db_audit_log)

        return db_audit_log