"""
Copy Trading Execution Engine

Handles the logic for replicating trades from lead traders to followers.
Listens for trade events and executes corresponding orders for followers.
Backed by PostgreSQL and Redis.
"""

import asyncio
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import (
    get_async_session, CopyTradingConfig, Follower, Trade, APIKeyStore, 
    OrderSide, OrderType, OrderStatus
)
from shared.services import RedisService
from modules.trading import key_storage
from modules.trading.exchanges.universal_connector import create_connector

logger = logging.getLogger("obscura.copy_trading")


class CopyTradingEngine:
    """
    Executes copy trades based on signals from TradeMonitor.
    """
    
    def __init__(self):
        self.redis = RedisService()
        self._running = False
        self._task: Optional[asyncio.Task] = None
        logger.info("CopyTradingEngine initialized with DB/Redis backend")

    async def start(self):
        """Start the copy trading engine"""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._event_listener())
        logger.info("Copy trading engine started")

    async def stop(self):
        """Stop the engine"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Copy trading engine stopped")

    async def _event_listener(self):
        """Listen for trade events from Redis"""
        pubsub = self.redis.redis.pubsub()
        await pubsub.psubscribe("trade_events:*")
        
        logger.info("Subscribed to trade_events:*")
        
        while self._running:
            try:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message:
                    channel = message['channel'].decode()
                    data = json.loads(message['data'])
                    
                    # Extract trader_id from channel or data
                    trader_id = data.get('trader_id')
                    
                    if trader_id:
                        # Process event in background to not block listener
                        asyncio.create_task(self._process_trade_event(trader_id, data))
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in event listener: {e}")
                await asyncio.sleep(1)

    async def _process_trade_event(self, trader_id: str, event_data: Dict[str, Any]):
        """Process a single trade event"""
        event_type = event_data.get('event_type')
        
        # We only copy filled orders or position opens
        if event_type not in ['order_filled', 'position_opened', 'position_updated']:
            return

        logger.info(f"Processing event {event_type} from {trader_id}")

        async with get_async_session() as session:
            # Find active followers
            stmt = select(Follower).where(
                Follower.trader_id == trader_id,
                Follower.is_copying == True,
                Follower.is_active == True
            )
            result = await session.execute(stmt)
            followers = result.scalars().all()
            
            if not followers:
                return

            for follower in followers:
                try:
                    # Get copy config
                    stmt_config = select(CopyTradingConfig).where(
                        CopyTradingConfig.follower_rel_id == follower.id,
                        CopyTradingConfig.is_active == True,
                        CopyTradingConfig.is_paused == False
                    )
                    res_config = await session.execute(stmt_config)
                    config = res_config.scalar_one_or_none()
                    
                    if not config:
                        continue
                        
                    await self._execute_copy_trade(session, follower, config, event_data)
                    
                except Exception as e:
                    logger.error(f"Error processing follower {follower.follower_id}: {e}")

    async def _execute_copy_trade(
        self, 
        session: AsyncSession,
        follower: Follower, 
        config: CopyTradingConfig, 
        event_data: Dict[str, Any]
    ):
        """Execute the copy trade for a specific follower"""
        
        # 1. Calculate size
        amount = self._calculate_copy_amount(config, event_data)
        if amount <= 0:
            logger.info(f"Skipping copy for {follower.follower_id}: calculated amount 0")
            return

        # 2. Get credentials
        # We need to find the follower's credentials for the SAME exchange as the trader
        # Or a mapped exchange if we support cross-exchange copy (advanced)
        # For now, assume same exchange
        exchange = event_data.get('exchange')
        
        stmt_creds = select(APIKeyStore).where(
            APIKeyStore.user_id == follower.follower_id,
            APIKeyStore.exchange == exchange,
            APIKeyStore.is_active == True,
            APIKeyStore.can_trade == True
        )
        res_creds = await session.execute(stmt_creds)
        creds_store = res_creds.scalars().first()
        
        if not creds_store:
            logger.warning(f"No credentials for {follower.follower_id} on {exchange}")
            return

        # 3. Get actual secrets
        creds = await key_storage.get_credentials_for_trading(
            str(creds_store.id),
            str(follower.follower_id)
        )
        
        if not creds:
            return

        # 4. Execute trade
        try:
            connector = await create_connector(exchange, creds)
            
            symbol = event_data.get('symbol')
            side = event_data.get('side')
            order_type = 'market' # Usually copy trades are market orders to ensure fill
            
            # Execute
            order = await connector.create_order(
                symbol=symbol,
                side=side,
                order_type=order_type,
                amount=amount
            )
            
            # 5. Record execution
            trade_record = Trade(
                user_id=follower.follower_id,
                exchange=exchange,
                exchange_type=creds_store.exchange_type,
                exchange_order_id=str(order['id']),
                symbol=symbol,
                side=side,
                order_type=order_type,
                status=OrderStatus.FILLED, # Assuming immediate fill for market
                amount=amount,
                filled_amount=float(order.get('filled', 0)),
                price=float(order.get('average', 0) or order.get('price', 0)),
                average_fill_price=float(order.get('average', 0)),
                is_copy_trade=True,
                # source_trade_id would link to the trader's trade if we had it in DB
                created_at=datetime.utcnow(),
                executed_at=datetime.utcnow()
            )
            session.add(trade_record)
            
            # Update config stats
            config.total_copied_trades += 1
            # PnL update would happen later when position closes
            
            await session.commit()
            
            logger.info(f"Executed copy trade for {follower.follower_id}: {side} {amount} {symbol}")
            
            await connector.exchange.close()
            
        except Exception as e:
            logger.error(f"Failed to execute copy trade: {e}")

    def _calculate_copy_amount(self, config: CopyTradingConfig, event_data: Dict[str, Any]) -> float:
        """Calculate the amount to trade based on config"""
        try:
            trader_amount = float(event_data.get('quantity', 0))
            trader_price = float(event_data.get('price', 0))
            trader_value = trader_amount * trader_price if trader_price else 0
            
            amount = 0.0
            
            if config.copy_mode == 'fixed_amount':
                # Fixed USD amount per trade
                fixed_usd = float(config.fixed_amount_usd or 0)
                if trader_price > 0:
                    amount = fixed_usd / trader_price
                    
            elif config.copy_mode == 'proportional':
                # Proportional to trader's size (e.g. 10% of trader's size)
                # This requires knowing trader's total equity which we might not have easily
                # Simplified: just use the percentage of the trade quantity
                percent = float(config.proportion_percent or 100) / 100.0
                amount = trader_amount * percent
                
            elif config.copy_mode == 'smart_scale':
                # Scale based on follower's equity vs trader's equity
                # Placeholder for advanced logic
                amount = trader_amount # Fallback
            
            # Apply limits
            if config.min_trade_size_usd:
                min_size = float(config.min_trade_size_usd)
                if amount * trader_price < min_size:
                    return 0
            
            if config.max_trade_size_usd:
                max_size = float(config.max_trade_size_usd)
                if amount * trader_price > max_size:
                    amount = max_size / trader_price
            
            return amount
            
        except Exception as e:
            logger.error(f"Error calculating copy amount: {e}")
            return 0.0


# Singleton instance
copy_engine = CopyTradingEngine()
