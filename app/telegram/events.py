"""
app.telegram.events
~~~~~~~~~~~~~~~~~~~~
Telethon event handler factory for media capture.

This module provides `make_handler_factory()` which returns a function
suitable for the `handler_factory` argument in `TelegramClientManager`.

Each account gets its own set of event handlers, bound to that account's
context. Handlers are isolated — a crash in one account's handler
does not affect other accounts.

Design:
  - Handlers are pure functions of (event, context). No shared state.
  - DB sessions are created per-event from the session_factory.
  - All exceptions are caught and logged. The handler never raises.
  - Media classification uses app.telegram.media (pure, no network).
  - Captured records are persisted via MediaCaptureService.
  - Saving to Saved Messages is intentionally NOT done here (Phase 9).
"""

from __future__ import annotations

from typing import Callable

from sqlalchemy.ext.asyncio import AsyncSession
from telethon import events
from telethon.tl.types import Message

from app.core.logging import get_logger
from app.services.capture import CaptureContext, MediaCaptureService
from app.telegram.media import classify_message

log = get_logger(__name__)


def make_handler_factory(
    session_factory: Callable[[], AsyncSession],
) -> Callable:
    """Return a handler_factory compatible with TelegramClientManager.

    The factory itself takes (manager, account_id) and returns a list of
    (callback, event_builder) tuples ready for client.add_event_handler().

    Args:
        session_factory: The async session factory (same one given to the manager).

    Returns:
        A handler_factory function.
    """

    def handler_factory(manager, account_id: int) -> list:
        """Build handlers for a specific account's Telethon client."""

        async def on_new_message(event: events.NewMessage.Event) -> None:
            """Fired for every new message received by this account."""
            try:
                await _handle_message(
                    event=event,
                    account_id=account_id,
                    manager=manager,
                    session_factory=session_factory,
                )
            except Exception as exc:
                log.error(
                    "event_handler_unhandled_error",
                    account_id=account_id,
                    error=str(exc),
                )

        return [
            (on_new_message, events.NewMessage()),
        ]

    return handler_factory


async def _handle_message(
    *,
    event: events.NewMessage.Event,
    account_id: int,
    manager,
    session_factory: Callable[[], AsyncSession],
) -> None:
    """Process a single new message for a given account.

    1. Classify media (pure, no network).
    2. If no capturable media → ignore silently.
    3. Get account's user_id from the manager's client registry.
    4. Create a DB session (isolated per event).
    5. Build CaptureContext from message metadata.
    6. Record via MediaCaptureService (idempotent).
    7. Log result; forwarding to Saved Messages deferred to Phase 9.
    """
    message: Message = event.message

    # Step 1-2: classify
    media_info = classify_message(message)
    if media_info is None:
        return

    # Step 3: get user_id from manager's registry
    managed = manager._clients.get(account_id)
    if managed is None:
        log.warning("event_account_not_in_manager", account_id=account_id)
        return
    user_id = managed.user_id

    # Step 4-6: DB session per event — never shared across events
    async with session_factory() as session:
        ctx = await _build_context(
            event=event,
            message=message,
            account_id=account_id,
            user_id=user_id,
            media_info=media_info,
        )
        service = MediaCaptureService(session)
        record, created = await service.record(ctx)
        await session.commit()

    if created:
        log.info(
            "media_captured",
            account_id=account_id,
            record_id=record.id,
            media_type=record.media_type,
            ttl=record.ttl_seconds,
            is_timed=media_info.is_self_destruct,
        )
        # Phase 9: forward record to Saved Messages here.
    else:
        log.debug("media_already_known", account_id=account_id, record_id=record.id)


async def _build_context(
    *,
    event: events.NewMessage.Event,
    message: Message,
    account_id: int,
    user_id: int,
    media_info,
) -> CaptureContext:
    """Extract all metadata from the Telethon event into a CaptureContext."""
    # Chat metadata
    source_chat_id = event.chat_id
    source_chat_title: str | None = None
    source_chat_username: str | None = None

    try:
        chat = await event.get_chat()
        if chat:
            source_chat_title = getattr(chat, "title", None) or getattr(
                chat, "first_name", None
            )
            source_chat_username = getattr(chat, "username", None)
    except Exception:
        pass  # Best effort — metadata failure must not break capture

    # Sender metadata
    sender_telegram_id: int | None = None
    sender_username: str | None = None
    sender_display_name: str | None = None

    try:
        sender = await event.get_sender()
        if sender:
            sender_telegram_id = getattr(sender, "id", None)
            sender_username = getattr(sender, "username", None)
            first = getattr(sender, "first_name", None) or ""
            last = getattr(sender, "last_name", None) or ""
            full_name = f"{first} {last}".strip()
            sender_display_name = full_name or None
    except Exception:
        pass  # Best effort

    return CaptureContext(
        telegram_account_id=account_id,
        user_id=user_id,
        source_chat_id=source_chat_id,
        source_message_id=message.id,
        media_info=media_info,
        source_chat_title=source_chat_title,
        source_chat_username=source_chat_username,
        sender_telegram_id=sender_telegram_id,
        sender_username=sender_username,
        sender_display_name=sender_display_name,
    )
