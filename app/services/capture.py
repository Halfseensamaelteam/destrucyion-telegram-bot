"""
app.services.capture
~~~~~~~~~~~~~~~~~~~~
MediaCaptureService — high-level service that processes a single Telegram message.

Responsibilities:
  1. Classify media type (delegates to app.telegram.media).
  2. Idempotency check via DB UNIQUE constraint (never Python set()).
  3. Create a MediaRecord row in PENDING state.
  4. Return the record for the caller (worker event handler) to forward
     to Saved Messages.

What this service does NOT do:
  - Does NOT forward media to Saved Messages (Phase 9).
  - Does NOT store sender metadata beyond what the caller supplies (Phase 8).
  - Does NOT download or buffer media bytes.

All idempotency is database-enforced as per AGENTS.md rule 7.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models.media_record import MediaRecord, MediaRecordStatus
from app.db.repositories.media_record_repo import MediaRecordRepository
from app.telegram.media import MediaInfo

log = get_logger(__name__)


class DuplicateMediaError(Exception):
    """Raised when a media record already exists for this (account, chat, message)."""


@dataclass
class CaptureContext:
    """All context needed to record a media event from a Telegram account.

    Attributes:
        telegram_account_id: The ID of the TelegramAccount row.
        user_id: The application user who owns the account.
        source_chat_id: Telegram chat/peer ID where the message arrived.
        source_message_id: Telegram message ID (used for idempotency).
        media_info: Result of classify_message().
        source_chat_title: Display name of the source chat.
        source_chat_username: Username of the source chat (if any).
        sender_telegram_id: Telegram user ID of the sender.
        sender_username: Telegram username of the sender.
        sender_display_name: Human-readable name of the sender.
    """

    telegram_account_id: int
    user_id: int
    source_chat_id: int
    source_message_id: int
    media_info: MediaInfo
    source_chat_title: str | None = None
    source_chat_username: str | None = None
    sender_telegram_id: int | None = None
    sender_username: str | None = None
    sender_display_name: str | None = None


class MediaCaptureService:
    """Records incoming media events from a Telegram account to the database.

    This service is designed to be called from within an account's Telethon
    event handler in the worker process.

    It is intentionally scoped to DB operations only. Network/Telethon operations
    (forwarding to Saved Messages) belong in a separate service (Phase 9).
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = MediaRecordRepository(session)

    async def record(self, ctx: CaptureContext) -> tuple[MediaRecord, bool]:
        """Create a MediaRecord for the given context, or return the existing one.

        Idempotency is enforced at the database level via the UNIQUE constraint
        on (telegram_account_id, source_chat_id, source_message_id).

        Returns:
            (MediaRecord, created) where created=False means it already existed.

        Never raises on duplicate — just returns the existing record with
        created=False. Only raises on unexpected DB errors.
        """
        record, created = await self._repo.create_or_skip(
            user_id=ctx.user_id,
            telegram_account_id=ctx.telegram_account_id,
            source_chat_id=ctx.source_chat_id,
            source_message_id=ctx.source_message_id,
            media_type=ctx.media_info.media_type,
            source_chat_title=ctx.source_chat_title,
            source_chat_username=ctx.source_chat_username,
            sender_telegram_id=ctx.sender_telegram_id,
            sender_username=ctx.sender_username,
            sender_display_name=ctx.sender_display_name,
            ttl_seconds=ctx.media_info.ttl_seconds,
            status=MediaRecordStatus.PENDING,
        )

        if created:
            log.info(
                "media_recorded",
                account_id=ctx.telegram_account_id,
                msg_id=ctx.source_message_id,
                type=ctx.media_info.media_type,
                ttl=ctx.media_info.ttl_seconds,
                is_timed=ctx.media_info.is_self_destruct,
            )
        else:
            log.debug(
                "media_duplicate_skipped",
                account_id=ctx.telegram_account_id,
                msg_id=ctx.source_message_id,
            )

        return record, created

    async def mark_saved(
        self,
        record: MediaRecord,
        *,
        saved_message_id: int,
    ) -> MediaRecord:
        """Update a MediaRecord to SAVED status after successful forwarding.

        Called by the Phase 9 Saved Messages service after a successful send.
        """
        from datetime import datetime, timezone

        return await self._repo.mark_saved(
            record,
            saved_message_id=saved_message_id,
            saved_at=datetime.now(timezone.utc),
        )

    async def mark_failed(self, record: MediaRecord, *, error: str) -> MediaRecord:
        """Update a MediaRecord to FAILED status."""
        log.warning(
            "media_capture_failed",
            record_id=record.id,
            error=error,
        )
        return await self._repo.mark_failed(record, error=error)
