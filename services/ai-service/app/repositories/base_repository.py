from typing import Any

from sqlalchemy.orm import Session

"""
Base repository providing common database operations.
"""


class BaseRepository:
    def __init__(self, db: Session):
        self.db = db

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()

    def refresh(self, instance: Any) -> None:
        self.db.refresh(instance)