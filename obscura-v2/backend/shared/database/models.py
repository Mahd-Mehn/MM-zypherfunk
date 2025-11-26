"""
SQLAlchemy models for Obscura V2
Complete data models for the copy trading platform
"""

import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum
from typing import Optional, List

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text,
    ForeignKey, Enum, JSON, Numeric, Index, UniqueConstraint,
    CheckConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from .connection import Base


# ============================================================================
# ENUMS
# ============================================================================

class SubscriptionTier(str, PyEnum):
    """Subscription tier levels"""
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class PaymentStatus(str, PyEnum):
    """Payment transaction status"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    REFUNDED = "refunded"
    EXPIRED = "expired"


class OrderSide(str, PyEnum):
    """Trade order side"""
    BUY = "buy"
    SELL = "sell"


class OrderType(str, PyEnum):
    """Trade order type"""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"


class OrderStatus(str, PyEnum):
    """Trade order status"""
    PENDING = "pending"
    OPEN = "open"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    FAILED = "failed"


class ExchangeType(str, PyEnum):
    """Exchange type"""
    CEX = "cex"
    DEX = "dex"


class UserRole(str, PyEnum):
    """User roles"""
    USER = "user"
    TRADER = "trader"
    ADMIN = "admin"


# ============================================================================
# USER MODELS
# ============================================================================

class User(Base):
    """User account model"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=True, index=True)
    wallet_address = Column(String(255), unique=True, nullable=True, index=True)
    username = Column(String(100), unique=True, nullable=True, index=True)
    
    # Auth
    hashed_password = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    role = Column(Enum(UserRole), default=UserRole.USER)
    
    # Profile
    display_name = Column(String(100), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    subscription = relationship("UserSubscription", back_populates="user", uselist=False)
    trader_profile = relationship("TraderProfile", back_populates="user", uselist=False)
    api_keys = relationship("APIKeyStore", back_populates="user")
    trades = relationship("Trade", back_populates="user")
    positions = relationship("Position", back_populates="user")
    following = relationship("Follower", foreign_keys="Follower.follower_id", back_populates="follower")
    followers = relationship("Follower", foreign_keys="Follower.trader_id", back_populates="trader")
    
    __table_args__ = (
        CheckConstraint(
            "email IS NOT NULL OR wallet_address IS NOT NULL",
            name="user_must_have_email_or_wallet"
        ),
    )


# ============================================================================
# SUBSCRIPTION MODELS
# ============================================================================

class UserSubscription(Base):
    """User subscription model"""
    __tablename__ = "user_subscriptions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    
    # Subscription details
    tier = Column(Enum(SubscriptionTier), default=SubscriptionTier.FREE, nullable=False)
    is_active = Column(Boolean, default=True)
    auto_renew = Column(Boolean, default=True)
    
    # Billing
    monthly_price_usd = Column(Numeric(10, 2), default=0)
    zcash_payment_address = Column(String(255), nullable=True)  # Unified Address
    
    # Dates
    started_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="subscription")
    payments = relationship("PaymentTransaction", back_populates="subscription")
    
    __table_args__ = (
        Index("idx_subscription_tier", "tier"),
        Index("idx_subscription_expires", "expires_at"),
    )


class PaymentTransaction(Base):
    """Payment transaction record"""
    __tablename__ = "payment_transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("user_subscriptions.id"), nullable=False)
    
    # Payment details
    amount_usd = Column(Numeric(10, 2), nullable=False)
    amount_zec = Column(Numeric(18, 8), nullable=True)
    exchange_rate = Column(Numeric(18, 8), nullable=True)  # ZEC/USD at time of payment
    
    # Zcash transaction
    tx_hash = Column(String(255), nullable=True, unique=True)
    from_address = Column(String(255), nullable=True)
    to_address = Column(String(255), nullable=True)
    memo = Column(Text, nullable=True)  # Encrypted memo
    
    # Status
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    confirmations = Column(Integer, default=0)
    
    # Period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    confirmed_at = Column(DateTime, nullable=True)
    
    # Relationships
    subscription = relationship("UserSubscription", back_populates="payments")
    
    __table_args__ = (
        Index("idx_payment_status", "status"),
        Index("idx_payment_tx_hash", "tx_hash"),
    )


# ============================================================================
# TRADER MODELS
# ============================================================================

class TraderProfile(Base):
    """Extended profile for traders with copy trading enabled"""
    __tablename__ = "trader_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    
    # Trading settings
    is_public = Column(Boolean, default=False)  # Visible in leaderboard
    allows_copy_trading = Column(Boolean, default=False)
    max_followers = Column(Integer, default=100)
    
    # Subscription fees (for copy traders)
    monthly_fee_usd = Column(Numeric(10, 2), default=0)
    performance_fee_percent = Column(Numeric(5, 2), default=0)  # % of profits
    zcash_payout_address = Column(String(255), nullable=True)
    
    # Stats (cached, updated periodically)
    total_trades = Column(Integer, default=0)
    win_rate = Column(Numeric(5, 2), default=0)
    total_pnl_usd = Column(Numeric(18, 2), default=0)
    sharpe_ratio = Column(Numeric(8, 4), nullable=True)
    max_drawdown = Column(Numeric(5, 2), nullable=True)
    avg_trade_duration_hours = Column(Numeric(10, 2), nullable=True)
    
    # Rankings
    rank_overall = Column(Integer, nullable=True)
    rank_monthly = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    stats_updated_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="trader_profile")
    copy_configs = relationship("CopyTradingConfig", back_populates="trader")
    
    __table_args__ = (
        Index("idx_trader_public", "is_public"),
        Index("idx_trader_rank", "rank_overall"),
    )


class APIKeyStore(Base):
    """Encrypted API key storage (keys stored in Nillion)"""
    __tablename__ = "api_key_stores"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Exchange info
    exchange = Column(String(50), nullable=False)
    exchange_type = Column(Enum(ExchangeType), nullable=False)
    label = Column(String(100), nullable=True)  # User-friendly name
    
    # Nillion storage reference (actual keys stored in Nillion)
    nillion_key_store_id = Column(String(255), nullable=False)
    nillion_secret_store_id = Column(String(255), nullable=True)
    nillion_extra_store_ids = Column(JSON, default={})
    
    key_version = Column(Integer, default=1)
    
    # Permissions
    can_trade = Column(Boolean, default=True)
    can_withdraw = Column(Boolean, default=False)
    permissions = Column(JSON, default={})  # Map of user_id -> permission_level
    
    # Status
    is_active = Column(Boolean, default=True)
    is_valid = Column(Boolean, default=True)  # Last validation result
    last_validated_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")
    
    __table_args__ = (
        UniqueConstraint("user_id", "exchange", "label", name="uq_user_exchange_label"),
        Index("idx_apikey_exchange", "exchange"),
        Index("idx_apikey_user", "user_id"),
    )


# ============================================================================
# COPY TRADING MODELS
# ============================================================================

class Follower(Base):
    """Copy trading follower relationship"""
    __tablename__ = "followers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trader_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    follower_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_copying = Column(Boolean, default=False)  # Actually copying trades
    
    # Timestamps
    followed_at = Column(DateTime, default=datetime.utcnow)
    copy_started_at = Column(DateTime, nullable=True)
    unfollowed_at = Column(DateTime, nullable=True)
    
    # Relationships
    trader = relationship("User", foreign_keys=[trader_id], back_populates="followers")
    follower = relationship("User", foreign_keys=[follower_id], back_populates="following")
    copy_config = relationship("CopyTradingConfig", back_populates="follower_rel", uselist=False)
    
    __table_args__ = (
        UniqueConstraint("trader_id", "follower_id", name="uq_trader_follower"),
        Index("idx_follower_trader", "trader_id"),
        Index("idx_follower_follower", "follower_id"),
    )


class CopyTradingConfig(Base):
    """Configuration for copy trading"""
    __tablename__ = "copy_trading_configs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    follower_rel_id = Column(UUID(as_uuid=True), ForeignKey("followers.id"), unique=True, nullable=False)
    trader_id = Column(UUID(as_uuid=True), ForeignKey("trader_profiles.id"), nullable=False)
    
    # Position sizing
    copy_mode = Column(String(20), default="proportional")  # proportional, fixed, mirror
    fixed_amount_usd = Column(Numeric(18, 2), nullable=True)
    proportion_percent = Column(Numeric(5, 2), default=100)  # % of trader's position
    max_position_usd = Column(Numeric(18, 2), nullable=True)
    
    # Risk management
    max_daily_loss_usd = Column(Numeric(18, 2), nullable=True)
    max_drawdown_percent = Column(Numeric(5, 2), nullable=True)
    stop_loss_percent = Column(Numeric(5, 2), nullable=True)
    
    # Filters
    allowed_exchanges = Column(JSON, default=list)  # Empty = all
    allowed_pairs = Column(JSON, default=list)  # Empty = all
    min_trade_size_usd = Column(Numeric(18, 2), default=10)
    max_trade_size_usd = Column(Numeric(18, 2), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_paused = Column(Boolean, default=False)
    pause_reason = Column(String(255), nullable=True)
    
    # Stats
    total_copied_trades = Column(Integer, default=0)
    total_pnl_usd = Column(Numeric(18, 2), default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    follower_rel = relationship("Follower", back_populates="copy_config")
    trader = relationship("TraderProfile", back_populates="copy_configs")
    
    __table_args__ = (
        Index("idx_copy_config_trader", "trader_id"),
    )


# ============================================================================
# TRADE MODELS
# ============================================================================

class Trade(Base):
    """Individual trade record"""
    __tablename__ = "trades"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Order details
    exchange = Column(String(50), nullable=False)
    exchange_type = Column(Enum(ExchangeType), nullable=False)
    exchange_order_id = Column(String(255), nullable=True)
    
    # Trade info
    symbol = Column(String(50), nullable=False)  # e.g., "BTC/USDT"
    side = Column(Enum(OrderSide), nullable=False)
    order_type = Column(Enum(OrderType), nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    
    # Amounts
    amount = Column(Numeric(28, 18), nullable=False)
    filled_amount = Column(Numeric(28, 18), default=0)
    price = Column(Numeric(28, 18), nullable=True)  # Limit price or null for market
    average_fill_price = Column(Numeric(28, 18), nullable=True)
    
    # Calculated values
    notional_value_usd = Column(Numeric(18, 2), nullable=True)
    fees_usd = Column(Numeric(18, 8), default=0)
    pnl_usd = Column(Numeric(18, 2), nullable=True)  # Realized PnL
    
    # Copy trading reference
    is_copy_trade = Column(Boolean, default=False)
    source_trade_id = Column(UUID(as_uuid=True), ForeignKey("trades.id"), nullable=True)
    
    # Blockchain (for DEX)
    tx_hash = Column(String(255), nullable=True)
    block_number = Column(Integer, nullable=True)
    gas_used = Column(Numeric(18, 0), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    executed_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="trades")
    copied_trades = relationship("Trade", backref="source_trade", remote_side=[id])
    
    __table_args__ = (
        Index("idx_trade_user", "user_id"),
        Index("idx_trade_symbol", "symbol"),
        Index("idx_trade_exchange", "exchange"),
        Index("idx_trade_status", "status"),
        Index("idx_trade_created", "created_at"),
    )


class Position(Base):
    """Open position tracking"""
    __tablename__ = "positions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Position info
    exchange = Column(String(50), nullable=False)
    symbol = Column(String(50), nullable=False)
    side = Column(Enum(OrderSide), nullable=False)  # Long or Short
    
    # Amounts
    size = Column(Numeric(28, 18), nullable=False)
    entry_price = Column(Numeric(28, 18), nullable=False)
    current_price = Column(Numeric(28, 18), nullable=True)
    liquidation_price = Column(Numeric(28, 18), nullable=True)
    
    # Leverage (for futures)
    leverage = Column(Numeric(5, 2), default=1)
    margin_used = Column(Numeric(18, 2), nullable=True)
    
    # PnL
    unrealized_pnl_usd = Column(Numeric(18, 2), default=0)
    realized_pnl_usd = Column(Numeric(18, 2), default=0)
    
    # Status
    is_open = Column(Boolean, default=True)
    
    # Timestamps
    opened_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="positions")
    
    __table_args__ = (
        UniqueConstraint("user_id", "exchange", "symbol", "is_open", name="uq_open_position"),
        Index("idx_position_user", "user_id"),
        Index("idx_position_open", "is_open"),
    )


# ============================================================================
# ANALYTICS MODELS
# ============================================================================

class AnalyticsSnapshot(Base):
    """Periodic analytics snapshot for users/traders"""
    __tablename__ = "analytics_snapshots"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Time period
    period_type = Column(String(20), nullable=False)  # hourly, daily, weekly, monthly
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # Portfolio value
    total_value_usd = Column(Numeric(18, 2), nullable=False)
    cash_balance_usd = Column(Numeric(18, 2), default=0)
    positions_value_usd = Column(Numeric(18, 2), default=0)
    
    # Performance
    pnl_usd = Column(Numeric(18, 2), default=0)
    pnl_percent = Column(Numeric(10, 4), default=0)
    
    # Trade stats
    trades_count = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    total_volume_usd = Column(Numeric(18, 2), default=0)
    
    # Risk metrics
    sharpe_ratio = Column(Numeric(8, 4), nullable=True)
    sortino_ratio = Column(Numeric(8, 4), nullable=True)
    max_drawdown_percent = Column(Numeric(5, 2), nullable=True)
    volatility = Column(Numeric(8, 4), nullable=True)
    
    # Extended metrics (stored as JSON for flexibility)
    metrics = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("user_id", "period_type", "period_start", name="uq_analytics_period"),
        Index("idx_analytics_user", "user_id"),
        Index("idx_analytics_period", "period_type", "period_start"),
    )


class MonitoringSession(Base):
    """Trade monitoring session tracking"""
    __tablename__ = "monitoring_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trader_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Session info
    exchange = Column(String(50), nullable=False)
    symbols = Column(JSON, default=list)  # Symbols being monitored
    
    # Status
    is_active = Column(Boolean, default=True)
    connection_status = Column(String(20), default="disconnected")
    
    # Stats
    events_received = Column(Integer, default=0)
    trades_detected = Column(Integer, default=0)
    last_event_at = Column(DateTime, nullable=True)
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index("idx_monitoring_trader", "trader_id"),
        Index("idx_monitoring_active", "is_active"),
    )


# ============================================================================
# EXCHANGE CONNECTION MODEL
# ============================================================================

class ExchangeConnection(Base):
    """User's exchange API connection"""
    __tablename__ = "exchange_connections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Exchange info
    exchange = Column(String(50), nullable=False)
    exchange_type = Column(Enum(ExchangeType), default=ExchangeType.CEX)
    label = Column(String(100), nullable=True)
    
    # Nillion reference (credentials stored in Nillion)
    nillion_store_id = Column(String(255), nullable=True)
    
    # Status
    status = Column(String(20), default="pending")  # pending, connected, error, disconnected
    is_active = Column(Boolean, default=True)
    is_signal_provider = Column(Boolean, default=False)  # User is a signal provider
    
    # Validation
    last_validated_at = Column(DateTime, nullable=True)
    last_synced_at = Column(DateTime, nullable=True)
    validation_error = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("user_id", "exchange", "label", name="uq_user_exchange_connection"),
        Index("idx_exchange_conn_user", "user_id"),
        Index("idx_exchange_conn_exchange", "exchange"),
    )


# ============================================================================
# ACTIVITY LOG MODEL
# ============================================================================

class ActivityLog(Base):
    """Audit log for all backend activities"""
    __tablename__ = "activity_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Action info
    action = Column(String(100), nullable=False)  # e.g., "trade.execute", "subscription.create"
    entity_type = Column(String(50), nullable=False)  # e.g., "trade", "subscription", "exchange"
    entity_id = Column(String(255), nullable=True)  # ID of affected entity
    
    # Details
    details = Column(JSON, default=dict)  # Additional context
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(500), nullable=True)
    
    # Result
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index("idx_activity_user", "user_id"),
        Index("idx_activity_action", "action"),
        Index("idx_activity_entity", "entity_type", "entity_id"),
        Index("idx_activity_created", "created_at"),
    )


# ============================================================================
# SUPPORTED EXCHANGE MODEL (for caching CCXT exchanges)
# ============================================================================

class SupportedExchange(Base):
    """Cached list of supported exchanges from CCXT"""
    __tablename__ = "supported_exchanges"
    
    id = Column(String(50), primary_key=True)  # Exchange ID (e.g., 'binance')
    
    # Display info
    name = Column(String(100), nullable=False)
    display_name = Column(String(100), nullable=False)
    logo_url = Column(String(500), nullable=True)
    
    # Type and features
    exchange_type = Column(Enum(ExchangeType), default=ExchangeType.CEX)
    countries = Column(JSON, default=list)
    
    # Capabilities
    has_fetch_my_trades = Column(Boolean, default=False)
    has_fetch_orders = Column(Boolean, default=False)
    has_fetch_balance = Column(Boolean, default=False)
    has_create_order = Column(Boolean, default=False)
    has_cancel_order = Column(Boolean, default=False)
    has_websocket = Column(Boolean, default=False)
    
    # Trading pairs
    trading_pairs_count = Column(Integer, default=0)
    
    # Rate limits
    rate_limit = Column(Integer, default=1000)  # ms between requests
    
    # Documentation
    api_docs_url = Column(String(500), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_supported_exchange_type", "exchange_type"),
        Index("idx_supported_exchange_active", "is_active"),
    )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def generate_uuid():
    """Generate a new UUID"""
    return uuid.uuid4()
