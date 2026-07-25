CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS vector;
-- =====================================================
-- Hospitals
-- =====================================================

CREATE TABLE hospitals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    address VARCHAR(500)
);

-- =====================================================
-- Users
-- =====================================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,

    hospital_id UUID NOT NULL,

    CONSTRAINT fk_users_hospital
        FOREIGN KEY (hospital_id)
        REFERENCES hospitals(id)
);

-- =====================================================
-- Audit Logs
-- =====================================================

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    action VARCHAR(50) NOT NULL,

    resource_type VARCHAR(100) NOT NULL,
    resource_id UUID NOT NULL,

    performed_by_id UUID NOT NULL,
    performed_by_username VARCHAR(100) NOT NULL,
    performed_by_role VARCHAR(50) NOT NULL,

    hospital_id UUID NOT NULL,
    hospital_name VARCHAR(255) NOT NULL,

    details VARCHAR(1000),
    ip_address VARCHAR(45),

    created_at TIMESTAMP NOT NULL
);

-- =====================================================
-- Indexes
-- =====================================================

CREATE INDEX idx_audit_created_at
ON audit_logs(created_at);

CREATE INDEX idx_audit_action
ON audit_logs(action);

CREATE INDEX idx_audit_resource_type
ON audit_logs(resource_type);

CREATE INDEX idx_audit_resource_id
ON audit_logs(resource_id);

CREATE INDEX idx_audit_user
ON audit_logs(performed_by_id);

CREATE INDEX idx_audit_hospital
ON audit_logs(hospital_id);
