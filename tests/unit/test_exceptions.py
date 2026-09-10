"""
tests/unit/test_exceptions.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Unit tests for app.core.exceptions hierarchy.
"""

import pytest

from app.core.exceptions import (
    AppError,
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    ConflictError,
    DuplicateMediaError,
    MediaCaptureError,
    MediaDeliveryError,
    MediaError,
    NotFoundError,
    SubscriptionError,
    SubscriptionExpiredError,
    SubscriptionNotFoundError,
    TelegramAccountError,
    TelegramAccountNotFoundError,
    TelegramAuthError,
    TelegramSessionError,
)


class TestExceptionHierarchy:
    def test_app_error_is_exception(self):
        assert issubclass(AppError, Exception)

    def test_configuration_error_is_app_error(self):
        assert issubclass(ConfigurationError, AppError)

    def test_subscription_expired_is_subscription_error(self):
        assert issubclass(SubscriptionExpiredError, SubscriptionError)
        assert issubclass(SubscriptionError, AppError)

    def test_telegram_session_error_is_account_error(self):
        assert issubclass(TelegramSessionError, TelegramAccountError)
        assert issubclass(TelegramAccountError, AppError)

    def test_duplicate_media_is_media_error(self):
        assert issubclass(DuplicateMediaError, MediaError)
        assert issubclass(MediaError, AppError)


class TestExceptionAttributes:
    def test_app_error_stores_message(self):
        err = AppError("something went wrong")
        assert err.message == "something went wrong"
        assert str(err) == "something went wrong"

    def test_app_error_default_code_is_class_name(self):
        err = ConfigurationError("bad config")
        assert err.code == "ConfigurationError"

    def test_app_error_custom_code(self):
        err = AppError("bad thing", code="CUSTOM_CODE")
        assert err.code == "CUSTOM_CODE"

    def test_can_catch_subclass_as_app_error(self):
        with pytest.raises(AppError):
            raise SubscriptionExpiredError("subscription is expired")

    def test_can_catch_specific_subclass(self):
        with pytest.raises(SubscriptionExpiredError):
            raise SubscriptionExpiredError("expired")
