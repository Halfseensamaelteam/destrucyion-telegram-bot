"""
worker.supervisor
~~~~~~~~~~~~~~~~~
TelegramClientManager — account supervision skeleton.

In Phase 1 this is a placeholder only.
Full implementation in Phase 6: load accounts, create isolated Telethon
clients, handle reconnections, and enforce subscription state.

Design rules (from CLAUDE.md):
- One TelegramClient per Telegram account — NEVER share clients.
- Account B failure must NOT affect Account A, C, D.
- Sessions are decrypted in this process only — never logged or returned.
"""


class TelegramClientManager:
    """Manages a pool of isolated Telethon clients, one per Telegram account.

    Phase 1: empty skeleton.
    Phase 6: full implementation.
    """

    def __init__(self) -> None:
        # TODO (Phase 6): initialise account registry and connection state
        pass

    async def start(self) -> None:
        """Load all active accounts and start their Telethon clients.

        TODO (Phase 6): query telegram_accounts from DB, decrypt sessions,
        create TelegramClient instances, register event handlers.
        """
        raise NotImplementedError("TelegramClientManager.start() — implement in Phase 6")

    async def stop(self) -> None:
        """Gracefully disconnect all active Telethon clients.

        TODO (Phase 6): disconnect all clients cleanly.
        """
        raise NotImplementedError("TelegramClientManager.stop() — implement in Phase 6")
