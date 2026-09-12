"""
app.telegram.metadata
~~~~~~~~~~~~~~~~~~~~~
Sender and chat metadata extraction from Telethon objects.

Handles all real-world sender identity cases without confusing them:
  - User with username
  - User without username (first/last name only)
  - User with no name at all (deleted/unknown account)
  - Group/channel context (sender may be the group itself)
  - Anonymous group admin (sender_id may be the chat id)
  - Forwarded messages (keeps original sender)
  - Channel post (no personal sender)

Design rule: sender identity must NEVER be confused between accounts.
Each result is fully self-contained — no shared state.

This module is pure: it takes Telethon TL objects and returns plain dataclasses.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SenderInfo:
    """Resolved information about the sender of a Telegram message.

    All fields are optional because any of them may be absent in practice.

    Attributes:
        telegram_id: Telegram user/channel ID. None for anonymous senders.
        username: @username without the @. None if not set.
        display_name: Human-readable name (first + last, or channel title).
        is_anonymous: True when the sender acted as an anonymous group admin.
        is_channel: True when the message was sent by a channel/linked post.
    """

    telegram_id: int | None
    username: str | None
    display_name: str | None
    is_anonymous: bool
    is_channel: bool

    @property
    def identity_label(self) -> str:
        """A human-readable identity string for use in captions.

        Priority: @username → display_name → ID → "Anonymous" → "Unknown"

        This string is NEVER used as an identifier — only for display.
        """
        if self.is_anonymous:
            return "Anonymous Admin"
        if self.username:
            return f"@{self.username}"
        if self.display_name:
            return self.display_name
        if self.telegram_id:
            return f"ID:{self.telegram_id}"
        return "Unknown"


@dataclass(frozen=True)
class ChatInfo:
    """Resolved information about the chat a message arrived from.

    Attributes:
        chat_id: Telegram chat/peer ID.
        title: Display name of the chat (group title, channel name, or user name).
        username: @username of the chat (if public). None for private chats.
        is_private: True for direct/private messages.
        is_group: True for groups and supergroups.
        is_channel: True for broadcast channels.
    """

    chat_id: int
    title: str | None
    username: str | None
    is_private: bool
    is_group: bool
    is_channel: bool

    @property
    def display_label(self) -> str:
        """A human-readable label for this chat, for use in captions."""
        if self.username:
            return f"@{self.username}"
        if self.title:
            return self.title
        return f"Chat:{self.chat_id}"


def extract_sender(sender_obj) -> SenderInfo:
    """Extract SenderInfo from a Telethon User, Channel, or None object.

    Handles:
      - telethon.tl.types.User (normal user, possibly deleted)
      - telethon.tl.types.Channel (channel/megagroup acting as sender)
      - None (anonymous or missing sender)

    Args:
        sender_obj: The result of event.get_sender() or message.get_sender().

    Returns:
        SenderInfo with all available fields populated.
    """
    if sender_obj is None:
        return SenderInfo(
            telegram_id=None,
            username=None,
            display_name=None,
            is_anonymous=True,
            is_channel=False,
        )

    # Channel or megagroup acting as a sender
    type_name = type(sender_obj).__name__
    if type_name == "Channel":
        return SenderInfo(
            telegram_id=getattr(sender_obj, "id", None),
            username=getattr(sender_obj, "username", None),
            display_name=getattr(sender_obj, "title", None),
            is_anonymous=False,
            is_channel=True,
        )

    # Normal user
    telegram_id = getattr(sender_obj, "id", None)
    username = getattr(sender_obj, "username", None) or None
    first = (getattr(sender_obj, "first_name", None) or "").strip()
    last = (getattr(sender_obj, "last_name", None) or "").strip()
    display_name = " ".join(filter(None, [first, last])) or None

    # Deleted/unknown accounts have no name
    is_deleted = getattr(sender_obj, "deleted", False)
    if is_deleted:
        display_name = "Deleted Account"

    return SenderInfo(
        telegram_id=telegram_id,
        username=username,
        display_name=display_name,
        is_anonymous=False,
        is_channel=False,
    )


def extract_chat(chat_obj, chat_id: int) -> ChatInfo:
    """Extract ChatInfo from a Telethon Chat/Channel/User object.

    Args:
        chat_obj: The result of event.get_chat(). May be None.
        chat_id: Fallback chat ID if chat_obj is unavailable.

    Returns:
        ChatInfo with all available fields populated.
    """
    if chat_obj is None:
        return ChatInfo(
            chat_id=chat_id,
            title=None,
            username=None,
            is_private=False,
            is_group=False,
            is_channel=False,
        )

    type_name = type(chat_obj).__name__
    title: str | None = None
    username: str | None = getattr(chat_obj, "username", None) or None
    is_private = False
    is_group = False
    is_channel = False

    if type_name == "User":
        is_private = True
        first = (getattr(chat_obj, "first_name", None) or "").strip()
        last = (getattr(chat_obj, "last_name", None) or "").strip()
        title = " ".join(filter(None, [first, last])) or None

    elif type_name == "Channel":
        is_megagroup = getattr(chat_obj, "megagroup", False)
        if is_megagroup:
            is_group = True
        else:
            is_channel = True
        title = getattr(chat_obj, "title", None)

    elif type_name in ("Chat", "ChatFull"):
        is_group = True
        title = getattr(chat_obj, "title", None)

    return ChatInfo(
        chat_id=chat_id,
        title=title,
        username=username,
        is_private=is_private,
        is_group=is_group,
        is_channel=is_channel,
    )


def build_caption(
    sender: SenderInfo,
    chat: ChatInfo,
    media_type: str,
    ttl_seconds: int | None = None,
    original_caption: str | None = None,
) -> str:
    """Build a Saved Messages caption for a captured media item.

    Format:
        📥 [Media type] from [sender] in [chat]
        ⏱ Self-destructing (10s)   ← only for timed media
        💬 [original caption]       ← only if present

    Args:
        sender: Resolved SenderInfo.
        chat: Resolved ChatInfo.
        media_type: String like "photo", "video", etc.
        ttl_seconds: TTL for self-destructing media. None = not timed.
        original_caption: The original message caption if any.

    Returns:
        A plain-text caption string.
    """
    type_emoji = {
        "photo": "🖼",
        "video": "🎬",
        "voice": "🎙",
        "video_note": "📹",
        "document": "📄",
        "sticker": "🎭",
    }.get(media_type, "📥")

    lines = [
        f"{type_emoji} {media_type.replace('_', ' ').title()} from "
        f"{sender.identity_label} in {chat.display_label}"
    ]

    if ttl_seconds is not None:
        lines.append(f"⏱ Self-destructing ({ttl_seconds}s)")

    if original_caption:
        lines.append(f'💬 "{original_caption}"')

    return "\n".join(lines)
