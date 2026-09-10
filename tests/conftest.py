"""
tests/conftest.py
~~~~~~~~~~~~~~~~~
Shared pytest fixtures and configuration.
"""

import os

import pytest


@pytest.fixture(autouse=True)
def reset_settings_cache():
    """Clear the lru_cache on get_settings() after each test.

    This ensures that environment variable changes in tests are picked up
    without cross-test contamination.
    """
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
