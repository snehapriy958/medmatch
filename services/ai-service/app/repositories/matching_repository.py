from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session


class MatchingRepository:
    """
    Repository responsible for tenant-isolated clinical trial retrieval.

    Retrieval strategy:

    1. Enforce hospital isolation.
    2. Retrieve candidate trials using trial-level semantic embeddings.
    3. Select one representative criterion for each candidate trial.
    4. Never retrieve trials from another hospital.
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
        Retrieve candidate trials using trial-level semantic similarity.

        Trial embeddings are used only to identify candidate trials.
        A representative criterion is returned for each trial so the
        existing matching service can preserve its current interface.

        Complete trial criteria are loaded later by MatchingService
        before LLM eligibility evaluation.
        """

        limit = max(
            1,
            min(limit, 100),
        )

        query = text(
            """
            WITH ranked_trials AS (

                SELECT
                    t.id AS trial_id,
                    t.title,
                    t.condition,
                    t.phase,
                    t.status,
                    t.brief_summary,

                    te.embedding <=> CAST(
                        :embedding AS vector
                    ) AS distance

                FROM trials t

                JOIN trial_embeddings te
                    ON te.trial_id = t.id

                WHERE
                    t.hospital_id = :hospital_id
                    AND EXISTS (
                        SELECT 1
                        FROM trial_criteria tc
                        WHERE tc.trial_id = t.id
                    )

                ORDER BY
                    te.embedding <=> CAST(
                        :embedding AS vector
                    ) ASC,
                    t.id ASC

                LIMIT :trial_limit
            ),

            ranked_criteria AS (

                SELECT
                    rt.trial_id,

                    rt.title,
                    rt.condition,
                    rt.phase,
                    rt.status,
                    rt.brief_summary,

                    tc.id,
                    tc.criteria_type,
                    tc.description,

                    rt.distance,

                    ROW_NUMBER() OVER (
                        PARTITION BY rt.trial_id
                        ORDER BY
                            ce.embedding <=> CAST(
                                :embedding AS vector
                            ) ASC,
                            tc.id ASC
                    ) AS criterion_rank

                FROM ranked_trials rt

                JOIN trial_criteria tc
                    ON tc.trial_id = rt.trial_id

                JOIN criteria_embeddings ce
                    ON ce.criteria_id = tc.id
            )

            SELECT
                id,
                trial_id,
                title,
                condition,
                phase,
                status,
                brief_summary,
                criteria_type,
                description,
                distance

            FROM ranked_criteria

            WHERE criterion_rank = 1

            ORDER BY
                distance ASC,
                trial_id ASC,
                id ASC
            """
        )
        result = self.db.execute(
            query,
            {
                "embedding": embedding,
                "hospital_id": hospital_id,
                "trial_limit": limit,
            },
        )

        return [
            dict(
                row._mapping
            )
            for row in result
        ]

    def find_similar_trials(
        self,
        embedding: list[float],
        hospital_id: UUID,
        limit: int = 10,
    ) -> list[dict]:
        """
        Return retrieved trials grouped by trial ID.

        The representative criterion is retained for compatibility
        with existing consumers.
        """

        criteria = self.find_similar_criteria(
            embedding=embedding,
            hospital_id=hospital_id,
            limit=limit,
        )

        grouped_trials: dict[UUID, dict] = {}

        for criterion in criteria:

            trial_id = criterion[
                "trial_id"
            ]

            if trial_id not in grouped_trials:

                grouped_trials[trial_id] = {
                    "trial_id": trial_id,
                    "title": criterion["title"],
                    "condition": criterion["condition"],
                    "phase": criterion["phase"],
                    "status": criterion["status"],
                    "brief_summary": (
                        criterion["brief_summary"]
                    ),
                    "criteria": [],
                }

            grouped_trials[trial_id][
                "criteria"
            ].append(
                {
                    "criteria_type": (
                        criterion["criteria_type"]
                    ),
                    "description": (
                        criterion["description"]
                    ),
                    "distance": (
                        criterion["distance"]
                    ),
                }
            )

        return list(
            grouped_trials.values()
        )