"""
app.db.repositories.telegram_account_repo
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Repository for the `telegram_accounts` table.

Each account belongs to exactly one application user. Never mix accounts.
"""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.telegram_account import TelegramAccount, TelegramAccountStatus


class TelegramAccountRepository:
    """Data access layer for TelegramAccount records."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, account_id: int) -> TelegramAccount | None:
        result = await self._session.execute(
            select(TelegramAccount).where(TelegramAccount.id == account_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_and_user(
        self, account_id: int, user_id: int
    ) -> TelegramAccount | None:
        """Tenant-safe lookup — returns None if account does not belong to user_id."""
        result = await self._session.execute(
            select(TelegramAccount).where(
                TelegramAccount.id == account_id,
                TelegramAccount.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: int) -> list[TelegramAccount]:
        result = await self._session.execute(
            select(TelegramAccount).where(TelegramAccount.user_id == user_id)
        )
        return list(result.scalars().all())

    async def list_active(self) -> list[TelegramAccount]:
        """Return all accounts with ACTIVE status across all users."""
        result = await self._session.execute(
            select(TelegramAccount).where(
                TelegramAccount.status == TelegramAccountStatus.ACTIVE
            )
        )
        return list(result.scalars().all())

    async def create(
        self,
        *,
        user_id: int,
        status: TelegramAccountStatus = TelegramAccountStatus.DISCONNECTED,
        telegram_user_id: int | None = None,
        username: str | None = None,
        phone_masked: str | None = None,
        session_ciphertext: str | None = None,
    ) -> TelegramAccount:
        account = TelegramAccount(
            user_id=user_id,
            telegram_user_id=telegram_user_id,
            username=username,
            phone_masked=phone_masked,
            session_ciphertext=session_ciphertext,
            status=status,
        )
        self._session.add(account)
        await self._session.flush()
        await self._session.refresh(account)
        return account

    async def update_status(
        self,
        account: TelegramAccount,
        status: TelegramAccountStatus,
        *,
        last_error: str | None = None,
        last_connected_at: datetime | None = None,
    ) -> TelegramAccount:
        account.status = status
        if last_error is not None:
            account.last_error = last_error
        if last_connected_at is not None:
            account.last_connected_at = last_connected_at
        await self._session.flush()
        await self._session.refresh(account)
        return account

    async def update(self, account: TelegramAccount, **kwargs: object) -> TelegramAccount:
        for key, value in kwargs.items():
            setattr(account, key, value)
        await self._session.flush()
        await self._session.refresh(account)
        return account
