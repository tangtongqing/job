"""Alembic migration environment for JobPulse."""

from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from src.db.session import Base
import src.db.models  # noqa: F401  Ensure every ORM table is registered.


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

database_url = (
    config.attributes.get("database_url")
    or os.getenv("ALEMBIC_DATABASE_URL")
    or config.get_main_option("sqlalchemy.url")
)
config.set_main_option("sqlalchemy.url", database_url)
target_metadata = Base.metadata


def _migration_options() -> dict[str, object]:
    return {
        "target_metadata": target_metadata,
        "compare_type": True,
        "render_as_batch": database_url.startswith("sqlite"),
    }


def run_migrations_offline() -> None:
    context.configure(
        url=database_url,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        **_migration_options(),
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, **_migration_options())
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
