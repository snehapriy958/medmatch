-- Owned by: auth-service
-- Source entity: com.medmatch.auth.entity.Role
--
-- Role names are stored as plain text (RoleType enum, EnumType.STRING)
-- rather than a native Postgres enum, matching the Java mapping exactly.

-- Role.java declares no explicit @Column(length=...) for `name`, so
-- Hibernate's ddl-auto=validate expects the JPA/Hibernate default of
-- VARCHAR(255). Using anything shorter here would fail validation on
-- auth-service startup, so this intentionally does not "tighten" the
-- column to the length actually needed by RoleType's values.
CREATE TABLE roles (
    id         UUID PRIMARY KEY,
    name       VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT now(),

    CONSTRAINT uq_roles_name UNIQUE (name)
);
