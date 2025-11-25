"""
Shared Database Module

Provides database connection, session management, and models
for all services in the modular monolith.
"""

from .connection import (
    Base,
    get_async_session,
    get_session,
    get_db,
    init_db,
    init_db_sync,
    get_async_engine,
    get_engine,
)

from .models import (
    # Enums
    SubscriptionTier,
    PaymentStatus,
    OrderSide,
    OrderType,
    OrderStatus,
    ExchangeType,
    UserRole,
    # Models
    User,
    UserSubscription,
    PaymentTransaction,
    TraderProfile,
    APIKeyStore,
    Follower,
    CopyTradingConfig,
    Trade,
    Position,
    AnalyticsSnapshot,
    MonitoringSession,
)

__all__ = [
    # Connection
    "Base",
    "get_async_session",
    "get_session",
    "get_db",
    "init_db",
    "init_db_sync",
    "get_async_engine",
    "get_engine",
    # Enums
    "SubscriptionTier",
    "PaymentStatus",
    "OrderSide",
    "OrderType",
    "OrderStatus",
    "ExchangeType",
    "UserRole",
    # Models
    "User",
    "UserSubscription",
    "PaymentTransaction",
    "TraderProfile",
    "APIKeyStore",
    "Follower",
    "CopyTradingConfig",
    "Trade",
    "Position",
    "AnalyticsSnapshot",
    "MonitoringSession",
]
