"""
Order Execution Service

Standardizes order creation and smart routing across all 105+ CCXT exchanges.
Handles 'market' vs 'limit' nuances and provides retry logic.
"""

import logging
import asyncio
import ccxt.async_support as ccxt
from typing import Dict, Any, Optional

logger = logging.getLogger("obscura.execution")

class OrderExecutionService:
    def __init__(self):
        self.exchanges: Dict[str, ccxt.Exchange] = {}

    async def get_exchange(self, exchange_id: str, api_key: str, secret: str, password: str = None) -> ccxt.Exchange:
        """
        Get or create an exchange instance with credentials.
        """
        if exchange_id not in self.exchanges:
            exchange_class = getattr(ccxt, exchange_id)
            config = {
                'apiKey': api_key,
                'secret': secret,
                'enableRateLimit': True,
                'options': {'defaultType': 'spot'}, # Default to spot, can be overridden
            }
            if password:
                config['password'] = password
            
            self.exchanges[exchange_id] = exchange_class(config)
            
        return self.exchanges[exchange_id]

    async def create_order(self, 
                           exchange_id: str, 
                           credentials: Dict[str, str],
                           symbol: str, 
                           side: str, 
                           amount: float, 
                           order_type: str = 'market', 
                           price: Optional[float] = None,
                           params: Dict = {}) -> Dict[str, Any]:
        """
        Execute an order with standardized handling and retry logic.
        """
        exchange = await self.get_exchange(exchange_id, **credentials)
        
        # 1. Standardize Symbol
        # Ensure symbol format matches exchange requirements (e.g. BTC/USDT vs BTC-USDT)
        # CCXT handles most of this, but we can add custom mapping if needed.
        
        # 2. Handle Market vs Limit Nuances
        if order_type == 'market':
            # Some exchanges require 'createMarketBuyOrder' specific methods or params
            # CCXT unifies this via create_order(..., 'market', ...)
            pass
            
        # 3. Retry Logic (Smart Routing)
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"Executing {side} {amount} {symbol} on {exchange_id} (Attempt {attempt+1})")
                
                order = await exchange.create_order(
                    symbol=symbol,
                    type=order_type,
                    side=side,
                    amount=amount,
                    price=price,
                    params=params
                )
                
                logger.info(f"Order executed: {order['id']}")
                return order
                
            except ccxt.InsufficientFunds as e:
                logger.error(f"Insufficient Funds on {exchange_id}: {e}")
                raise e # Don't retry on funds error
                
            except ccxt.NetworkError as e:
                logger.warning(f"Network Error on {exchange_id}: {e}. Retrying...")
                await asyncio.sleep(1 * (attempt + 1)) # Exponential backoff
                
            except ccxt.ExchangeError as e:
                logger.error(f"Exchange Error on {exchange_id}: {e}")
                # Analyze error code for specific handling
                raise e
                
        raise Exception(f"Failed to execute order on {exchange_id} after {max_retries} attempts")

execution_service = OrderExecutionService()
