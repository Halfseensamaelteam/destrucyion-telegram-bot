"""
app.core.exceptions
~~~~~~~~~~~~~~~~~~~
Application-wide exception hierarchy.

All custom exceptions inherit from ``AppError`` so callers can catch them
with a single ``except AppError`` if needed.
"""


class AppError(Exception):
    """Base class for all application-defined errors."""

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__

    def __repr__(self) -> str:  # pragma: no cover
        return f"{self.__class__.__name__}(message={self.message!r}, code={self.code!r})"


# ------------------------------------------------------------------
# Configuration / startup
# ------------------------------------------------------------------


class ConfigurationError(AppError):
    """Raised when a required configuration value is missing or invalid."""


# ------------------------------------------------------------------
# Authentication / authorization
# ------------------------------------------------------------------


class AuthenticationError(AppError):
    """Raised when a user cannot be authenticated."""


class AuthorizationError(AppError):
    """Raised when an authenticated user lacks permission for an operation."""


# ------------------------------------------------------------------
# Subscription
# ------------------------------------------------------------------


class SubscriptionError(AppError):
    """Base class for subscription-related errors."""


class SubscriptionExpiredError(SubscriptionError):
    """Raised when a user attempts an action that requires an active subscription."""


class SubscriptionNotFoundError(SubscriptionError):
    """Raised when no subscription record exists for the user."""


# ------------------------------------------------------------------
# Telegram account
# ------------------------------------------------------------------


class TelegramAccountError(AppError):
    """Base class for Telegram account errors."""


class TelegramAccountNotFoundError(TelegramAccountError):
    """Raised when a requested Telegram account does not exist."""


class TelegramAuthError(TelegramAccountError):
    """Raised when Telegram authentication fails."""


class TelegramSessionError(TelegramAccountError):
    """Raised when a Telegram session cannot be loaded, decrypted, or used."""


# ------------------------------------------------------------------
# Media
# ------------------------------------------------------------------


class MediaError(AppError):
    """Base class for media processing errors."""


class MediaCaptureError(MediaError):
    """Raised when media cannot be downloaded from Telegram."""


class MediaDeliveryError(MediaError):
    """Raised when media cannot be forwarded to Saved Messages."""


class DuplicateMediaError(MediaError):
    """Raised when attempting to save media that has already been processed (idempotency)."""


# ------------------------------------------------------------------
# Data / persistence
# ------------------------------------------------------------------


class NotFoundError(AppError):
    """Raised when a requested database record does not exist."""


class ConflictError(AppError):
    """Raised when a uniqueness constraint is violated."""
