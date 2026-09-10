"""
tests/conftest.py
~~~~~~~~~~~~~~~~~
Shared pytest fixtures and configuration.
"""

import os

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.db.models.base import Base
import app.db.models  # noqa: F401 — registers all models


@pytest.fixture(autouse=True)
def reset_settings_cache():
    """Clear the lru_cache on get_settings() after each test."""
    from app.core.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def minimal_env(monkeypatch):
    """Set minimal required environment variables for Settings to load cleanly."""
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("APP_SECRET_KEY", "test-secret-key-for-testing")
    monkeypatch.setenv("TELEGRAM_API_ID", "12345")
    monkeypatch.setenv("TELEGRAM_API_HASH", "testhash")
    monkeypatch.setenv("BOT_TOKEN", "123456:test-token")
    return None


@pytest_asyncio.fixture
async def db_engine():
    """In-memory SQLite async engine for database tests.

    Creates all tables before the test, drops them after.
    No external database required.
    """
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    """Async SQLAlchemy session bound to the in-memory test engine.

    Each test gets a fresh transaction that is rolled back on teardown,
    keeping tests fully isolated.
    """
    factory = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    async with factory() as session:
        yield session
