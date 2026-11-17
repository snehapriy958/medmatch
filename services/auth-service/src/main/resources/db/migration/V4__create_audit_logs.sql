CREATE TABLE audit_logs (

    id UUID PRIMARY KEY,

    user_id UUID NOT NULL,

    action VARCHAR(100) NOT NULL,

    resource VARCHAR(255) NOT NULL,

    details TEXT,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP

);