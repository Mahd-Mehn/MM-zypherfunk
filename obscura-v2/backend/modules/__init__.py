"""
Obscura V2 Modules

Modular monolith architecture with standalone deployment capability.

Modules:
- api_gateway: Unified entry point, routes to all services
- trading: Multi-exchange trade execution (100+ exchanges)
- subscriptions: Billing and Zcash payments
- copy_trading: Real-time trade copying
- analytics: Performance metrics and leaderboards
- citadel: Secure key storage via Nillion
"""

__all__ = [
    "api_gateway",
    "trading",
    "subscriptions",
    "copy_trading",
    "analytics",
    "citadel",
]
