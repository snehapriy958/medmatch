-- Owned by: auth-service (this migration), but the COLUMN SET is a
-- shared contract with the AI service, which writes directly to this
-- table (see services/ai-service/app/models/audit_log.py and
-- app/repositories/audit_log_repository.py).
--
-- auth-service's Java entity (entity/AuditLog.java) intentionally
-- maps only 8 of these 12 columns. The 4 AI-service-only columns
-- (performed_by_username, performed_by_role, hospital_id,
-- hospital_name) are always NULL on rows written by auth-service and
-- populated only by the AI service, from JWT claims, at write time.
-- This is a deliberate minimal-compatibility decision, not an
-- oversight — see the comment on AuditLog.java for the full
-- explanation and the plan for a possible future full-parity change.
--
-- DO NOT remove or "clean up" the 4 AI-service-only columns to match
-- the Java entity — doing so would break AI-service audit writes.

CREATE TABLE audit_logs (
    id                     UUID PRIMARY KEY,
    performed_by_id        UUID,
    action                 VARCHAR(100) NOT NULL,
    resource_type          VARCHAR(100),
    resource_id            UUID,
    ip_address              VARCHAR(255),
    details                TEXT,
    created_at             TIMESTAMP NOT NULL DEFAULT now(),

    -- AI-service-only columns (see note above). Deliberately no
    -- foreign keys on performed_by_id / hospital_id, matching both
    -- services' entities: audit rows must survive deletion of the
    -- user or hospital they reference.
    performed_by_username  VARCHAR(255),
    performed_by_role      VARCHAR(50),
    hospital_id            UUID,
    hospital_name          VARCHAR(255)
);

CREATE INDEX ix_audit_logs_performed_by_id ON audit_logs (performed_by_id);
CREATE INDEX ix_audit_logs_hospital_id ON audit_logs (hospital_id);
