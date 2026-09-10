"""
app.db.repositories.subscription_repo
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Repository for the `subscriptions` table.

Subscription is the database-authoritative source of truth (CLAUDE.md §11).
Never use in-memory timers or Redis as the source of truth.
"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.subscription import Subscription, SubscriptionPlan, SubscriptionStatus


class SubscriptionRepository:
    """Data access layer for Subscription records."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_user_id(self, user_id: int) -> Subscription | None:
        result = await self._session.execute(
            select(Subscription).where(Subscription.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def is_active(self, user_id: int) -> bool:
        """Return True if the user has a currently active subscription.

        Active criteria (CLAUDE.md §11):
            status == ACTIVE
            AND starts_at <= now
            AND expires_at > now   (or plan == LIFETIME)
        """
        sub = await self.get_by_user_id(user_id)
        if sub is None:
            return False
        return sub.is_active

    async def create(
        self,
        *,
        user_id: int,
        plan: SubscriptionPlan,
        starts_at: datetime,
        expires_at: datetime | None = None,
        status: SubscriptionStatus = SubscriptionStatus.ACTIVE,
    ) -> Subscription:
        sub = Subscription(
            user_id=user_id,
            plan=plan,
            starts_at=starts_at,
            expires_at=expires_at,
            status=status,
        )
        self._session.add(sub)
        await self._session.flush()
        await self._session.refresh(sub)
        return sub

    async def renew(
        self,
        subscription: Subscription,
        *,
        new_expires_at: datetime,
        plan: SubscriptionPlan | None = None,
    ) -> Subscription:
        """Extend or renew an existing subscription."""
        subscription.expires_at = new_expires_at
        subscription.status = SubscriptionStatus.ACTIVE
        if plan is not None:
            subscription.plan = plan
        subscription.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        await self._session.refresh(subscription)
        return subscription

    async def expire(self, subscription: Subscription) -> Subscription:
        """Mark a subscription as expired."""
        subscription.status = SubscriptionStatus.EXPIRED
        subscription.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        await self._session.refresh(subscription)
        return subscription

    async def cancel(self, subscription: Subscription) -> Subscription:
        """Mark a subscription as cancelled."""
        subscription.status = SubscriptionStatus.CANCELLED
        subscription.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        await self._session.refresh(subscription)
        return subscription
