ALTER TABLE audit_logs
ADD COLUMN IF NOT EXISTS performed_by_id UUID;

ALTER TABLE audit_logs
ADD COLUMN IF NOT EXISTS performed_by_username VARCHAR(255);

ALTER TABLE audit_logs
ADD COLUMN IF NOT EXISTS performed_by_role VARCHAR(100);

ALTER TABLE audit_logs
ADD COLUMN IF NOT EXISTS hospital_id UUID;

ALTER TABLE audit_logs
ADD COLUMN IF NOT EXISTS hospital_name VARCHAR(255);