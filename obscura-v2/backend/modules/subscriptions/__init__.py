"""
Subscriptions Module

Handles subscription management, billing, and Zcash payments.
Can run as standalone microservice or part of monolith.

Components:
- service: Subscription management API
- payments/: Zcash payment processing
- billing: Billing cycles and invoicing
"""

from .service import app as subscription_service, subscription_manager
from .manager import SubscriptionManager, BillingCycle, SubscriptionPlanDTO
from .payments.zcash_client import ZcashClient, zcash

__all__ = [
    "subscription_service",
    "subscription_manager",
    "SubscriptionManager",
    "BillingCycle",
    "SubscriptionPlanDTO",
    "ZcashClient",
    "zcash",
]
