"""
Alembic environment configuration for destrucyion-telegram-bot.

Supports async engines (asyncpg for PostgreSQL, aiosqlite for SQLite).
DATABASE_URL is read from the environment / .env file — never hard-coded.
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

# --------------------------------------------------------------------------- #
# Import all models so Alembic can auto-detect schema changes                  #
# --------------------------------------------------------------------------- #
import app.db.models  # noqa: F401 — registers all models with Base.metadata
from app.db.models.base import Base
from app.core.config import get_settings

# --------------------------------------------------------------------------- #
# Alembic config object from alembic.ini                                       #
# --------------------------------------------------------------------------- #
config = context.config

# Set up Python logging from the alembic.ini [loggers] section
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override sqlalchemy.url from our Settings so credentials come from .env
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = Base.metadata


# --------------------------------------------------------------------------- #
# Migration runners                                                            #
# --------------------------------------------------------------------------- #

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (no live DB connection needed)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,  # Required for SQLite ALTER TABLE support
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=True,  # Required for SQLite ALTER TABLE support
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode (connects to the actual DB)."""
    engine = create_async_engine(settings.database_url, echo=False)
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
