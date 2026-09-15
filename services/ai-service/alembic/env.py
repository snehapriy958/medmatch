from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# App imports: use the application's own settings (DATABASE_URL) and
# the full SQLAlchemy model registry, so Alembic autogenerate compares
# against exactly what the app actually maps.
from app.config.settings import settings
from app.db.base import Base
from app.models import (  # noqa: F401 - imported for metadata registration
    AuditLog,
    CriteriaEmbedding,
    Hospital,
    Patient,
    PatientNote,
    PatientNoteEmbedding,
    Trial,
    TrialCriteria,
    TrialEmbedding,
)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Use the application's own DATABASE_URL rather than a value hardcoded
# in alembic.ini, so this stays a single source of truth with the app.
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

target_metadata = Base.metadata

# Tables owned (migrated) by auth-service via Flyway. This is the
# full list, not just the tables the AI service happens to also map:
# `roles` and `users` have no SQLAlchemy model in this service at all,
# but autogenerate would otherwise see them in the live DB, find no
# corresponding model, and propose DROP TABLE — which must never
# happen. `hospitals` and `audit_logs` DO have AI-service SQLAlchemy
# models (Hospital: read-only reference lookups; AuditLog: writes to
# the shared 12-column table), but ownership of their DDL still
# belongs entirely to auth-service.
#
# This filter keeps `alembic revision --autogenerate` from ever
# proposing a CREATE/ALTER/DROP for any of these four tables.
AUTH_SERVICE_OWNED_TABLES = {"roles", "hospitals", "users", "audit_logs"}


def include_object(object, name, type_, reflected, compare_to):
    if type_ == "table" and name in AUTH_SERVICE_OWNED_TABLES:
        return False
    return True

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
