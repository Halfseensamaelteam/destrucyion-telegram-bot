"""
tests/unit/test_security.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Unit tests for app.core.security — session encrypt/decrypt.

Tests:
- Roundtrip: encrypt then decrypt returns original string.
- Empty key raises ConfigurationError.
- Invalid key raises ConfigurationError.
- Wrong key raises TelegramSessionError.
- Empty session string raises ValueError.
- Empty ciphertext raises ValueError.
- Tampered ciphertext raises TelegramSessionError.
"""

import pytest
from cryptography.fernet import Fernet

from app.core.exceptions import ConfigurationError, TelegramSessionError
from app.core.security import decrypt_session, encrypt_session


@pytest.fixture
def valid_key() -> str:
    return Fernet.generate_key().decode()


@pytest.fixture
def another_key() -> str:
    return Fernet.generate_key().decode()


class TestEncryptDecryptRoundtrip:
    def test_roundtrip_basic(self, valid_key):
        session = "1BVtsOKIBU..."  # simulated session string
        ciphertext = encrypt_session(session, valid_key)
        recovered = decrypt_session(ciphertext, valid_key)
        assert recovered == session

    def test_ciphertext_differs_from_plaintext(self, valid_key):
        session = "some_session_string"
        ciphertext = encrypt_session(session, valid_key)
        assert ciphertext != session

    def test_repeated_encryption_produces_different_ciphertext(self, valid_key):
        """Fernet uses random IV — same plaintext yields different ciphertext."""
        session = "same_session_string"
        ct1 = encrypt_session(session, valid_key)
        ct2 = encrypt_session(session, valid_key)
        assert ct1 != ct2  # different IVs

    def test_both_still_decrypt_to_same_value(self, valid_key):
        session = "same_session_string"
        ct1 = encrypt_session(session, valid_key)
        ct2 = encrypt_session(session, valid_key)
        assert decrypt_session(ct1, valid_key) == session
        assert decrypt_session(ct2, valid_key) == session


class TestEncryptErrors:
    def test_empty_key_raises_configuration_error(self):
        with pytest.raises(ConfigurationError):
            encrypt_session("session", "")

    def test_invalid_key_raises_configuration_error(self):
        with pytest.raises(ConfigurationError):
            encrypt_session("session", "not-a-valid-fernet-key")

    def test_empty_session_raises_value_error(self, valid_key):
        with pytest.raises(ValueError):
            encrypt_session("", valid_key)


class TestDecryptErrors:
    def test_wrong_key_raises_session_error(self, valid_key, another_key):
        ciphertext = encrypt_session("real_session", valid_key)
        with pytest.raises(TelegramSessionError):
            decrypt_session(ciphertext, another_key)

    def test_empty_key_raises_configuration_error(self, valid_key):
        ciphertext = encrypt_session("real_session", valid_key)
        with pytest.raises(ConfigurationError):
            decrypt_session(ciphertext, "")

    def test_empty_ciphertext_raises_value_error(self, valid_key):
        with pytest.raises(ValueError):
            decrypt_session("", valid_key)

    def test_tampered_ciphertext_raises_session_error(self, valid_key):
        ciphertext = encrypt_session("real_session", valid_key)
        # Corrupt the ciphertext
        tampered = ciphertext[:-4] + "XXXX"
        with pytest.raises(TelegramSessionError):
            decrypt_session(tampered, valid_key)
