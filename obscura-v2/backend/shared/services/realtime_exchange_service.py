"""
Real-Time Exchange Service (CCXT Pro)

Handles real-time websocket connections to exchanges for immediate trade copying.
"""

import asyncio
import logging
import json
import ccxt.pro as ccxtpro
from typing import Dict, List, Callable, Awaitable
from datetime import datetime

from shared.services import redis_service
from shared.database.connection import get_async_session
from shared.database.repositories import TradeRepository, UserRepository
from shared.database.models import OrderStatus, OrderSide, OrderType

logger = logging.getLogger("obscura.realtime")

class RealTimeExchangeService:
    def __init__(self):
        self.exchanges: Dict[str, ccxtpro.Exchange] = {}
        self.callbacks: Dict[str, List[Callable[[dict], Awaitable[None]]]] = {}
        self.redis_channel_copy_trade = "queue:copy_trade"
        self.redis_channel_proof_gen = "queue:proof_generation"

    async def start_watching(self, exchange_id: str, api_key: str, secret: str, password: str = None, user_id: str = None):
        """
        Starts a websocket connection for a specific exchange account.
        """
        if exchange_id not in self.exchanges:
            exchange_class = getattr(ccxtpro, exchange_id)
            config = {
                'apiKey': api_key,
                'secret': secret,
                'enableRateLimit': True,
            }
            if password:
                config['password'] = password
                
            self.exchanges[exchange_id] = exchange_class(config)
            
        # Start the watch loop in the background
        asyncio.create_task(self._watch_loop(exchange_id, user_id))

    async def _watch_loop(self, exchange_id: str, user_id: str = None):
        exchange = self.exchanges[exchange_id]
        logger.info(f"Started watching {exchange_id} for user {user_id}...")
        
        while True:
            try:
                # Watch for new trades (executions)
                if exchange.has['watchMyTrades']:
                    trades = await exchange.watch_my_trades()
                    for trade in trades:
                        await self._handle_trade(exchange_id, trade, user_id)
                
                # Watch for order updates (status changes)
                if exchange.has['watchOrders']:
                    orders = await exchange.watch_orders()
                    for order in orders:
                        await self._handle_order_update(exchange_id, order, user_id)

                # If neither is supported, fallback to polling (simulated delay)
                if not exchange.has['watchMyTrades'] and not exchange.has['watchOrders']:
                    logger.warning(f"{exchange_id} does not support WS private channels. Falling back to REST polling.")
                    await self._poll_rest_fallback(exchange_id, user_id)
                    
            except Exception as e:
                logger.error(f"Error watching {exchange_id}: {e}")
                await asyncio.sleep(5) # Backoff

    async def _poll_rest_fallback(self, exchange_id: str, user_id: str = None):
        """
        Fallback for exchanges that don't support Websockets.
        Polls REST API every 5 seconds.
        """
        exchange = self.exchanges[exchange_id]
        try:
            # Fetch open orders and recent trades
            if exchange.has['fetchOpenOrders']:
                orders = await exchange.fetch_open_orders()
                # Process orders...
            
            if exchange.has['fetchMyTrades']:
                trades = await exchange.fetch_my_trades()
                for trade in trades:
                    # We need a way to deduplicate trades here in a real implementation
                    # For now, we assume the loop handles new trades only or we check DB
                    await self._handle_trade(exchange_id, trade, user_id)
                
        except Exception as e:
            logger.error(f"Polling error for {exchange_id}: {e}")
        
        await asyncio.sleep(5)

    async def _handle_trade(self, exchange_id: str, trade: dict, user_id: str = None):
        """
        Process a detected trade:
        1. Store in DB
        2. Publish to Copy Trading Queue
        3. If closing trade, calculate PnL and Publish to Proof Queue
        """
        logger.info(f"New Trade on {exchange_id}: {trade['symbol']} {trade['side']} {trade['amount']}")
        
        if not user_id:
            logger.warning("Trade detected but no user_id associated. Skipping storage/queue.")
            return

        async with get_async_session() as session:
            trade_repo = TradeRepository(session)
            
            # 1. Store Trade in Database
            # Map CCXT trade object to our DB model
            db_trade = await trade_repo.create(
                user_id=user_id,
                exchange=exchange_id,
                symbol=trade['symbol'],
                side=OrderSide(trade['side']),
                order_type=OrderType(trade['type'] or 'market'),
                amount=trade['amount'],
                price=trade['price'],
                filled_amount=trade['amount'], # Assuming full fill for 'trade' event
                average_fill_price=trade['price'],
                fees_usd=trade['fee']['cost'] if trade.get('fee') else 0,
                status=OrderStatus.FILLED,
                executed_at=datetime.fromtimestamp(trade['timestamp'] / 1000),
                external_id=trade['id']
            )
            await trade_repo.commit()
            logger.info(f"Stored trade {db_trade.id} for user {user_id}")

            # 2. Publish to Copy Trading Queue
            # Followers need to execute this immediately
            copy_payload = {
                "leader_id": user_id,
                "trade_id": str(db_trade.id),
                "exchange": exchange_id,
                "symbol": trade['symbol'],
                "side": trade['side'],
                "amount": trade['amount'],
                "price": trade['price'],
                "timestamp": trade['timestamp']
            }
            await redis_service.publish(self.redis_channel_copy_trade, json.dumps(copy_payload))
            logger.info(f"Published to {self.redis_channel_copy_trade}")

            # 3. Check for PnL / Proof Generation
            # Simplified logic: If side is SELL (for long) or BUY (for short), we trigger PnL calc
            # In a real system, we'd check the Position state.
            if trade['side'] == 'sell': # Assuming Long-only for simplicity or closing a position
                # Calculate PnL (Mock logic or call a service)
                # For now, we push to the Proof Queue to let the Verification Service handle the math
                proof_payload = {
                    "trader_id": user_id,
                    "trade_id": str(db_trade.id),
                    "symbol": trade['symbol'],
                    "action": "close_position",
                    "timestamp": trade['timestamp']
                }
                await redis_service.publish(self.redis_channel_proof_gen, json.dumps(proof_payload))
                logger.info(f"Published to {self.redis_channel_proof_gen} for ZK Proof")

    async def _handle_order_update(self, exchange_id: str, order: dict, user_id: str = None):
        """
        Handle order status updates (e.g. filled, canceled)
        """
        logger.info(f"Order Update on {exchange_id}: {order['id']} status={order['status']}")
        
        if order['status'] == 'canceled' and user_id:
             # If a leader cancels an order, we might want to propagate that cancellation
             cancel_payload = {
                 "leader_id": user_id,
                 "original_order_id": order['id'],
                 "action": "cancel",
                 "symbol": order['symbol']
             }
             await redis_service.publish(self.redis_channel_copy_trade, json.dumps(cancel_payload))
             logger.info(f"Published Cancellation to {self.redis_channel_copy_trade}")

    async def close_all(self):
        for name, exchange in self.exchanges.items():
            await exchange.close()

realtime_service = RealTimeExchangeService()
