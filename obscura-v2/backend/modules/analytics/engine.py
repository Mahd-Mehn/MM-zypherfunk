import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_async_session, Trade, Position, AnalyticsSnapshot, User
from shared.services import RedisService, CacheKeys

logger = logging.getLogger(__name__)

class AnalyticsEngine:
    def __init__(self):
        self.redis = RedisService()
        self._lock = asyncio.Lock()

    async def record_trade(self, user_id: str, trade_data: Dict[str, Any]):
        """Record a trade execution and update metrics"""
        try:
            async with get_async_session() as session:
                # Create trade record
                trade = Trade(
                    user_id=user_id,
                    exchange=trade_data.get('exchange'),
                    symbol=trade_data.get('symbol'),
                    side=trade_data.get('side'),
                    amount=float(trade_data.get('amount', 0)),
                    price=float(trade_data.get('price', 0)),
                    fee=float(trade_data.get('fee', 0)),
                    fee_currency=trade_data.get('fee_currency'),
                    timestamp=datetime.fromisoformat(trade_data.get('timestamp', datetime.utcnow().isoformat())),
                    order_id=trade_data.get('order_id'),
                    strategy_id=trade_data.get('strategy_id'),
                    pnl=float(trade_data.get('pnl', 0)) if trade_data.get('pnl') else None
                )
                session.add(trade)
                
                # Update position if applicable
                if trade_data.get('position_id'):
                    await self._update_position_from_trade(session, trade_data)
                
                await session.commit()
                
                # Invalidate cache and publish update
                await self.redis.delete(CacheKeys.user_metrics(user_id))
                await self.redis.publish_event(
                    f"analytics.trade.{user_id}",
                    {
                        "type": "trade_recorded",
                        "data": trade_data
                    }
                )
                
                # Trigger async metrics update
                asyncio.create_task(self.update_user_metrics(user_id))
                
                return trade.id
                
        except Exception as e:
            logger.error(f"Error recording trade: {str(e)}")
            raise

    async def _update_position_from_trade(self, session: AsyncSession, trade_data: Dict[str, Any]):
        """Update position status based on trade"""
        position_id = trade_data.get('position_id')
        stmt = select(Position).where(Position.id == position_id)
        result = await session.execute(stmt)
        position = result.scalar_one_or_none()
        
        if position:
            # Update position logic would go here (avg entry, size, etc)
            # For now we just update timestamp
            position.updated_at = datetime.utcnow()
            if trade_data.get('close_position'):
                position.status = 'closed'
                position.closed_at = datetime.utcnow()
                position.realized_pnl = float(trade_data.get('pnl', 0))

    async def get_user_metrics(self, user_id: str, timeframe: str = '24h') -> Dict[str, Any]:
        """Get cached user metrics or calculate fresh"""
        cache_key = CacheKeys.user_metrics(user_id)
        cached = await self.redis.get_cached(cache_key)
        
        if cached:
            return cached
            
        metrics = await self.calculate_metrics(user_id, timeframe)
        await self.redis.set_cached(cache_key, metrics, ttl=300)  # Cache for 5 mins
        return metrics

    async def calculate_metrics(self, user_id: str, timeframe: str = '24h') -> Dict[str, Any]:
        """Calculate comprehensive trading metrics from DB"""
        async with get_async_session() as session:
            # Determine time range
            now = datetime.utcnow()
            if timeframe == '24h':
                start_time = now - timedelta(days=1)
            elif timeframe == '7d':
                start_time = now - timedelta(days=7)
            elif timeframe == '30d':
                start_time = now - timedelta(days=30)
            else:
                start_time = now - timedelta(days=1) # Default

            # Query trades
            stmt = select(Trade).where(
                Trade.user_id == user_id,
                Trade.timestamp >= start_time
            )
            result = await session.execute(stmt)
            trades = result.scalars().all()
            
            if not trades:
                return self._empty_metrics()

            # Calculate metrics
            total_trades = len(trades)
            winning_trades = [t for t in trades if (t.pnl or 0) > 0]
            losing_trades = [t for t in trades if (t.pnl or 0) <= 0]
            
            total_pnl = sum(t.pnl or 0 for t in trades)
            win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
            
            volume = sum(t.amount * t.price for t in trades)
            
            metrics = {
                "total_trades": total_trades,
                "win_rate": win_rate,
                "total_pnl": total_pnl,
                "volume": volume,
                "profit_factor": self._calculate_profit_factor(winning_trades, losing_trades),
                "updated_at": now.isoformat()
            }
            
            # Store snapshot
            snapshot = AnalyticsSnapshot(
                user_id=user_id,
                timestamp=now,
                total_value=0, # Would need balance integration
                pnl_24h=total_pnl if timeframe == '24h' else 0,
                volume_24h=volume if timeframe == '24h' else 0,
                win_rate=win_rate,
                open_positions=0 # Would need position query
            )
            session.add(snapshot)
            await session.commit()
            
            return metrics

    def _calculate_profit_factor(self, winning_trades: List[Trade], losing_trades: List[Trade]) -> float:
        gross_profit = sum(t.pnl or 0 for t in winning_trades)
        gross_loss = abs(sum(t.pnl or 0 for t in losing_trades))
        
        if gross_loss == 0:
            return float('inf') if gross_profit > 0 else 0
            
        return gross_profit / gross_loss

    def _empty_metrics(self) -> Dict[str, Any]:
        return {
            "total_trades": 0,
            "win_rate": 0,
            "total_pnl": 0,
            "volume": 0,
            "profit_factor": 0,
            "updated_at": datetime.utcnow().isoformat()
        }

    async def update_user_metrics(self, user_id: str):
        """Background task to update metrics"""
        async with self._lock:
            await self.calculate_metrics(user_id, '24h')
            await self.calculate_metrics(user_id, '7d')
            await self.calculate_metrics(user_id, '30d')

# Global instance
analytics_engine = AnalyticsEngine()
