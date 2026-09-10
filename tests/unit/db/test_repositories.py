import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone, timedelta

from app.db.models import (
    MediaRecordStatus,
    MediaType,
    SubscriptionPlan,
    SubscriptionStatus,
    TelegramAccountStatus,
)
from app.db.repositories import (
    MediaRecordRepository,
    SubscriptionRepository,
    TelegramAccountRepository,
    UserRepository,
)

pytestmark = pytest.mark.asyncio


async def test_user_repository(db_session: AsyncSession) -> None:
    repo = UserRepository(db_session)
    
    user1, created = await repo.get_or_create(telegram_user_id=111, username="test1")
    assert created is True
    assert user1.id is not None
    
    user2, created = await repo.get_or_create(telegram_user_id=111, username="test_changed")
    assert created is False
    assert user1.id == user2.id


async def test_telegram_account_repository_tenant_isolation(db_session: AsyncSession) -> None:
    user_repo = UserRepository(db_session)
    account_repo = TelegramAccountRepository(db_session)

    user_a = await user_repo.create(telegram_user_id=1)
    user_b = await user_repo.create(telegram_user_id=2)

    account_a = await account_repo.create(user_id=user_a.id, telegram_user_id=10)
    account_b = await account_repo.create(user_id=user_b.id, telegram_user_id=20)

    # User A tries to fetch User B's account
    fetched = await account_repo.get_by_id_and_user(account_b.id, user_a.id)
    assert fetched is None  # Should be protected

    # User B fetches own account
    fetched = await account_repo.get_by_id_and_user(account_b.id, user_b.id)
    assert fetched is not None
    assert fetched.id == account_b.id


async def test_subscription_repository(db_session: AsyncSession) -> None:
    user_repo = UserRepository(db_session)
    sub_repo = SubscriptionRepository(db_session)

    user = await user_repo.create(telegram_user_id=1)
    now = datetime.now(timezone.utc)
    
    sub = await sub_repo.create(
        user_id=user.id,
        plan=SubscriptionPlan.WEEKLY,
        starts_at=now - timedelta(days=1),
        expires_at=now + timedelta(days=6)
    )

    assert await sub_repo.is_active(user.id) is True

    await sub_repo.expire(sub)
    assert await sub_repo.is_active(user.id) is False


async def test_media_record_repository_idempotency(db_session: AsyncSession) -> None:
    user_repo = UserRepository(db_session)
    account_repo = TelegramAccountRepository(db_session)
    media_repo = MediaRecordRepository(db_session)

    user = await user_repo.create(telegram_user_id=1)
    account = await account_repo.create(user_id=user.id)

    # First time seeing media
    record1, created1 = await media_repo.create_or_skip(
        user_id=user.id,
        telegram_account_id=account.id,
        source_chat_id=100,
        source_message_id=200,
        media_type=MediaType.PHOTO,
    )
    assert created1 is True
    assert record1.id is not None

    # See the exact same media again (duplicate update from Telegram)
    record2, created2 = await media_repo.create_or_skip(
        user_id=user.id,
        telegram_account_id=account.id,
        source_chat_id=100,
        source_message_id=200,
        media_type=MediaType.PHOTO,
    )
    assert created2 is False
    assert record1.id == record2.id  # Same record returned, no crash
