"""
app.services.subscription
~~~~~~~~~~~~~~~~~~~~~~~~~
Business logic for managing user subscriptions.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Subscription, SubscriptionPlan, SubscriptionStatus, User
from app.db.repositories import SubscriptionRepository


class SubscriptionError(Exception):
    """Base exception for subscription-related errors."""
    pass


class SubscriptionService:
    """Service layer for subscription operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = SubscriptionRepository(session)

    def _calculate_expiration(
        self, plan: SubscriptionPlan, start_date: datetime
    ) -> datetime | None:
        """Calculate the expiration date based on the plan type."""
        if plan == SubscriptionPlan.WEEKLY:
            return start_date + timedelta(days=7)
        if plan == SubscriptionPlan.MONTHLY:
            return start_date + timedelta(days=30)
        if plan == SubscriptionPlan.LIFETIME:
            return None
        raise ValueError(f"Unknown subscription plan: {plan}")

    async def get_subscription(self, user_id: int) -> Subscription | None:
        """Fetch a user's subscription record."""
        return await self._repo.get_by_user_id(user_id)

    async def check_active(self, user_id: int) -> bool:
        """Return True if the user has a currently active subscription.
        
        This relies on the database-authoritative SubscriptionRepository.is_active.
        """
        return await self._repo.is_active(user_id)

    async def grant_subscription(
        self,
        user_id: int,
        plan: SubscriptionPlan,
        starts_at: datetime | None = None,
    ) -> Subscription:
        """Grant a new subscription to a user (admin operation).
        
        If the user already has a subscription, it will be renewed/overwritten
        starting from the specified `starts_at` date.
        """
        now = datetime.now(timezone.utc)
        start_date = starts_at or now
        expires_at = self._calculate_expiration(plan, start_date)

        existing_sub = await self._repo.get_by_user_id(user_id)
        if existing_sub is not None:
            # Overwrite existing subscription
            return await self._repo.renew(
                existing_sub,
                new_expires_at=expires_at,
                plan=plan,
            )

        # Create new subscription
        return await self._repo.create(
            user_id=user_id,
            plan=plan,
            starts_at=start_date,
            expires_at=expires_at,
            status=SubscriptionStatus.ACTIVE,
        )

    async def renew_subscription(
        self,
        user_id: int,
        plan: SubscriptionPlan | None = None,
    ) -> Subscription:
        """Renew an existing subscription.
        
        If the subscription is still active, time is appended to the current expiration.
        If it's expired or cancelled, it restarts from now.
        """
        sub = await self._repo.get_by_user_id(user_id)
        if sub is None:
            raise SubscriptionError("Cannot renew: user has no subscription record. Use grant_subscription first.")

        now = datetime.now(timezone.utc)
        current_plan = plan or sub.plan

        if current_plan == SubscriptionPlan.LIFETIME:
            return await self._repo.renew(
                sub,
                new_expires_at=None,
                plan=current_plan,
            )

        expires_at = sub.expires_at
        if expires_at is not None and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
            
        if sub.is_active and expires_at and expires_at > now:
            # Append time to existing expiration
            # SQLite stores dates naively, so make sure it's aware
            new_expires = self._calculate_expiration(current_plan, expires_at)
        else:
            # Restart from now
            new_expires = self._calculate_expiration(current_plan, now)

        return await self._repo.renew(
            sub,
            new_expires_at=new_expires,
            plan=current_plan,
        )

    async def revoke_subscription(self, user_id: int) -> Subscription:
        """Revoke/cancel an active subscription immediately."""
        sub = await self._repo.get_by_user_id(user_id)
        if sub is None:
            raise SubscriptionError("User has no subscription to revoke.")
        
        return await self._repo.cancel(sub)
