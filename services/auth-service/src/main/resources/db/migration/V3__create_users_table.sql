-- Owned by: auth-service
-- Source entity: com.medmatch.auth.entity.User
--
-- No explicit @Column(length=...) is declared for any VARCHAR field on
-- User.java, so each defaults to Hibernate's standard VARCHAR(255).

CREATE TABLE users (
    id         UUID PRIMARY KEY,
    email      VARCHAR(255) NOT NULL,
    password   VARCHAR(255) NOT NULL,
    first_name VARCHAR(255) NOT NULL,
    last_name  VARCHAR(255) NOT NULL,
    phone      VARCHAR(255),
    role_id    UUID NOT NULL,
    hospital_id UUID NOT NULL,
    enabled    BOOLEAN NOT NULL DEFAULT true,
    status     VARCHAR(255) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now(),

    CONSTRAINT uq_users_email UNIQUE (email),

    CONSTRAINT fk_users_role
        FOREIGN KEY (role_id) REFERENCES roles (id),

    CONSTRAINT fk_users_hospital
        FOREIGN KEY (hospital_id) REFERENCES hospitals (id)
);

CREATE INDEX ix_users_role_id ON users (role_id);
CREATE INDEX ix_users_hospital_id ON users (hospital_id);
