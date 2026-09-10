"""
app.db.session
~~~~~~~~~~~~~~
Async SQLAlchemy engine and session factory.

Supports both PostgreSQL (asyncpg) and SQLite (aiosqlite) via DATABASE_URL.
The correct driver is selected automatically from the URL scheme:
    postgresql+asyncpg://...
    sqlite+aiosqlite:///...
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _get_engine() -> AsyncEngine:
    """Return the singleton async engine, creating it on first call."""
    global _engine
    if _engine is None:
        settings = get_settings()
        connect_args: dict = {}
        if settings.database_url.startswith("sqlite"):
            # SQLite requires check_same_thread=False for async use
            connect_args["check_same_thread"] = False
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.is_development,
            pool_pre_ping=True,
            connect_args=connect_args,
        )
    return _engine


def _get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the singleton async session factory."""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=_get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _session_factory


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields one AsyncSession per request.

    Usage::

        async def my_endpoint(session: AsyncSession = Depends(get_session)):
            ...
    """
    factory = _get_session_factory()
    async with factory() as session:
        yield session


async def create_all_tables() -> None:
    """Create all tables (development/test helper — use Alembic in production)."""
    from app.db.models import Base  # noqa: PLC0415 — avoid circular import at module level

    async with _get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_all_tables() -> None:
    """Drop all tables (test helper only — never use in production)."""
    from app.db.models import Base  # noqa: PLC0415

    async with _get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


def override_engine(engine: AsyncEngine) -> None:
    """Replace the engine with a test engine. Call before any session usage."""
    global _engine, _session_factory
    _engine = engine
    _session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
