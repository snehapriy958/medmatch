import logging
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.match import Match


logger = logging.getLogger(__name__)


class MatchRepository:
    """
    Handles all database operations for persisted matches.

    Every read method requires hospital_id and filters on it
    explicitly, alongside whichever other identifier is supplied.
    This repository makes no assumption that an id passed in by a
    caller has already been hospital-scoped upstream.
    """

    def __init__(
        self,
        db: Session,
    ) -> None:
        self.db = db

    def create_match(
        self,
        match: Match,
    ) -> Match:
        """
        Add a new match entity.
        """

        self.db.add(match)

        return match

    def get_match_by_id(
        self,
        match_id: UUID,
        hospital_id: UUID,
    ) -> Match | None:
        """
        Retrieve a match only from the authenticated hospital.
        """

        return (
            self.db.query(Match)
            .filter(
                Match.id == match_id,
                Match.hospital_id == hospital_id,
            )
            .first()
        )

    def list_matches_for_patient(
        self,
        patient_id: UUID,
        hospital_id: UUID,
    ) -> list[Match]:
        """
        Retrieve all matches for a patient, scoped to a hospital.
        """

        return (
            self.db.query(Match)
            .filter(
                Match.patient_id == patient_id,
                Match.hospital_id == hospital_id,
            )
            .order_by(
                Match.created_at.desc(),
            )
            .all()
        )

    def list_matches_for_trial(
        self,
        trial_id: UUID,
        hospital_id: UUID,
    ) -> list[Match]:
        """
        Retrieve all matches for a trial, scoped to a hospital.
        """

        return (
            self.db.query(Match)
            .filter(
                Match.trial_id == trial_id,
                Match.hospital_id == hospital_id,
            )
            .order_by(
                Match.created_at.desc(),
            )
            .all()
        )

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
