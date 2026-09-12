"""
tests/unit/telegram/test_media.py
Unit tests for app.telegram.media — media type classification.
No Telegram network connection. All objects are mocked/constructed manually.
"""

import pytest
from unittest.mock import MagicMock, patch

from telethon.tl.types import (
    Message,
    MessageMediaPhoto,
    MessageMediaDocument,
    Document,
    DocumentAttributeAudio,
    DocumentAttributeVideo,
    DocumentAttributeSticker,
    Photo,
)

from app.telegram.media import classify_message, has_media, MediaInfo
from app.db.models.media_record import MediaType


# ---------------------------------------------------------------------------
# Helper builders
# ---------------------------------------------------------------------------

def make_photo_message(ttl: int | None = None) -> MagicMock:
    photo = MagicMock(spec=Photo)
    media = MagicMock(spec=MessageMediaPhoto)
    media.photo = photo
    media.ttl_seconds = ttl
    msg = MagicMock(spec=Message)
    msg.media = media
    msg.message = "a caption"
    return msg


def make_document_message(attrs: list, ttl: int | None = None, caption: str | None = None) -> MagicMock:
    doc = MagicMock(spec=Document)
    doc.attributes = attrs
    media = MagicMock(spec=MessageMediaDocument)
    media.document = doc
    media.ttl_seconds = ttl
    msg = MagicMock(spec=Message)
    msg.media = media
    msg.message = caption
    return msg


def make_empty_message() -> MagicMock:
    msg = MagicMock(spec=Message)
    msg.media = None
    return msg


# ---------------------------------------------------------------------------
# Photo tests
# ---------------------------------------------------------------------------

def test_classify_photo_normal():
    msg = make_photo_message()
    result = classify_message(msg)
    assert result is not None
    assert result.media_type == MediaType.PHOTO
    assert result.is_self_destruct is False
    assert result.ttl_seconds is None
    assert result.caption == "a caption"


def test_classify_photo_timed():
    msg = make_photo_message(ttl=10)
    result = classify_message(msg)
    assert result is not None
    assert result.media_type == MediaType.PHOTO
    assert result.is_self_destruct is True
    assert result.ttl_seconds == 10


# ---------------------------------------------------------------------------
# Video tests
# ---------------------------------------------------------------------------

def test_classify_video():
    attr = MagicMock(spec=DocumentAttributeVideo)
    attr.round_message = False
    msg = make_document_message([attr])
    result = classify_message(msg)
    assert result is not None
    assert result.media_type == MediaType.VIDEO
    assert result.is_self_destruct is False


def test_classify_video_note():
    attr = MagicMock(spec=DocumentAttributeVideo)
    attr.round_message = True
    msg = make_document_message([attr])
    result = classify_message(msg)
    assert result.media_type == MediaType.VIDEO_NOTE


# ---------------------------------------------------------------------------
# Voice tests
# ---------------------------------------------------------------------------

def test_classify_voice():
    attr = MagicMock(spec=DocumentAttributeAudio)
    attr.voice = True
    msg = make_document_message([attr])
    result = classify_message(msg)
    assert result.media_type == MediaType.VOICE


def test_classify_audio_as_document():
    """Regular audio (music) is treated as DOCUMENT."""
    attr = MagicMock(spec=DocumentAttributeAudio)
    attr.voice = False
    msg = make_document_message([attr])
    result = classify_message(msg)
    assert result.media_type == MediaType.DOCUMENT


# ---------------------------------------------------------------------------
# Sticker tests
# ---------------------------------------------------------------------------

def test_classify_sticker():
    attr = MagicMock(spec=DocumentAttributeSticker)
    msg = make_document_message([attr])
    result = classify_message(msg)
    assert result.media_type == MediaType.STICKER


# ---------------------------------------------------------------------------
# Generic document tests
# ---------------------------------------------------------------------------

def test_classify_document_no_known_attrs():
    """A document with no recognized attributes defaults to DOCUMENT."""
    msg = make_document_message([])
    result = classify_message(msg)
    assert result.media_type == MediaType.DOCUMENT


def test_classify_document_timed():
    attr = MagicMock(spec=DocumentAttributeVideo)
    attr.round_message = False
    msg = make_document_message([attr], ttl=30)
    result = classify_message(msg)
    assert result.is_self_destruct is True
    assert result.ttl_seconds == 30


# ---------------------------------------------------------------------------
# No-media tests
# ---------------------------------------------------------------------------

def test_classify_empty_message():
    msg = make_empty_message()
    assert classify_message(msg) is None


def test_classify_none_returns_none():
    assert classify_message(None) is None


def test_has_media_true():
    assert has_media(make_photo_message()) is True


def test_has_media_false():
    assert has_media(make_empty_message()) is False
