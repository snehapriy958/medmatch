from app.db.session import SessionLocal
from app.services.embedding_service import EmbeddingService
from app.repositories.criteria_embedding_repository import CriteriaEmbeddingRepository
from app.repositories.patient_note_embedding_repository import PatientNoteEmbeddingRepository
from sqlalchemy import text

HOSPITAL_ID = "7cd67ec8-7602-4472-9a4d-4676d6cd467f"

db = SessionLocal()

try:
    rows = db.execute(
        text("""
            SELECT tc.id, tc.description
            FROM trial_criteria tc
            JOIN trials t ON t.id = tc.trial_id
            LEFT JOIN criteria_embeddings ce
                ON ce.criteria_id = tc.id
            WHERE t.hospital_id = :hid
              AND ce.id IS NULL
            ORDER BY tc.id
        """),
        {"hid": HOSPITAL_ID},
    ).fetchall()

    print(f"Missing embeddings: {len(rows)}", flush=True)

    service = EmbeddingService(
        CriteriaEmbeddingRepository(db),
        PatientNoteEmbeddingRepository(db),
    )

    for i, row in enumerate(rows, 1):
        criteria_id, description = row

        print(
            f"[{i}/{len(rows)}] Processing {criteria_id}",
            flush=True,
        )

        service.create_trial_embedding(
            criteria_id=criteria_id,
            text=description,
        )

        print(
            f"[{i}/{len(rows)}] SUCCESS",
            flush=True,
        )

    total = db.execute(
        text("""
            SELECT COUNT(*)
            FROM criteria_embeddings ce
            JOIN trial_criteria tc
                ON tc.id = ce.criteria_id
            JOIN trials t
                ON t.id = tc.trial_id
            WHERE t.hospital_id = :hid
        """),
        {"hid": HOSPITAL_ID},
    ).scalar()

    print(f"Total isolation embeddings: {total}", flush=True)

finally:
    db.close()