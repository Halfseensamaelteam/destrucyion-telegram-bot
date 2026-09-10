"""
tests/unit/core/test_crypto.py
Tests for SessionCipher — encrypt/decrypt Fernet session strings.
"""

import pytest
from cryptography.fernet import Fernet

from app.core.crypto import SessionCipher, SessionEncryptionError, generate_key


FAKE_SESSION = "1BVtsOH8BuzrFdBvLFIBvhOvNwE_FAKE_SESSION_STRING_FOR_TESTING_ONLY"


def make_cipher() -> SessionCipher:
    """Return a cipher with a freshly generated valid key."""
    return SessionCipher(Fernet.generate_key())


def test_encrypt_decrypt_roundtrip():
    cipher = make_cipher()
    ciphertext = cipher.encrypt(FAKE_SESSION)
    assert cipher.decrypt(ciphertext) == FAKE_SESSION


def test_ciphertext_is_not_plaintext():
    cipher = make_cipher()
    ciphertext = cipher.encrypt(FAKE_SESSION)
    # Ciphertext must never contain the raw session string
    assert FAKE_SESSION not in ciphertext


def test_different_ciphertext_each_time():
    """Fernet is non-deterministic (includes timestamp + random IV)."""
    cipher = make_cipher()
    ct1 = cipher.encrypt(FAKE_SESSION)
    ct2 = cipher.encrypt(FAKE_SESSION)
    assert ct1 != ct2
    # But both decrypt to the same value
    assert cipher.decrypt(ct1) == cipher.decrypt(ct2) == FAKE_SESSION


def test_wrong_key_raises():
    key1 = Fernet.generate_key()
    key2 = Fernet.generate_key()
    cipher1 = SessionCipher(key1)
    cipher2 = SessionCipher(key2)
    ciphertext = cipher1.encrypt(FAKE_SESSION)
    with pytest.raises(SessionEncryptionError):
        cipher2.decrypt(ciphertext)


def test_invalid_key_raises():
    with pytest.raises(SessionEncryptionError):
        SessionCipher("not-a-valid-fernet-key")


def test_tampered_ciphertext_raises():
    cipher = make_cipher()
    ciphertext = cipher.encrypt(FAKE_SESSION)
    # Tamper the middle of the ciphertext
    tampered = ciphertext[:10] + "XXXX" + ciphertext[14:]
    with pytest.raises(SessionEncryptionError):
        cipher.decrypt(tampered)


def test_generate_key_produces_valid_fernet_key():
    key = generate_key()
    # Should not raise
    cipher = SessionCipher(key)
    ct = cipher.encrypt(FAKE_SESSION)
    assert cipher.decrypt(ct) == FAKE_SESSION


def test_from_settings(monkeypatch):
    """SessionCipher.from_settings() uses SESSION_ENCRYPTION_KEY from env."""
    from app.core.config import get_settings

    valid_key = Fernet.generate_key().decode()
    monkeypatch.setenv("SESSION_ENCRYPTION_KEY", valid_key)
    monkeypatch.setenv("TELEGRAM_API_ID", "12345")
    monkeypatch.setenv("TELEGRAM_API_HASH", "testhash")
    monkeypatch.setenv("BOT_TOKEN", "123456:test")
    monkeypatch.setenv("APP_SECRET_KEY", "test-secret")
    get_settings.cache_clear()

    cipher = SessionCipher.from_settings()
    ct = cipher.encrypt(FAKE_SESSION)
    assert cipher.decrypt(ct) == FAKE_SESSION

    get_settings.cache_clear()


def test_from_settings_missing_key_raises(monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setenv("SESSION_ENCRYPTION_KEY", "")
    monkeypatch.setenv("TELEGRAM_API_ID", "12345")
    monkeypatch.setenv("TELEGRAM_API_HASH", "testhash")
    monkeypatch.setenv("BOT_TOKEN", "123456:test")
    monkeypatch.setenv("APP_SECRET_KEY", "test-secret")
    get_settings.cache_clear()

    with pytest.raises(SessionEncryptionError, match="SESSION_ENCRYPTION_KEY is not configured"):
        SessionCipher.from_settings()

    get_settings.cache_clear()
