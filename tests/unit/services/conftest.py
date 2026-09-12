"""
tests/unit/services/conftest.py
Shared fixtures for service-layer unit tests.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.user_repo import UserRepository
from app.db.repositories.telegram_account_repo import TelegramAccountRepository
from app.db.models.telegram_account import TelegramAccountStatus


@pytest.fixture
async def user(db_session: AsyncSession):
    repo = UserRepository(db_session)
    return await repo.create(telegram_user_id=1001)


@pytest.fixture
async def account(db_session: AsyncSession, user):
    repo = TelegramAccountRepository(db_session)
    return await repo.create(
        user_id=user.id,
        phone_masked="+628****6789",
        status=TelegramAccountStatus.ACTIVE,
    )
