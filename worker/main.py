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
        phase="7-media-capture",
    )
    
    from app.db.database import AsyncSessionLocal
    from app.telegram.events import make_handler_factory
    from worker.supervisor import TelegramClientManager
    
    handler_factory = make_handler_factory(AsyncSessionLocal)
    manager = TelegramClientManager(AsyncSessionLocal, handler_factory=handler_factory)
    
    # Catch SIGINT and SIGTERM to gracefully stop the manager
    import signal
    loop = asyncio.get_running_loop()
    
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, lambda: asyncio.create_task(manager.stop()))
        except NotImplementedError:
            pass # Windows doesn't fully support add_signal_handler
            
    await manager.start()
    log.info("worker_started", status="manager running")
    
    try:
        await manager.run_forever()
    except asyncio.CancelledError:
        pass
    finally:
        await manager.stop()
        log.info("worker_stopped")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
