"""
Trade Monitoring System

Real-time monitoring of traders' orders, positions, and executions.
Powers the copy trading functionality by detecting and relaying trades.
Backed by PostgreSQL and Redis.
"""

import asyncio
import logging
import json
from typing import Dict, Any, List, Optional, Callable, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_async_session, MonitoringSession, APIKeyStore, Trade, Position
from shared.services import RedisService, CacheKeys
from modules.trading.exchanges.universal_connector import UniversalConnector, create_connector
from modules.trading import key_storage

logger = logging.getLogger("obscura.monitoring")


class TradeEventType(Enum):
    """Types of trade events"""
    ORDER_PLACED = "order_placed"
    ORDER_FILLED = "order_filled"
    ORDER_PARTIALLY_FILLED = "order_partially_filled"
    ORDER_CANCELED = "order_canceled"
    POSITION_OPENED = "position_opened"
    POSITION_CLOSED = "position_closed"
    POSITION_UPDATED = "position_updated"
    STOP_LOSS_TRIGGERED = "stop_loss_triggered"
    TAKE_PROFIT_TRIGGERED = "take_profit_triggered"


@dataclass
class TradeEvent:
    """Trade event from monitored trader"""
    event_id: str
    event_type: TradeEventType
    trader_id: str
    exchange: str
    symbol: str
    side: str
    order_type: str
    quantity: float
    price: Optional[float]
    filled_quantity: float
    timestamp: datetime
    order_id: str
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "trader_id": str(self.trader_id),
            "exchange": self.exchange,
            "symbol": self.symbol,
            "side": self.side,
            "order_type": self.order_type,
            "quantity": self.quantity,
            "price": self.price,
            "filled_quantity": self.filled_quantity,
            "timestamp": self.timestamp.isoformat(),
            "order_id": self.order_id,
            "raw_data": self.raw_data
        }


class TradeMonitor:
    """
    Real-time trade monitoring system.
    """
    
    def __init__(self):
        self.redis = RedisService()
        self.connectors: Dict[str, UniversalConnector] = {}  # session_id -> connector
        self.active_sessions: Dict[str, MonitoringSession] = {} # session_id -> session object
        
        self._monitoring = False
        self._poll_interval = 5  # seconds
        self._monitor_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        
        logger.info("TradeMonitor initialized with DB/Redis backend")

    async def start_monitoring(self):
        """Start the monitoring loop and load active sessions"""
        if self._monitoring:
            return
        
        self._monitoring = True
        await self._load_active_sessions()
        self._monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Trade monitoring started")

    async def stop_monitoring(self):
        """Stop the monitoring loop"""
        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        # Close all connectors
        for connector in self.connectors.values():
            if hasattr(connector.exchange, 'close'):
                await connector.exchange.close()
        
        self.connectors.clear()
        self.active_sessions.clear()
        logger.info("Trade monitoring stopped")

    async def add_session(
        self,
        trader_id: str,
        exchange: str,
        symbols: Optional[List[str]] = None
    ) -> str:
        """
        Add a monitoring session for a trader.
        """
        async with get_async_session() as session:
            # Check if session already exists
            stmt = select(MonitoringSession).where(
                MonitoringSession.trader_id == trader_id,
                MonitoringSession.exchange == exchange,
                MonitoringSession.is_active == True
            )
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                if symbols:
                    existing.symbols = symbols
                    await session.commit()
                return str(existing.id)
            
            # Create new session
            monitoring_session = MonitoringSession(
                trader_id=trader_id,
                exchange=exchange,
                symbols=symbols,
                is_active=True,
                connection_status='initializing'
            )
            session.add(monitoring_session)
            await session.commit()
            await session.refresh(monitoring_session)
            
            # Initialize connector immediately
            await self._init_connector(monitoring_session)
            
            return str(monitoring_session.id)

    async def remove_session(self, session_id: str):
        """Remove/Deactivate a monitoring session"""
        async with get_async_session() as session:
            stmt = select(MonitoringSession).where(MonitoringSession.id == session_id)
            result = await session.execute(stmt)
            monitoring_session = result.scalar_one_or_none()
            
            if monitoring_session:
                monitoring_session.is_active = False
                monitoring_session.connection_status = 'disconnected'
                await session.commit()
        
        # Remove from memory
        if session_id in self.connectors:
            connector = self.connectors.pop(session_id)
            if hasattr(connector.exchange, 'close'):
                await connector.exchange.close()
        
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]

    async def _load_active_sessions(self):
        """Load all active sessions from DB"""
        async with get_async_session() as session:
            stmt = select(MonitoringSession).where(MonitoringSession.is_active == True)
            result = await session.execute(stmt)
            sessions = result.scalars().all()
            
            for s in sessions:
                await self._init_connector(s)

    async def _init_connector(self, session_obj: MonitoringSession):
        """Initialize connector for a session"""
        try:
            # Find credentials
            async with get_async_session() as db_session:
                stmt = select(APIKeyStore).where(
                    APIKeyStore.user_id == session_obj.trader_id,
                    APIKeyStore.exchange == session_obj.exchange,
                    APIKeyStore.is_active == True
                )
                result = await db_session.execute(stmt)
                creds_store = result.scalars().first()
                
                if not creds_store:
                    logger.error(f"No credentials found for session {session_obj.id}")
                    return

                # Get actual secrets
                creds = await key_storage.get_credentials_for_trading(
                    str(creds_store.id),
                    str(session_obj.trader_id)
                )
                
                if not creds:
                    logger.error(f"Failed to retrieve secrets for session {session_obj.id}")
                    return

                # Create connector
                connector = await create_connector(session_obj.exchange, creds)
                
                async with self._lock:
                    self.connectors[str(session_obj.id)] = connector
                    self.active_sessions[str(session_obj.id)] = session_obj
                    
                # Update status
                session_obj.connection_status = 'connected'
                # Note: session_obj is detached here if we closed the session, 
                # but we are just updating memory object or need to update DB
                
                # Update DB status
                stmt_update = update(MonitoringSession).where(
                    MonitoringSession.id == session_obj.id
                ).values(connection_status='connected')
                await db_session.execute(stmt_update)
                await db_session.commit()
                
                logger.info(f"Initialized connector for session {session_obj.id}")

        except Exception as e:
            logger.error(f"Error initializing session {session_obj.id}: {e}")

    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self._monitoring:
            try:
                # Copy keys to avoid modification during iteration
                session_ids = list(self.connectors.keys())
                
                for session_id in session_ids:
                    connector = self.connectors.get(session_id)
                    session_obj = self.active_sessions.get(session_id)
                    
                    if not connector or not session_obj:
                        continue
                    
                    await self._check_activity(session_id, session_obj, connector)
                
                await asyncio.sleep(self._poll_interval)
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(self._poll_interval)

    async def _check_activity(
        self,
        session_id: str,
        session_obj: MonitoringSession,
        connector: UniversalConnector
    ):
        """Check activity for a single session"""
        try:
            # Check orders
            await self._check_orders(session_obj, connector)
            
            # Check positions
            await self._check_positions(session_obj, connector)
            
            # Update heartbeat
            async with get_async_session() as session:
                stmt = update(MonitoringSession).where(
                    MonitoringSession.id == session_id
                ).values(
                    last_heartbeat=datetime.utcnow(),
                    events_received=MonitoringSession.events_received + 1 # Approximate
                )
                await session.execute(stmt)
                await session.commit()
                
        except Exception as e:
            logger.error(f"Error checking activity for {session_id}: {e}")

    async def _check_orders(self, session_obj: MonitoringSession, connector: UniversalConnector):
        """Check for new orders"""
        try:
            if hasattr(connector.exchange, 'fetch_orders'):
                since = int((datetime.utcnow() - timedelta(hours=1)).timestamp() * 1000)
                orders = await connector.exchange.fetch_orders(since=since, limit=20)
            elif hasattr(connector.exchange, 'fetch_open_orders'):
                orders = await connector.exchange.fetch_open_orders()
            else:
                return

            for order in orders:
                # Check if we already processed this order
                # We use Redis to deduplicate events
                event_id = f"{session_obj.exchange}_{order['id']}_{order['status']}"
                if await self.redis.get_cached(f"processed_event:{event_id}"):
                    continue

                # Filter symbols
                if session_obj.symbols and order['symbol'] not in session_obj.symbols:
                    continue

                # Create event
                event = self._create_order_event(session_obj, order)
                
                # Publish event
                await self._publish_event(event)
                
                # Mark as processed
                await self.redis.set_cached(f"processed_event:{event_id}", "1", ttl=3600)

        except Exception as e:
            logger.error(f"Error fetching orders: {e}")

    async def _check_positions(self, session_obj: MonitoringSession, connector: UniversalConnector):
        """Check for position changes"""
        try:
            if not hasattr(connector.exchange, 'fetch_positions'):
                return
            
            positions = await connector.exchange.fetch_positions()
            
            for position in positions:
                symbol = position.get('symbol')
                if session_obj.symbols and symbol not in session_obj.symbols:
                    continue
                
                # Generate a hash of the position state to detect changes
                pos_state = f"{symbol}_{position.get('contracts')}_{position.get('entryPrice')}"
                last_state_key = f"pos_state:{session_obj.trader_id}:{session_obj.exchange}:{symbol}"
                
                last_state = await self.redis.get_cached(last_state_key)
                
                if last_state != pos_state:
                    # Position changed
                    event = self._create_position_event(session_obj, position, last_state is None)
                    await self._publish_event(event)
                    await self.redis.set_cached(last_state_key, pos_state, ttl=86400)

        except Exception as e:
            logger.error(f"Error fetching positions: {e}")

    def _create_order_event(self, session_obj: MonitoringSession, order: Dict) -> TradeEvent:
        status = order.get('status', '').lower()
        filled = float(order.get('filled', 0))
        
        if status == 'closed':
            event_type = TradeEventType.ORDER_FILLED
        elif status == 'canceled':
            event_type = TradeEventType.ORDER_CANCELED
        elif filled > 0:
            event_type = TradeEventType.ORDER_PARTIALLY_FILLED
        else:
            event_type = TradeEventType.ORDER_PLACED

        return TradeEvent(
            event_id=f"evt_{order['id']}_{datetime.utcnow().timestamp()}",
            event_type=event_type,
            trader_id=str(session_obj.trader_id),
            exchange=session_obj.exchange,
            symbol=order['symbol'],
            side=order['side'],
            order_type=order.get('type', 'unknown'),
            quantity=float(order.get('amount', 0)),
            price=float(order['price']) if order.get('price') else None,
            filled_quantity=filled,
            timestamp=datetime.utcnow(),
            order_id=str(order['id']),
            raw_data=order
        )

    def _create_position_event(self, session_obj: MonitoringSession, position: Dict, is_new: bool) -> TradeEvent:
        current_size = float(position.get('contracts', 0) or position.get('amount', 0))
        
        if is_new:
            event_type = TradeEventType.POSITION_OPENED
        elif current_size == 0:
            event_type = TradeEventType.POSITION_CLOSED
        else:
            event_type = TradeEventType.POSITION_UPDATED

        return TradeEvent(
            event_id=f"pos_{session_obj.exchange}_{position.get('symbol')}_{datetime.utcnow().timestamp()}",
            event_type=event_type,
            trader_id=str(session_obj.trader_id),
            exchange=session_obj.exchange,
            symbol=position.get('symbol'),
            side=position.get('side', 'long'),
            order_type='position',
            quantity=abs(current_size),
            price=float(position.get('entryPrice', 0)) if position.get('entryPrice') else None,
            filled_quantity=abs(current_size),
            timestamp=datetime.utcnow(),
            order_id=f"pos_{position.get('symbol')}",
            raw_data=position
        )

    async def _publish_event(self, event: TradeEvent):
        """Publish event to Redis Pub/Sub"""
        channel = f"trade_events:{event.trader_id}"
        await self.redis.publish_event(channel, event.to_dict())
        logger.info(f"Published event {event.event_type.value} for {event.trader_id}")


# Singleton instance
trade_monitor = TradeMonitor()
