from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

import app.models  # noqa: F401  (import registers every table on Base.metadata)
from alembic import context
from app.core.config import get_settings
from app.core.db import Base

config = context.config
config.set_main_option("sqlalchemy.url", get_settings().database_url)
if config.config_file_name:
    fileConfig(config.config_file_name)
target_metadata = Base.metadata


def _include_object(obj, name, type_, reflected, compare_to):
    # Only manage tables defined in our models; ignore the PostGIS / Tiger /
    # topology system tables that ship with the postgis image.
    if type_ == "table":
        return name in target_metadata.tables
    return True


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=_include_object,
        )
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
