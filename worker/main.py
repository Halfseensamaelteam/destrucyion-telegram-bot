"""
worker.main
~~~~~~~~~~~
Persistent worker entry point.

The worker is responsible for running long-lived Telethon clients.
It MUST NOT run on Vercel or any serverless platform — it requires a
persistent process (VPS, Docker host, Railway, Render, Fly.io, etc.).

In Phase 1, the worker starts and logs a startup message only.
The TelegramClientManager and account loading are implemented in Phase 6.

Run locally:
    python -m worker.main
"""

import asyncio

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger

settings = get_settings()
configure_logging(settings.log_level)
log = get_logger(__name__)


async def run() -> None:
    """Main worker coroutine.

    Phase 1: skeleton only — logs startup and exits.
    Phase 6+: loads accounts, starts Telethon clients, processes media.
    """
    log.info(
        "worker_starting",
        env=settings.app_env,
        phase="1-skeleton",
    )
    # TODO (Phase 6): initialise TelegramClientManager
    # TODO (Phase 6): load active telegram_accounts from DB
    # TODO (Phase 6): start isolated Telethon clients
    # TODO (Phase 6): await supervisor loop
    log.info("worker_started", status="skeleton — no accounts loaded yet")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
