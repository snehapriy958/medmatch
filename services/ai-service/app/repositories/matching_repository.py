from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session


class MatchingRepository:
    """
    Repository responsible for vector similarity search.
    """

    def __init__(
        self,
        db: Session,
    ) -> None:
        self.db = db

    def find_similar_criteria(
        self,
        embedding: list[float],
        hospital_id: UUID,
        limit: int = 10,
    ) -> list[dict]:
        """
        Find the most similar trial criteria using pgvector,
        restricted to the authenticated user's hospital.
        """

        limit = max(1, min(limit, 100))

        query = text(
            """
            SELECT
                tc.id,
                tc.trial_id,
                tc.criteria_type,
                tc.description,
                ce.embedding <=> CAST(:embedding AS vector) AS distance

            FROM criteria_embeddings ce

            JOIN trial_criteria tc
                ON tc.id = ce.criteria_id

            JOIN trials t
                ON t.id = tc.trial_id

            WHERE t.hospital_id = :hospital_id

            ORDER BY distance
            
            LIMIT :limit
            """
        )

        result = self.db.execute(
            query,
            {
                "embedding": embedding,
                "hospital_id": hospital_id,
                "limit": limit,
            },
        )

        return [
            dict(row._mapping)
            for row in result
        ]

    def find_similar_trials(
        self,
        embedding: list[float],
        hospital_id: UUID,
        limit: int = 10,
    ) -> list[dict]:
        """
        Retrieve the most relevant criteria and group them by trial.
        """

        criteria = self.find_similar_criteria(
            embedding=embedding,
            hospital_id=hospital_id,
            limit=limit,
        )

        grouped_trials: dict[UUID, list[dict]] = {}

        for criterion in criteria:
            trial_id = criterion["trial_id"]

            if trial_id not in grouped_trials:
                grouped_trials[trial_id] = []

            grouped_trials[trial_id].append(
                {
                    "criteria_type": criterion["criteria_type"],
                    "description": criterion["description"],
                    "distance": criterion["distance"],
                }
            )

        return [
            {
                "trial_id": trial_id,
                "criteria": trial_criteria,
            }
            for trial_id, trial_criteria in grouped_trials.items()
        ]