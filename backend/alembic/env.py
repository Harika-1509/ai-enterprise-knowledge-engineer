import sys
from pathlib import Path
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Add backend/ to Python path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.config import settings
from app.core.database import Base

# Import all ORM models so Alembic can discover them during autogeneration.
# noqa prevents lint warnings about unused imports.
from app.models import User, Document, Chat, ChatMessage  # noqa: F401

# Alembic Config object
config = context.config

# Use the DATABASE_URL from our application settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Configure Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# -------------------------------------------------------------------------
# Metadata used by Alembic autogenerate
# -------------------------------------------------------------------------
# Alembic compares this metadata against the actual database schema
# to automatically generate migration scripts.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    In offline mode Alembic doesn't create a database connection.
    Instead it generates SQL migration scripts.
    """

    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    In online mode Alembic connects directly to the database and
    applies migrations.
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
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()