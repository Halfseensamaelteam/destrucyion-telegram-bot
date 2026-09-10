import pytest
from datetime import datetime, timezone, timedelta

from app.db.models import Subscription, SubscriptionPlan, SubscriptionStatus

def test_subscription_is_active_property():
    now = datetime.now(timezone.utc)
    
    # 1. Normal active subscription
    sub_active = Subscription(
        plan=SubscriptionPlan.WEEKLY,
        starts_at=now - timedelta(days=1),
        expires_at=now + timedelta(days=6),
        status=SubscriptionStatus.ACTIVE
    )
    assert sub_active.is_active is True

    # 2. Expired by date
    sub_expired_date = Subscription(
        plan=SubscriptionPlan.WEEKLY,
        starts_at=now - timedelta(days=10),
        expires_at=now - timedelta(days=3),
        status=SubscriptionStatus.ACTIVE
    )
    assert sub_expired_date.is_active is False

    # 3. Cancelled status overrides valid date
    sub_cancelled = Subscription(
        plan=SubscriptionPlan.WEEKLY,
        starts_at=now - timedelta(days=1),
        expires_at=now + timedelta(days=6),
        status=SubscriptionStatus.CANCELLED
    )
    assert sub_cancelled.is_active is False

    # 4. Future subscription (not started yet)
    sub_future = Subscription(
        plan=SubscriptionPlan.WEEKLY,
        starts_at=now + timedelta(days=1),
        expires_at=now + timedelta(days=8),
        status=SubscriptionStatus.ACTIVE
    )
    assert sub_future.is_active is False

    # 5. Lifetime subscription (no expiration)
    sub_lifetime = Subscription(
        plan=SubscriptionPlan.LIFETIME,
        starts_at=now - timedelta(days=1),
        expires_at=None,
        status=SubscriptionStatus.ACTIVE
    )
    assert sub_lifetime.is_active is True
