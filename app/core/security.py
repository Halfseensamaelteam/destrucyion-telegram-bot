"""
app.core.security
~~~~~~~~~~~~~~~~~
Session encryption / decryption helpers.

Telethon StringSession strings are treated as credentials equivalent to
account passwords. They MUST be encrypted before being stored in PostgreSQL
and decrypted only inside the worker process, never exposed through any API.

Encryption scheme: Fernet symmetric encryption (AES-128-CBC + HMAC-SHA256).
Key: 32-byte URL-safe base64 value from SESSION_ENCRYPTION_KEY env var.

Usage::

    from app.core.security import encrypt_session, decrypt_session

    ciphertext = encrypt_session(session_string, key)   # store in DB
    plaintext  = decrypt_session(ciphertext, key)        # use in worker
"""

import base64

from cryptography.fernet import Fernet, InvalidToken

from app.core.exceptions import ConfigurationError, TelegramSessionError


def _get_fernet(key: str) -> Fernet:
    """Return a Fernet instance from a base64 key string.

    Args:
        key: URL-safe base64-encoded 32-byte key.

    Raises:
        ConfigurationError: If the key is empty or malformed.
    """
    if not key:
        raise ConfigurationError(
            "SESSION_ENCRYPTION_KEY is not set. "
            "Generate one with: "
            "python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    try:
        # Fernet accepts bytes; encode the string key.
        return Fernet(key.encode() if isinstance(key, str) else key)
    except (ValueError, base64.binascii.Error) as exc:
        raise ConfigurationError(
            f"SESSION_ENCRYPTION_KEY is invalid: {exc}"
        ) from exc


def encrypt_session(session_string: str, encryption_key: str) -> str:
    """Encrypt a Telethon StringSession for storage in the database.

    Args:
        session_string: Raw Telethon StringSession string.
        encryption_key: Fernet key (from settings.session_encryption_key).

    Returns:
        URL-safe base64 ciphertext string suitable for storing in a TEXT column.

    Raises:
        ConfigurationError: If the encryption key is missing or invalid.
    """
    if not session_string:
        raise ValueError("session_string must not be empty")

    fernet = _get_fernet(encryption_key)
    ciphertext_bytes = fernet.encrypt(session_string.encode("utf-8"))
    return ciphertext_bytes.decode("utf-8")


def decrypt_session(ciphertext: str, encryption_key: str) -> str:
    """Decrypt a stored session ciphertext back to a Telethon StringSession.

    Args:
        ciphertext: The encrypted session string stored in the database.
        encryption_key: Fernet key (from settings.session_encryption_key).

    Returns:
        The decrypted Telethon StringSession string.

    Raises:
        TelegramSessionError: If decryption fails (wrong key, tampered data).
        ConfigurationError: If the encryption key is missing or invalid.
    """
    if not ciphertext:
        raise ValueError("ciphertext must not be empty")

    fernet = _get_fernet(encryption_key)
    try:
        plaintext_bytes = fernet.decrypt(ciphertext.encode("utf-8"))
        return plaintext_bytes.decode("utf-8")
    except InvalidToken as exc:
        raise TelegramSessionError(
            "Failed to decrypt Telegram session: token is invalid or key is wrong. "
            "The session record may be corrupted or encrypted with a different key."
        ) from exc
