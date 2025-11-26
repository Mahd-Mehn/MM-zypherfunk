"""
Database Repository Layer for Obscura V2

Provides a clean abstraction over database operations with caching support.
All database access should go through these repositories.
"""

import uuid
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import select, update, delete, func, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import (
    User, UserRole, TraderProfile, APIKeyStore, Trade, Position,
    Follower, CopyTradingConfig, UserSubscription, PaymentTransaction,
    AnalyticsSnapshot, MonitoringSession, ActivityLog, ExchangeConnection,
    OrderSide, OrderType, OrderStatus, ExchangeType, SubscriptionTier, PaymentStatus
)
from .connection import get_async_session
from shared.services import redis_service, CacheKeys

logger = logging.getLogger("obscura.repositories")


# =============================================================================
# Base Repository
# =============================================================================

class BaseRepository:
    """Base repository with common operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def commit(self):
        await self.session.commit()
    
    async def rollback(self):
        await self.session.rollback()
    
    async def refresh(self, obj):
        await self.session.refresh(obj)


# =============================================================================
# User Repository
# =============================================================================

class UserRepository(BaseRepository):
    """Repository for User operations"""
    
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID with caching"""
        cache_key = CacheKeys.user_profile(user_id)
        cached = await redis_service.get_json(cache_key)
        
        if cached:
            # Return cached data as dict (caller can construct User if needed)
            return cached
        
        result = await self.session.execute(
            select(User).where(User.id == uuid.UUID(user_id))
        )
        user = result.scalar_one_or_none()
        
        if user:
            user_dict = self._user_to_dict(user)
            await redis_service.set_json(cache_key, user_dict, ttl_seconds=300)
            return user
        
        return None
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_by_wallet(self, wallet_address: str) -> Optional[User]:
        """Get user by wallet address"""
        result = await self.session.execute(
            select(User).where(User.wallet_address == wallet_address)
        )
        return result.scalar_one_or_none()
    
    async def create(self, **kwargs) -> User:
        """Create new user"""
        user = User(**kwargs)
        self.session.add(user)
        await self.session.flush()
        return user
    
    async def update(self, user_id: str, **kwargs) -> Optional[User]:
        """Update user"""
        await self.session.execute(
            update(User).where(User.id == uuid.UUID(user_id)).values(**kwargs)
        )
        # Invalidate cache
        await redis_service.delete(CacheKeys.user_profile(user_id))
        return await self.get_by_id(user_id)
    
    def _user_to_dict(self, user: User) -> Dict[str, Any]:
        """Convert user to dictionary"""
        return {
            "id": str(user.id),
            "email": user.email,
            "wallet_address": user.wallet_address,
            "username": user.username,
            "display_name": user.display_name,
            "avatar_url": user.avatar_url,
            "bio": user.bio,
            "role": user.role.value if user.role else "user",
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }


# =============================================================================
# Trader Repository
# =============================================================================

class TraderRepository(BaseRepository):
    """Repository for Trader operations"""
    
    async def get_profile(self, user_id: str) -> Optional[TraderProfile]:
        """Get trader profile"""
        cache_key = f"trader:profile:{user_id}"
        cached = await redis_service.get_json(cache_key)
        
        if cached:
            return cached
        
        result = await self.session.execute(
            select(TraderProfile)
            .options(selectinload(TraderProfile.user))
            .where(TraderProfile.user_id == uuid.UUID(user_id))
        )
        profile = result.scalar_one_or_none()
        
        if profile:
            profile_dict = self._profile_to_dict(profile)
            await redis_service.set_json(cache_key, profile_dict, ttl_seconds=60)
            return profile
        
        return None
    
    async def get_leaderboard(
        self,
        limit: int = 50,
        offset: int = 0,
        timeframe: str = "30d",
        sort_by: str = "pnl"
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get trader leaderboard with pagination"""
        cache_key = f"leaderboard:{timeframe}:{sort_by}:{offset}:{limit}"
        cached = await redis_service.get_json(cache_key)
        
        if cached:
            return cached["traders"], cached["total"]
        
        # Build sort column
        sort_columns = {
            "pnl": TraderProfile.total_pnl_usd,
            "winRate": TraderProfile.win_rate,
            "followers": func.count(Follower.id),
            "trades": TraderProfile.total_trades,
        }
        
        # Count total
        count_result = await self.session.execute(
            select(func.count(TraderProfile.id))
            .where(TraderProfile.is_public == True)
        )
        total = count_result.scalar()
        
        # Build query
        query = (
            select(TraderProfile)
            .options(selectinload(TraderProfile.user))
            .where(TraderProfile.is_public == True)
            .order_by(desc(sort_columns.get(sort_by, TraderProfile.total_pnl_usd)))
            .offset(offset)
            .limit(limit)
        )
        
        result = await self.session.execute(query)
        profiles = result.scalars().all()
        
        traders = [self._profile_to_dict(p) for p in profiles]
        
        # Cache for 30 seconds
        await redis_service.set_json(
            cache_key, 
            {"traders": traders, "total": total}, 
            ttl_seconds=30
        )
        
        return traders, total
    
    async def get_followers_count(self, trader_id: str) -> int:
        """Get follower count for a trader"""
        result = await self.session.execute(
            select(func.count(Follower.id))
            .where(
                and_(
                    Follower.trader_id == uuid.UUID(trader_id),
                    Follower.is_active == True
                )
            )
        )
        return result.scalar() or 0
    
    async def get_followers(self, trader_id: str) -> List[Dict[str, Any]]:
        """Get list of followers for a trader"""
        result = await self.session.execute(
            select(Follower)
            .options(
                selectinload(Follower.follower),
                selectinload(Follower.copy_config)
            )
            .where(
                and_(
                    Follower.trader_id == uuid.UUID(trader_id),
                    Follower.is_active == True
                )
            )
        )
        followers = result.scalars().all()
        
        return [
            {
                "id": str(f.id),
                "follower_id": str(f.follower_id),
                "display_name": f.follower.display_name if f.follower else None,
                "follower_email": f.follower.email if f.follower else None,
                "follower_address": f.follower.wallet_address if f.follower else None,
                "is_copying": f.is_copying,
                "followed_at": f.followed_at.isoformat() if f.followed_at else None,
                # Subscription details
                "status": "active" if (f.copy_config and f.copy_config.is_active and not f.copy_config.is_paused) else ("paused" if (f.copy_config and f.copy_config.is_paused) else "inactive"),
                "max_capital_pct": float(f.copy_config.proportion_percent) if f.copy_config else 0,
                "max_position_size": float(f.copy_config.max_position_usd) if (f.copy_config and f.copy_config.max_position_usd) else None,
                "stop_loss_pct": float(f.copy_config.stop_loss_percent) if (f.copy_config and f.copy_config.stop_loss_percent) else None,
                "take_profit_pct": None,
                "total_trades_copied": f.copy_config.total_copied_trades if f.copy_config else 0,
                "total_profit_loss": float(f.copy_config.total_pnl_usd) if f.copy_config else 0,
                "created_at": f.created_at.isoformat() if hasattr(f, 'created_at') and f.created_at else (f.followed_at.isoformat() if f.followed_at else None),
                "updated_at": f.copy_config.updated_at.isoformat() if (f.copy_config and f.copy_config.updated_at) else None,
            }
            for f in followers
        ]
    
    async def update_stats(self, user_id: str, stats: Dict[str, Any]) -> None:
        """Update trader statistics"""
        await self.session.execute(
            update(TraderProfile)
            .where(TraderProfile.user_id == uuid.UUID(user_id))
            .values(
                total_trades=stats.get("total_trades"),
                win_rate=stats.get("win_rate"),
                total_pnl_usd=stats.get("total_pnl_usd"),
                sharpe_ratio=stats.get("sharpe_ratio"),
                max_drawdown=stats.get("max_drawdown"),
                stats_updated_at=datetime.utcnow()
            )
        )
        # Invalidate cache
        await redis_service.delete(f"trader:profile:{user_id}")
    
    def _profile_to_dict(self, profile: TraderProfile) -> Dict[str, Any]:
        """Convert trader profile to dictionary"""
        user = profile.user
        return {
            "id": str(profile.user_id),
            "address": user.wallet_address if user else None,
            "display_name": user.display_name if user else f"Trader-{str(profile.user_id)[:8]}",
            "bio": user.bio if user else "",
            "avatar_url": user.avatar_url if user else None,
            "verification_types": [],
            "win_rate": float(profile.win_rate or 0),
            "total_trades": profile.total_trades or 0,
            "verified_trades": profile.total_trades or 0,
            "total_pnl": float(profile.total_pnl_usd or 0),
            "followers": 0,  # Calculated separately
            "performance_fee": float(profile.performance_fee_percent or 0),
            "chains": [],
            "exchanges": [],
            "trust_tier": 1,
            "joined_date": user.created_at.isoformat() if user and user.created_at else None,
            "rank_overall": profile.rank_overall,
            "rank_monthly": profile.rank_monthly,
        }


# =============================================================================
# Trade Repository
# =============================================================================

class TradeRepository(BaseRepository):
    """Repository for Trade operations"""
    
    async def create(self, **kwargs) -> Trade:
        """Create a new trade record"""
        trade = Trade(**kwargs)
        self.session.add(trade)
        await self.session.flush()
        return trade
    
    async def get_by_id(self, trade_id: str) -> Optional[Trade]:
        """Get trade by ID"""
        result = await self.session.execute(
            select(Trade).where(Trade.id == uuid.UUID(trade_id))
        )
        return result.scalar_one_or_none()
    
    async def get_user_trades(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
        symbol: Optional[str] = None,
        exchange: Optional[str] = None,
        status: Optional[str] = None
    ) -> Tuple[List[Trade], int]:
        """Get trades for a user with pagination and filters"""
        conditions = [Trade.user_id == uuid.UUID(user_id)]
        
        if symbol:
            conditions.append(Trade.symbol == symbol)
        if exchange:
            conditions.append(Trade.exchange == exchange)
        if status:
            conditions.append(Trade.status == OrderStatus(status))
        
        # Count total
        count_result = await self.session.execute(
            select(func.count(Trade.id)).where(and_(*conditions))
        )
        total = count_result.scalar()
        
        # Get trades
        result = await self.session.execute(
            select(Trade)
            .where(and_(*conditions))
            .order_by(desc(Trade.created_at))
            .offset(offset)
            .limit(limit)
        )
        trades = result.scalars().all()
        
        return trades, total
    
    async def get_trades_summary(self, user_id: str, since: Optional[datetime] = None) -> Dict[str, Any]:
        """Get trade summary statistics"""
        conditions = [Trade.user_id == uuid.UUID(user_id)]
        if since:
            conditions.append(Trade.created_at >= since)
        
        result = await self.session.execute(
            select(
                func.count(Trade.id).label("total"),
                func.sum(Trade.pnl_usd).label("total_pnl"),
                func.count(Trade.id).filter(Trade.pnl_usd > 0).label("winning"),
                func.count(Trade.id).filter(Trade.pnl_usd < 0).label("losing"),
                func.avg(Trade.notional_value_usd).label("avg_size"),
            )
            .where(and_(*conditions))
        )
        row = result.one()
        
        total = row.total or 0
        winning = row.winning or 0
        
        return {
            "total_trades": total,
            "total_pnl": float(row.total_pnl or 0),
            "winning_trades": winning,
            "losing_trades": row.losing or 0,
            "win_rate": (winning / total * 100) if total > 0 else 0,
            "avg_trade_size": float(row.avg_size or 0),
        }
    
    def trade_to_dict(self, trade: Trade) -> Dict[str, Any]:
        """Convert trade to dictionary"""
        return {
            "id": str(trade.id),
            "exchange": trade.exchange,
            "symbol": trade.symbol,
            "side": trade.side.value if trade.side else None,
            "order_type": trade.order_type.value if trade.order_type else None,
            "status": trade.status.value if trade.status else None,
            "amount": float(trade.amount or 0),
            "filled_amount": float(trade.filled_amount or 0),
            "price": float(trade.price or 0),
            "average_fill_price": float(trade.average_fill_price or 0),
            "pnl_usd": float(trade.pnl_usd or 0),
            "fees_usd": float(trade.fees_usd or 0),
            "is_copy_trade": trade.is_copy_trade,
            "created_at": trade.created_at.isoformat() if trade.created_at else None,
            "executed_at": trade.executed_at.isoformat() if trade.executed_at else None,
        }


# =============================================================================
# Exchange Connection Repository
# =============================================================================

class ExchangeConnectionRepository(BaseRepository):
    """Repository for Exchange Connection operations"""
    
    async def create(self, **kwargs) -> ExchangeConnection:
        """Create exchange connection"""
        conn = ExchangeConnection(**kwargs)
        self.session.add(conn)
        await self.session.flush()
        return conn
    
    async def get_by_id(self, connection_id: str) -> Optional[ExchangeConnection]:
        """Get connection by ID"""
        result = await self.session.execute(
            select(ExchangeConnection)
            .where(ExchangeConnection.id == uuid.UUID(connection_id))
        )
        return result.scalar_one_or_none()
    
    async def get_user_connections(self, user_id: str) -> List[ExchangeConnection]:
        """Get all exchange connections for a user"""
        result = await self.session.execute(
            select(ExchangeConnection)
            .where(
                and_(
                    ExchangeConnection.user_id == uuid.UUID(user_id),
                    ExchangeConnection.is_active == True
                )
            )
            .order_by(desc(ExchangeConnection.created_at))
        )
        return result.scalars().all()
    
    async def update_status(
        self, 
        connection_id: str, 
        status: str, 
        last_synced_at: Optional[datetime] = None
    ) -> None:
        """Update connection status"""
        values = {"status": status}
        if last_synced_at:
            values["last_synced_at"] = last_synced_at
        
        await self.session.execute(
            update(ExchangeConnection)
            .where(ExchangeConnection.id == uuid.UUID(connection_id))
            .values(**values)
        )
    
    async def delete(self, connection_id: str) -> bool:
        """Delete exchange connection"""
        result = await self.session.execute(
            delete(ExchangeConnection)
            .where(ExchangeConnection.id == uuid.UUID(connection_id))
        )
        return result.rowcount > 0
    
    def connection_to_dict(self, conn: ExchangeConnection) -> Dict[str, Any]:
        """Convert connection to dictionary"""
        return {
            "id": str(conn.id),
            "user_id": str(conn.user_id),
            "exchange": conn.exchange,
            "exchange_type": conn.exchange_type.value if conn.exchange_type else "cex",
            "label": conn.label,
            "status": conn.status,
            "is_signal_provider": conn.is_signal_provider,
            "last_synced_at": conn.last_synced_at.isoformat() if conn.last_synced_at else None,
            "created_at": conn.created_at.isoformat() if conn.created_at else None,
        }


# =============================================================================
# Subscription Repository
# =============================================================================

class SubscriptionRepository(BaseRepository):
    """Repository for Subscription operations"""
    
    async def create(self, **kwargs) -> CopyTradingConfig:
        """Create a copy trading subscription"""
        # First create the follower relationship
        follower = Follower(
            trader_id=uuid.UUID(kwargs.pop("trader_id")),
            follower_id=uuid.UUID(kwargs.pop("follower_id")),
            is_active=True,
            is_copying=False,
        )
        self.session.add(follower)
        await self.session.flush()
        
        # Then create the config
        config = CopyTradingConfig(
            follower_rel_id=follower.id,
            trader_id=follower.trader_id,
            **kwargs
        )
        self.session.add(config)
        await self.session.flush()
        
        return config
    
    async def get_by_id(self, subscription_id: str) -> Optional[CopyTradingConfig]:
        """Get subscription by ID"""
        result = await self.session.execute(
            select(CopyTradingConfig)
            .options(selectinload(CopyTradingConfig.follower_rel))
            .where(CopyTradingConfig.id == uuid.UUID(subscription_id))
        )
        return result.scalar_one_or_none()
    
    async def get_user_subscriptions(
        self, 
        user_id: str,
        active_only: bool = True
    ) -> List[CopyTradingConfig]:
        """Get all subscriptions for a user (as follower)"""
        conditions = [Follower.follower_id == uuid.UUID(user_id)]
        if active_only:
            conditions.append(CopyTradingConfig.is_active == True)
        
        result = await self.session.execute(
            select(CopyTradingConfig)
            .join(Follower)
            .options(
                selectinload(CopyTradingConfig.follower_rel),
                selectinload(CopyTradingConfig.trader)
            )
            .where(and_(*conditions))
        )
        return result.scalars().all()
    
    async def update(self, subscription_id: str, **kwargs) -> Optional[CopyTradingConfig]:
        """Update subscription"""
        await self.session.execute(
            update(CopyTradingConfig)
            .where(CopyTradingConfig.id == uuid.UUID(subscription_id))
            .values(**kwargs)
        )
        return await self.get_by_id(subscription_id)
    
    async def pause(self, subscription_id: str, reason: str = "User paused") -> None:
        """Pause subscription"""
        await self.session.execute(
            update(CopyTradingConfig)
            .where(CopyTradingConfig.id == uuid.UUID(subscription_id))
            .values(is_paused=True, pause_reason=reason)
        )
    
    async def resume(self, subscription_id: str) -> None:
        """Resume subscription"""
        await self.session.execute(
            update(CopyTradingConfig)
            .where(CopyTradingConfig.id == uuid.UUID(subscription_id))
            .values(is_paused=False, pause_reason=None)
        )
    
    async def cancel(self, subscription_id: str) -> None:
        """Cancel subscription"""
        await self.session.execute(
            update(CopyTradingConfig)
            .where(CopyTradingConfig.id == uuid.UUID(subscription_id))
            .values(is_active=False)
        )
        
        # Also update follower relationship
        config = await self.get_by_id(subscription_id)
        if config and config.follower_rel:
            await self.session.execute(
                update(Follower)
                .where(Follower.id == config.follower_rel_id)
                .values(is_copying=False, unfollowed_at=datetime.utcnow())
            )
    
    def subscription_to_dict(self, config: CopyTradingConfig) -> Dict[str, Any]:
        """Convert subscription to dictionary"""
        return {
            "id": str(config.id),
            "follower_id": str(config.follower_rel.follower_id) if config.follower_rel else None,
            "trader_id": str(config.trader_id),
            "status": "paused" if config.is_paused else ("active" if config.is_active else "cancelled"),
            "copy_mode": config.copy_mode,
            "max_capital_pct": float(config.proportion_percent or 100),
            "max_position_size": float(config.max_position_usd) if config.max_position_usd else None,
            "stop_loss_pct": float(config.stop_loss_percent) if config.stop_loss_percent else None,
            "take_profit_pct": None,
            "total_copied_trades": config.total_copied_trades or 0,
            "total_pnl": float(config.total_pnl_usd or 0),
            "created_at": config.created_at.isoformat() if config.created_at else None,
        }


# =============================================================================
# Activity Log Repository
# =============================================================================

class ActivityLogRepository(BaseRepository):
    """Repository for Activity Log operations"""
    
    async def log(
        self,
        user_id: Optional[str],
        action: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> ActivityLog:
        """Log an activity"""
        log = ActivityLog(
            user_id=uuid.UUID(user_id) if user_id else None,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details or {},
            ip_address=ip_address,
        )
        self.session.add(log)
        await self.session.flush()
        return log
    
    async def get_user_activities(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        action: Optional[str] = None
    ) -> Tuple[List[ActivityLog], int]:
        """Get activities for a user"""
        conditions = [ActivityLog.user_id == uuid.UUID(user_id)]
        if action:
            conditions.append(ActivityLog.action == action)
        
        count_result = await self.session.execute(
            select(func.count(ActivityLog.id)).where(and_(*conditions))
        )
        total = count_result.scalar()
        
        result = await self.session.execute(
            select(ActivityLog)
            .where(and_(*conditions))
            .order_by(desc(ActivityLog.created_at))
            .offset(offset)
            .limit(limit)
        )
        activities = result.scalars().all()
        
        return activities, total


# =============================================================================
# Portfolio Repository
# =============================================================================

class PortfolioRepository(BaseRepository):
    """Repository for Portfolio/Position operations"""
    
    async def get_positions(self, user_id: str, open_only: bool = True) -> List[Position]:
        """Get user positions"""
        conditions = [Position.user_id == uuid.UUID(user_id)]
        if open_only:
            conditions.append(Position.is_open == True)
        
        result = await self.session.execute(
            select(Position)
            .where(and_(*conditions))
            .order_by(desc(Position.opened_at))
        )
        return result.scalars().all()
    
    async def get_portfolio_value(self, user_id: str) -> Dict[str, Any]:
        """Calculate total portfolio value"""
        positions = await self.get_positions(user_id)
        
        total_value = Decimal("0")
        total_unrealized_pnl = Decimal("0")
        
        position_list = []
        for pos in positions:
            value = pos.size * (pos.current_price or pos.entry_price)
            total_value += value
            total_unrealized_pnl += pos.unrealized_pnl_usd or Decimal("0")
            
            # Calculate metrics
            market_value = float(value)
            unrealized_pnl = float(pos.unrealized_pnl_usd or 0)
            cost_basis = float(pos.size * pos.entry_price)
            pnl_pct = (unrealized_pnl / cost_basis * 100) if cost_basis > 0 else 0
            
            position_list.append({
                "symbol": pos.symbol,
                "exchange": pos.exchange,
                "side": pos.side.value if pos.side else None,
                "size": float(pos.size),
                "entry_price": float(pos.entry_price),
                "current_price": float(pos.current_price or pos.entry_price),
                "unrealized_pnl": unrealized_pnl,
                "leverage": float(pos.leverage or 1),
                
                # Frontend compatibility fields
                "quantity": float(pos.size),
                "average_price": float(pos.entry_price),
                "market_value_usd": market_value,
                "unrealized_pnl_usd": unrealized_pnl,
                "unrealized_pnl_percentage": pnl_pct,
                "last_updated": pos.updated_at.isoformat() if pos.updated_at else datetime.utcnow().isoformat()
            })
        
        return {
            "total_value_usd": float(total_value),
            "total_unrealized_pnl": float(total_unrealized_pnl),
            "positions": position_list,
            "position_count": len(positions),
        }
    
    async def get_analytics_snapshot(
        self,
        user_id: str,
        period_type: str = "daily",
        limit: int = 30
    ) -> List[AnalyticsSnapshot]:
        """Get analytics snapshots for performance charting"""
        result = await self.session.execute(
            select(AnalyticsSnapshot)
            .where(
                and_(
                    AnalyticsSnapshot.user_id == uuid.UUID(user_id),
                    AnalyticsSnapshot.period_type == period_type
                )
            )
            .order_by(desc(AnalyticsSnapshot.period_start))
            .limit(limit)
        )
        return result.scalars().all()


# =============================================================================
# Repository Factory
# =============================================================================

class RepositoryFactory:
    """Factory for creating repositories with shared session"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self._user_repo = None
        self._trader_repo = None
        self._trade_repo = None
        self._exchange_repo = None
        self._subscription_repo = None
        self._activity_repo = None
        self._portfolio_repo = None
    
    @property
    def users(self) -> UserRepository:
        if not self._user_repo:
            self._user_repo = UserRepository(self.session)
        return self._user_repo
    
    @property
    def traders(self) -> TraderRepository:
        if not self._trader_repo:
            self._trader_repo = TraderRepository(self.session)
        return self._trader_repo
    
    @property
    def trades(self) -> TradeRepository:
        if not self._trade_repo:
            self._trade_repo = TradeRepository(self.session)
        return self._trade_repo
    
    @property
    def exchanges(self) -> ExchangeConnectionRepository:
        if not self._exchange_repo:
            self._exchange_repo = ExchangeConnectionRepository(self.session)
        return self._exchange_repo
    
    @property
    def subscriptions(self) -> SubscriptionRepository:
        if not self._subscription_repo:
            self._subscription_repo = SubscriptionRepository(self.session)
        return self._subscription_repo
    
    @property
    def activities(self) -> ActivityLogRepository:
        if not self._activity_repo:
            self._activity_repo = ActivityLogRepository(self.session)
        return self._activity_repo
    
    @property
    def portfolio(self) -> PortfolioRepository:
        if not self._portfolio_repo:
            self._portfolio_repo = PortfolioRepository(self.session)
        return self._portfolio_repo
    
    async def commit(self):
        await self.session.commit()
    
    async def rollback(self):
        await self.session.rollback()


async def get_repositories() -> RepositoryFactory:
    """Get repository factory with new session"""
    async with get_async_session() as session:
        yield RepositoryFactory(session)
