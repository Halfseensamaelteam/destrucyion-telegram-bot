"""
tests/unit/services/test_capture.py
Unit tests for MediaCaptureService — all DB interactions mocked.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.media_record import MediaRecord, MediaRecordStatus, MediaType
from app.db.repositories import MediaRecordRepository
from app.services.capture import CaptureContext, MediaCaptureService
from app.telegram.media import MediaInfo

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def media_info_photo():
    return MediaInfo(
        media_type=MediaType.PHOTO,
        ttl_seconds=None,
        is_self_destruct=False,
        caption="test caption",
    )


@pytest.fixture
def media_info_timed():
    return MediaInfo(
        media_type=MediaType.VIDEO,
        ttl_seconds=15,
        is_self_destruct=True,
        caption=None,
    )


@pytest.fixture
def base_ctx(media_info_photo):
    return CaptureContext(
        telegram_account_id=1,
        user_id=1,
        source_chat_id=100,
        source_message_id=42,
        media_info=media_info_photo,
        source_chat_title="Test Chat",
        source_chat_username="testchat",
        sender_telegram_id=9001,
        sender_username="sender",
        sender_display_name="Sender Name",
    )


# ---------------------------------------------------------------------------
# Tests: record() — create new
# ---------------------------------------------------------------------------

async def test_record_creates_new(db_session: AsyncSession, user, account, base_ctx, media_info_photo):
    """record() creates a new MediaRecord in PENDING state."""
    base_ctx.user_id = user.id
    base_ctx.telegram_account_id = account.id

    service = MediaCaptureService(db_session)
    record, created = await service.record(base_ctx)

    assert created is True
    assert record.id is not None
    assert record.status == MediaRecordStatus.PENDING
    assert record.media_type == MediaType.PHOTO
    assert record.ttl_seconds is None
    assert record.user_id == user.id
    assert record.telegram_account_id == account.id
    assert record.source_chat_id == 100
    assert record.source_message_id == 42


async def test_record_timed_media(db_session: AsyncSession, user, account, media_info_timed):
    """record() correctly stores TTL for self-destructing media."""
    ctx = CaptureContext(
        telegram_account_id=account.id,
        user_id=user.id,
        source_chat_id=200,
        source_message_id=99,
        media_info=media_info_timed,
    )
    service = MediaCaptureService(db_session)
    record, created = await service.record(ctx)

    assert created is True
    assert record.ttl_seconds == 15
    assert record.media_type == MediaType.VIDEO


# ---------------------------------------------------------------------------
# Tests: record() — idempotency
# ---------------------------------------------------------------------------

async def test_record_duplicate_returns_existing(db_session: AsyncSession, user, account, base_ctx):
    """Second call with same (account, chat, msg) returns existing record and created=False."""
    base_ctx.user_id = user.id
    base_ctx.telegram_account_id = account.id

    service = MediaCaptureService(db_session)
    record1, created1 = await service.record(base_ctx)
    record2, created2 = await service.record(base_ctx)

    assert created1 is True
    assert created2 is False
    assert record1.id == record2.id


# ---------------------------------------------------------------------------
# Tests: mark_saved()
# ---------------------------------------------------------------------------

async def test_mark_saved(db_session: AsyncSession, user, account, base_ctx):
    base_ctx.user_id = user.id
    base_ctx.telegram_account_id = account.id

    service = MediaCaptureService(db_session)
    record, _ = await service.record(base_ctx)
    assert record.status == MediaRecordStatus.PENDING

    saved = await service.mark_saved(record, saved_message_id=8888)
    assert saved.status == MediaRecordStatus.SAVED
    assert saved.saved_message_id == 8888
    assert saved.saved_at is not None


# ---------------------------------------------------------------------------
# Tests: mark_failed()
# ---------------------------------------------------------------------------

async def test_mark_failed(db_session: AsyncSession, user, account, base_ctx):
    base_ctx.user_id = user.id
    base_ctx.telegram_account_id = account.id

    service = MediaCaptureService(db_session)
    record, _ = await service.record(base_ctx)

    failed = await service.mark_failed(record, error="Timeout while forwarding")
    assert failed.status == MediaRecordStatus.FAILED
    assert "Timeout" in failed.error
