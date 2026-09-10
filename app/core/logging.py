"""
app.core.logging
~~~~~~~~~~~~~~~~
Structured logging setup using structlog.

Call ``configure_logging()`` once at application startup (in app/main.py and
worker/main.py) before any log calls are made.

Fields never to include in log events:
  - session strings
  - auth codes / 2FA passwords
  - encryption keys
  - raw media content
  - any credential or secret

Usage::

    from app.core.logging import get_logger

    log = get_logger(__name__)
    log.info("media_saved", user_id=1, telegram_account_id=2, source_message_id=99)
"""

import logging
import sys

import structlog


def configure_logging(log_level: str = "INFO") -> None:
    """Configure structlog for the application.

    Args:
        log_level: One of DEBUG, INFO, WARNING, ERROR, CRITICAL.
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    # Configure stdlib logging — structlog will render through it.
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )

    # Silence noisy third-party loggers.
    logging.getLogger("telethon").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            # JSON in production; pretty console in development.
            structlog.dev.ConsoleRenderer()
            if _is_dev_environment()
            else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a bound structlog logger for the given module name.

    Args:
        name: Typically ``__name__``.

    Returns:
        A structlog BoundLogger instance.
    """
    return structlog.get_logger(name)


def _is_dev_environment() -> bool:
    """Detect development environment for renderer selection."""
    import os

    return os.getenv("APP_ENV", "development").lower() == "development"
