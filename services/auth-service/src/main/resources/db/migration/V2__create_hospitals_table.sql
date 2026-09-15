-- Owned by: auth-service
-- Source entity: com.medmatch.auth.entity.Hospital
--
-- Shared reference table. Also mapped read-only in the AI service
-- (app/models/hospital.py) via HospitalRepository.get_by_id — the
-- AI service never creates, alters, or writes to this table.
--
-- Column set is identical between the two mappings (id, code, name,
-- address, active, created_at, updated_at); no reconciliation was
-- needed here, unlike audit_logs.

CREATE TABLE hospitals (
    id         UUID PRIMARY KEY,
    code       VARCHAR(255) NOT NULL,
    name       VARCHAR(255) NOT NULL,
    address    VARCHAR(255),
    active     BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now(),

    CONSTRAINT uq_hospitals_code UNIQUE (code)
);

CREATE INDEX ix_hospitals_name ON hospitals (name);
