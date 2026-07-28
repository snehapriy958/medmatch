from uuid import UUID

from sqlalchemy.orm import Session

from app.models.hospital import Hospital
from app.repositories.base_repository import BaseRepository


class HospitalRepository(BaseRepository):

    def __init__(self, db: Session):
        super().__init__(db)

    def get_by_id(
        self,
        hospital_id: UUID,
    ) -> Hospital | None:
        return (
            self.db.query(Hospital)
            .filter(Hospital.id == hospital_id)
            .first()
        )