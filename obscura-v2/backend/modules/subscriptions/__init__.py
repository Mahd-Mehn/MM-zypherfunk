"""
Subscriptions Module

Handles subscription management, billing, and Zcash payments.
Can run as standalone microservice or part of monolith.

Components:
- service: Subscription management API
- payments/: Zcash payment processing
- billing: Billing cycles and invoicing
"""

from .service import SubscriptionService, subscription_service
from .payments.zcash_client import ZcashClient, zcash

__all__ = [
    "SubscriptionService",
    "subscription_service",
    "ZcashClient",
    "zcash",
]
