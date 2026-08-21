from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session


class MatchingRepository:
    """
    Repository responsible for vector similarity search.

    Retrieval strategy:

    1. Enforce hospital/tenant isolation.
    2. Identify condition-compatible trials before vector ranking.
    3. Rank compatible trials using pgvector.
    4. Return the most relevant criteria from those trials.
    5. Fall back to tenant-scoped semantic retrieval only when
       no condition-compatible trials exist.
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
        patient_note: str,
        limit: int = 10,
    ) -> list[dict]:
        """
        Retrieve semantically similar trial criteria with
        condition-aware filtering.

        Retrieval policy:

        1. Enforce hospital/tenant isolation.
        2. Identify condition-compatible trials before vector ranking.
        3. Rank compatible trials using pgvector.
        4. Return the most relevant criteria from those trials.
        5. If no condition-compatible trial exists, return no results.

        Important:
        There is intentionally NO semantic fallback to unrelated trials.
        """

        limit = max(1, min(limit, 100))

        query = text(
            """
            WITH condition_tokens AS (

                /*
                * Extract meaningful condition words from the
                * patient's clinical note.
                */
                SELECT DISTINCT token
                FROM regexp_split_to_table(
                    lower(coalesce(:patient_note, '')),
                    '[^a-zA-Z0-9]+'
                ) AS token
                WHERE length(token) >= 4
                AND token NOT IN (
                    'cancer',
                    'disease',
                    'syndrome',
                    'disorder',
                    'treatment',
                    'advanced',
                    'metastatic',
                    'malignant',
                    'carcinoma',
                    'patient',
                    'patients',
                    'stage',
                    'clinical',
                    'trial',
                    'therapy',
                    'female',
                    'male',
                    'year',
                    'years',
                    'old',
                    'diagnosed',
                    'diagnosis',
                    'history',
                    'with',
                    'without',
                    'positive',
                    'negative',
                    'normal',
                    'completed',
                    'currently'
                )
            ),

            condition_candidates AS (

                /*
                * Find trials in THIS hospital whose condition
                * contains at least one meaningful condition token.
                */
                SELECT
                    t.id AS trial_id,

                    COUNT(DISTINCT ct.token) AS matched_condition_tokens,

                    MIN(
                        ce.embedding <=> CAST(:embedding AS vector)
                    ) AS trial_distance

                FROM trials t

                JOIN trial_criteria tc
                    ON tc.trial_id = t.id

                JOIN criteria_embeddings ce
                    ON ce.criteria_id = tc.id

                JOIN condition_tokens ct
                    ON lower(coalesce(t.condition, ''))
                    LIKE '%' || ct.token || '%'

                WHERE t.hospital_id = :hospital_id

                GROUP BY t.id

                ORDER BY
                    matched_condition_tokens DESC,
                    trial_distance ASC

                LIMIT :trial_limit
            ),

            ranked_criteria AS (

                /*
                * Rank criteria only inside condition-compatible
                * trials selected above.
                */
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

                    ce.embedding <=> CAST(:embedding AS vector)
                        AS distance,

                    ROW_NUMBER() OVER (
                        PARTITION BY tc.trial_id
                        ORDER BY
                            ce.embedding <=> CAST(:embedding AS vector)
                    ) AS criterion_rank

                FROM condition_candidates cc

                JOIN trials t
                    ON t.id = cc.trial_id

                JOIN trial_criteria tc
                    ON tc.trial_id = t.id

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

            WHERE criterion_rank <= 5

            ORDER BY
                distance ASC
            """
        )

        result = self.db.execute(
            query,
            {
                "embedding": embedding,
                "hospital_id": hospital_id,
                "patient_note": patient_note,
                "trial_limit": limit,
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
        patient_note: str,
        limit: int = 10,
    ) -> list[dict]:
        """
        Group retrieved criteria by trial while preserving
        trial metadata.
        """

        criteria = self.find_similar_criteria(
            embedding=embedding,
            hospital_id=hospital_id,
            patient_note=patient_note,
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