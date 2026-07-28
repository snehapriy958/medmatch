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

                t.title,
                t.condition,
                t.phase,
                t.status,
                t.brief_summary,

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
        Group retrieved criteria by trial while preserving
        trial metadata.
        """

        criteria = self.find_similar_criteria(
            embedding=embedding,
            hospital_id=hospital_id,
            limit=limit,
        )

        grouped_trials: dict[UUID, dict] = {}

        for criterion in criteria:
            trial_id = criterion["trial_id"]

            if trial_id not in grouped_trials:
                grouped_trials[trial_id] = {
                    "trial_id": trial_id,
                    "title": criterion["title"],
                    "condition": criterion["condition"],
                    "phase": criterion["phase"],
                    "status": criterion["status"],
                    "brief_summary": criterion["brief_summary"],
                    "criteria": [],
                }

            grouped_trials[trial_id]["criteria"].append(
                {
                    "criteria_type": criterion["criteria_type"],
                    "description": criterion["description"],
                    "distance": criterion["distance"],
                }
            )

        return list(grouped_trials.values())