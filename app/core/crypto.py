"""
app.core.crypto
~~~~~~~~~~~~~~~
Fernet-based symmetric encryption for Telethon session strings.

Session strings are Telegram credentials. Rules (CLAUDE.md §13):
  - NEVER log them
  - NEVER return them from API endpoints
  - NEVER include them in exception messages
  - NEVER commit them to source control
  - Store ONLY the ciphertext (`session_ciphertext`) in the database

Usage:
    key = Fernet.generate_key().decode()        # store in SESSION_ENCRYPTION_KEY env var
    cipher = SessionCipher.from_env()
    ciphertext = cipher.encrypt("session_str")
    plaintext  = cipher.decrypt(ciphertext)
"""

from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken


class SessionEncryptionError(Exception):
    """Raised when session encryption or decryption fails."""


class SessionCipher:
    """Wraps Fernet to encrypt/decrypt Telethon session strings.

    The raw session string is NEVER stored as an instance attribute and
    NEVER appears in repr, str, or error messages from this class.
    """

    def __init__(self, key: str | bytes) -> None:
        """Initialise with a base64-urlsafe Fernet key.

        Args:
            key: A URL-safe base64-encoded 32-byte key (the output of
                 ``Fernet.generate_key()``).

        Raises:
            SessionEncryptionError: If the key is invalid.
        """
        try:
            if isinstance(key, str):
                key = key.encode()
            self._fernet = Fernet(key)
        except Exception:
            raise SessionEncryptionError(
                "Invalid SESSION_ENCRYPTION_KEY. "
                "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
            )

    @classmethod
    def from_settings(cls) -> "SessionCipher":
        """Create a SessionCipher from the application settings.

        Raises:
            SessionEncryptionError: If the key is missing or invalid.
        """
        from app.core.config import get_settings

        settings = get_settings()
        key = settings.session_encryption_key.get_secret_value()
        if not key:
            raise SessionEncryptionError(
                "SESSION_ENCRYPTION_KEY is not configured. "
                "Set it in your .env file."
            )
        return cls(key)

    def encrypt(self, session_string: str) -> str:
        """Encrypt a Telethon session string.

        Args:
            session_string: The plaintext Telethon StringSession value.

        Returns:
            A base64-urlsafe ciphertext string safe to store in the database.

        Note:
            Fernet generates a unique IV each call, so the same input produces
            different ciphertext every time. This is intentional.
        """
        ciphertext_bytes = self._fernet.encrypt(session_string.encode())
        return ciphertext_bytes.decode()

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt a stored session ciphertext.

        Args:
            ciphertext: The base64-urlsafe ciphertext from the database.

        Returns:
            The plaintext Telethon StringSession string.

        Raises:
            SessionEncryptionError: If decryption fails (wrong key, tampered data).

        Warning:
            The caller is responsible for NOT logging the returned value.
        """
        try:
            plaintext_bytes = self._fernet.decrypt(ciphertext.encode())
            return plaintext_bytes.decode()
        except InvalidToken:
            raise SessionEncryptionError(
                "Failed to decrypt session: token is invalid or the key has changed."
            )


def generate_key() -> str:
    """Generate a new random Fernet key suitable for SESSION_ENCRYPTION_KEY.

    Run this once and store the output in your .env file.
    Never regenerate for an existing database unless you re-encrypt all sessions.
    """
    return Fernet.generate_key().decode()
