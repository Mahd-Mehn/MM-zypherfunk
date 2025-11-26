"""
Coinbase Exchange Connector
Supports Coinbase Advanced Trade API
"""

import os
from typing import List, Optional
from decimal import Decimal
from datetime import datetime
import json

try:
    import ccxt
    _HAVE_CCXT = True
except ImportError:
    ccxt = None  # type: ignore
    _HAVE_CCXT = False

from .base import (
    ExchangeConnector, TradeOrder, OrderResult, Balance,
    MarketData, OrderType, OrderSide, ExchangeType
)


class CoinbaseConnector(ExchangeConnector):
    """Coinbase exchange integration"""
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        super().__init__(api_key, api_secret)
        self.name = "Coinbase"
        self.exchange_type = ExchangeType.CEX
        self.client = None
        self._initialized = False
        
        self.api_key = api_key or os.getenv("COINBASE_API_KEY")
        self.api_secret = api_secret or os.getenv("COINBASE_API_SECRET")
        self.sandbox = os.getenv("COINBASE_SANDBOX", "false").lower() == "true"
    
    async def initialize(self) -> bool:
        """Initialize Coinbase client"""
        if not _HAVE_CCXT:
            print("Warning: CCXT not installed. Install with: pip install ccxt")
            return False
        
        try:
            self.client = ccxt.coinbase({
                'apiKey': self.api_key,
                'secret': self.api_secret,
                'enableRateLimit': True,
            })
            
            if self.sandbox:
                self.client.set_sandbox_mode(True)
            
            await self.client.load_markets()
            self._initialized = True
            print(f"Coinbase connector initialized (sandbox={self.sandbox})")
            return True
            
        except Exception as e:
            print(f"Failed to initialize Coinbase: {e}")
            return False
    
    async def place_order(self, order: TradeOrder) -> OrderResult:
        """Place order on Coinbase"""
        if not self._initialized:
            await self.initialize()
        
        if not self.client:
            raise RuntimeError("Coinbase client not initialized")
        
        try:
            side = order.side.value
            
            if order.order_type == OrderType.MARKET:
                result = await self.client.create_market_order(
                    symbol=order.symbol,
                    side=side,
                    amount=float(order.amount)
                )
            else:
                if not order.price:
                    raise ValueError("Limit orders require price")
                result = await self.client.create_limit_order(
                    symbol=order.symbol,
                    side=side,
                    amount=float(order.amount),
                    price=float(order.price)
                )
            
            return OrderResult(
                order_id=str(result['id']),
                exchange=self.name,
                exchange_type=self.exchange_type,
                symbol=order.symbol,
                side=order.side,
                amount=Decimal(str(result.get('amount', 0))),
                filled_amount=Decimal(str(result.get('filled', 0))),
                average_price=Decimal(str(result.get('average', 0) or result.get('price', 0))),
                status=result.get('status', 'unknown'),
                timestamp=datetime.fromtimestamp(result['timestamp'] / 1000),
                fees={'trading_fee': Decimal(str(result.get('fee', {}).get('cost', 0)))},
                metadata={'raw_response': result}
            )
            
        except Exception as e:
            raise RuntimeError(f"Coinbase order failed: {e}")
    
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel order on Coinbase"""
        if not self.client:
            return False
        
        try:
            await self.client.cancel_order(order_id, symbol)
            return True
        except Exception as e:
            print(f"Failed to cancel Coinbase order: {e}")
            return False
    
    async def get_order_status(self, order_id: str, symbol: str) -> OrderResult:
        """Get order status from Coinbase"""
        if not self.client:
            raise RuntimeError("Client not initialized")
        
        try:
            result = await self.client.fetch_order(order_id, symbol)
            
            return OrderResult(
                order_id=str(result['id']),
                exchange=self.name,
                exchange_type=self.exchange_type,
                symbol=symbol,
                side=OrderSide(result['side']),
                amount=Decimal(str(result.get('amount', 0))),
                filled_amount=Decimal(str(result.get('filled', 0))),
                average_price=Decimal(str(result.get('average', 0) or result.get('price', 0))),
                status=result.get('status', 'unknown'),
                timestamp=datetime.fromtimestamp(result['timestamp'] / 1000),
                metadata={'raw_response': result}
            )
        except Exception as e:
            raise RuntimeError(f"Failed to get Coinbase order status: {e}")
    
    async def get_balance(self, asset: Optional[str] = None) -> List[Balance]:
        """Get Coinbase account balance"""
        if not self.client:
            raise RuntimeError("Client not initialized")
        
        try:
            balance_data = await self.client.fetch_balance()
            
            if asset:
                if asset in balance_data:
                    b = balance_data[asset]
                    return [Balance(
                        asset=asset,
                        free=Decimal(str(b.get('free', 0))),
                        locked=Decimal(str(b.get('used', 0))),
                        total=Decimal(str(b.get('total', 0)))
                    )]
                return []
            
            balances = []
            for asset_name, b in balance_data.items():
                if b.get('total', 0) > 0:
                    balances.append(Balance(
                        asset=asset_name,
                        free=Decimal(str(b.get('free', 0))),
                        locked=Decimal(str(b.get('used', 0))),
                        total=Decimal(str(b.get('total', 0)))
                    ))
            
            return balances
            
        except Exception as e:
            raise RuntimeError(f"Failed to get Coinbase balance: {e}")
    
    async def get_market_data(self, symbol: str) -> MarketData:
        """Get market data from Coinbase"""
        if not self.client:
            raise RuntimeError("Client not initialized")
        
        try:
            ticker = await self.client.fetch_ticker(symbol)
            
            return MarketData(
                symbol=symbol,
                bid=Decimal(str(ticker.get('bid', 0))),
                ask=Decimal(str(ticker.get('ask', 0))),
                last=Decimal(str(ticker.get('last', 0))),
                volume_24h=Decimal(str(ticker.get('quoteVolume', 0))),
                timestamp=datetime.fromtimestamp(ticker['timestamp'] / 1000)
            )
        except Exception as e:
            raise RuntimeError(f"Failed to get Coinbase market data: {e}")
    
    async def get_supported_pairs(self) -> List[str]:
        """Get supported trading pairs on Coinbase"""
        if not self.client:
            await self.initialize()
        
        try:
            markets = await self.client.load_markets()
            return list(markets.keys())
        except Exception as e:
            print(f"Failed to get Coinbase pairs: {e}")
            return []
    
    async def fetch_my_trades(
        self, 
        symbol: Optional[str] = None, 
        since: Optional[int] = None,
        limit: int = 100
    ) -> List[dict]:
        """
        Fetch user's trade history from Coinbase.
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USD')
            since: Unix timestamp in milliseconds
            limit: Maximum number of trades per symbol
            
        Returns:
            List of trade dictionaries in CCXT format
        """
        if not self.client:
            await self.initialize()
        
        if not self.client:
            raise RuntimeError("Client not initialized")
        
        all_trades = []
        
        try:
            if symbol:
                trades = await self.client.fetch_my_trades(symbol, since=since, limit=limit)
                all_trades.extend(trades)
            else:
                # Get balance to determine which pairs to check
                balance = await self.client.fetch_balance()
                assets = [k for k, v in balance['total'].items() if v > 0 and k not in ['USD', 'USDC']]
                
                for asset in assets[:10]:
                    for quote in ['USD', 'USDC', 'USDT']:
                        pair = f"{asset}/{quote}"
                        try:
                            trades = await self.client.fetch_my_trades(pair, since=since, limit=limit)
                            all_trades.extend(trades)
                            break
                        except Exception:
                            pass
            
            all_trades.sort(key=lambda x: x.get('timestamp', 0))
            return all_trades
            
        except Exception as e:
            raise RuntimeError(f"Failed to fetch trades from Coinbase: {e}")
    
    def format_symbol(self, base: str, quote: str) -> str:
        """Format symbol for Coinbase"""
        return f"{base}/{quote}"
