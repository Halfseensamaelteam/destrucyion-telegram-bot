import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    MediaRecord,
    MediaRecordStatus,
    MediaType,
    Subscription,
    SubscriptionPlan,
    SubscriptionStatus,
    TelegramAccount,
    TelegramAccountStatus,
    User,
)
from datetime import datetime, timezone

pytestmark = pytest.mark.asyncio


async def test_create_user(db_session: AsyncSession) -> None:
    user = User(telegram_user_id=123, username="testuser")
    db_session.add(user)
    await db_session.commit()

    assert user.id is not None
    assert user.created_at is not None


async def test_create_telegram_account(db_session: AsyncSession) -> None:
    user = User(telegram_user_id=123)
    db_session.add(user)
    await db_session.flush()

    account = TelegramAccount(
        user_id=user.id,
        telegram_user_id=456,
        status=TelegramAccountStatus.ACTIVE,
    )
    db_session.add(account)
    await db_session.commit()

    assert account.id is not None
    assert account.status == TelegramAccountStatus.ACTIVE


async def test_create_subscription(db_session: AsyncSession) -> None:
    user = User(telegram_user_id=123)
    db_session.add(user)
    await db_session.flush()

    now = datetime.now(timezone.utc)
    sub = Subscription(
        user_id=user.id,
        plan=SubscriptionPlan.MONTHLY,
        starts_at=now,
        status=SubscriptionStatus.ACTIVE,
    )
    db_session.add(sub)
    await db_session.commit()

    assert sub.id is not None


async def test_media_record_idempotency_constraint(db_session: AsyncSession) -> None:
    """Test that the unique constraint on (telegram_account_id, source_chat_id, source_message_id) works."""
    user = User(telegram_user_id=123)
    db_session.add(user)
    await db_session.flush()

    account = TelegramAccount(user_id=user.id)
    db_session.add(account)
    await db_session.flush()

    record1 = MediaRecord(
        user_id=user.id,
        telegram_account_id=account.id,
        source_chat_id=1001,
        source_message_id=2002,
        media_type=MediaType.PHOTO,
        status=MediaRecordStatus.PENDING,
    )
    db_session.add(record1)
    await db_session.commit()

    # Attempt to insert exact same idempotency keys
    record2 = MediaRecord(
        user_id=user.id,
        telegram_account_id=account.id,
        source_chat_id=1001,
        source_message_id=2002,
        media_type=MediaType.VIDEO, # Different type, but keys are same
        status=MediaRecordStatus.PENDING,
    )
    db_session.add(record2)
    with pytest.raises(IntegrityError):
        await db_session.commit()
