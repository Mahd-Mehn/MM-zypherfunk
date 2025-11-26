"""
Copy Trading Worker

Listens to the 'queue:copy_trade' Redis channel and executes trades for followers.
"""

import asyncio
import json
import logging
from typing import Dict, Any

from shared.services import redis_service
from shared.services.order_execution_service import execution_service
from shared.database.connection import get_async_session
from shared.database.repositories import SubscriptionRepository, ExchangeConnectionRepository

logger = logging.getLogger("obscura.worker.copy_trade")

class CopyTradingWorker:
    def __init__(self):
        self.channel_name = "queue:copy_trade"
        self.is_running = False

    async def start(self):
        self.is_running = True
        logger.info(f"Starting Copy Trading Worker on {self.channel_name}...")
        
        pubsub = redis_service.redis.pubsub()
        await pubsub.subscribe(self.channel_name)

        try:
            async for message in pubsub.listen():
                if not self.is_running:
                    break
                    
                if message['type'] == 'message':
                    await self._process_message(message['data'])
        except Exception as e:
            logger.error(f"Worker error: {e}")
        finally:
            await pubsub.unsubscribe(self.channel_name)

    async def stop(self):
        self.is_running = False
        logger.info("Stopping Copy Trading Worker...")

    async def _process_message(self, raw_data: bytes):
        try:
            payload = json.loads(raw_data)
            logger.info(f"Received copy payload: {payload}")
            
            leader_id = payload.get("leader_id")
            action = payload.get("action", "trade") # 'trade' or 'cancel'
            
            async with get_async_session() as session:
                sub_repo = SubscriptionRepository(session)
                conn_repo = ExchangeConnectionRepository(session)
                
                # 1. Get all active followers for this leader
                followers = await sub_repo.get_active_followers(leader_id)
                logger.info(f"Found {len(followers)} followers for leader {leader_id}")
                
                # 2. Execute for each follower (Parallel execution)
                tasks = []
                for follower in followers:
                    # Get follower's exchange connections
                    connections = await conn_repo.get_user_connections(str(follower.follower_id))
                    if not connections:
                        logger.warning(f"No exchange connection for follower {follower.follower_id}")
                        continue
                        
                    # Select the correct exchange connection
                    # We must match the leader's exchange to ensure symbol compatibility
                    leader_exchange = payload.get("exchange")
                    target_conn = None
                    
                    if leader_exchange:
                        for c in connections:
                            if c.exchange.lower() == leader_exchange.lower():
                                target_conn = c
                                break
                    
                    if not target_conn:
                        # Fallback: If user only has ONE connection, maybe we can try it?
                        # But strictly speaking, cross-exchange copy trading is dangerous without symbol mapping.
                        # For a "real app", we should be strict or have a specific "cross-exchange" flag.
                        # We will be strict here to prevent failed orders due to symbol mismatch.
                        logger.warning(f"Follower {follower.follower_id} has no active connection for {leader_exchange}. Skipping.")
                        continue
                        
                    conn = target_conn
                    
                    # Decrypt credentials (Mock - in prod use Citadel/Nillion)
                    api_key = "mock_key" # conn.api_key (decrypted)
                    secret = "mock_secret" # conn.api_secret (decrypted)
                    passphrase = None # conn.passphrase
                    
                    if action == "trade":
                        tasks.append(self._execute_copy_trade(
                            conn.exchange, 
                            {"api_key": api_key, "secret": secret, "password": passphrase},
                            payload,
                            follower.config # Copy settings (e.g. fixed amount vs percentage)
                        ))
                    elif action == "cancel":
                        tasks.append(self._execute_cancel(
                            conn.exchange,
                            {"api_key": api_key, "secret": secret, "password": passphrase},
                            payload
                        ))
                
                if tasks:
                    await asyncio.gather(*tasks)
                    
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    async def _execute_copy_trade(self, exchange_id: str, creds: Dict, payload: Dict, config: Any):
        """
        Execute the trade for a single follower.
        """
        try:
            # Calculate amount based on follower config
            # e.g. Fixed Amount or Proportional
            amount = float(payload['amount']) # Default to mirroring exact amount for now
            
            logger.info(f"Executing copy for follower on {exchange_id}")
            await execution_service.create_order(
                exchange_id=exchange_id,
                credentials=creds,
                symbol=payload['symbol'],
                side=payload['side'],
                amount=amount,
                order_type='market' # Always market for copy trading to ensure fill
            )
        except Exception as e:
            logger.error(f"Failed to copy trade: {e}")

    async def _execute_cancel(self, exchange_id: str, creds: Dict, payload: Dict):
        """
        Cancel an order for a follower.
        """
        # Logic to find the corresponding follower order ID would be needed here
        # For now, we just log it
        logger.info(f"Would cancel order derived from {payload['original_order_id']} on {exchange_id}")

if __name__ == "__main__":
    # Standalone runner
    logging.basicConfig(level=logging.INFO)
    worker = CopyTradingWorker()
    asyncio.run(worker.start())
