from typing import Any

from sqlalchemy.orm import Session


class BaseRepository:
    def __init__(
        self,
        db: Session,
    ) -> None:
        self.db = db

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()

    def flush(self) -> None:
        self.db.flush()

    def refresh(
        self,
        instance: Any,
    ) -> None:
        self.db.refresh(instance)