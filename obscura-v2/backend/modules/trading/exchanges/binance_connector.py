"""
Binance Exchange Connector
Supports Binance Spot trading via CCXT library
"""

import os
from typing import List, Optional
from decimal import Decimal
from datetime import datetime
import hashlib
import hmac
import time

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


class BinanceConnector(ExchangeConnector):
    """Binance exchange integration using CCXT"""
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        super().__init__(api_key, api_secret)
        self.name = "Binance"
        self.exchange_type = ExchangeType.CEX
        self.client = None
        self._initialized = False
        
        # Use provided keys or environment variables
        self.api_key = api_key or os.getenv("BINANCE_API_KEY")
        self.api_secret = api_secret or os.getenv("BINANCE_API_SECRET")
        self.testnet = os.getenv("BINANCE_TESTNET", "false").lower() == "true"
        
        # Demo trading mode (recommended for 2025+, uses demo-api.binance.com)
        # Set BINANCE_USE_DEMO=true to use demo trading instead of old testnet
        self.use_demo = os.getenv("BINANCE_USE_DEMO", "true").lower() == "true"
    
    async def initialize(self) -> bool:
        """Initialize Binance client"""
        if not _HAVE_CCXT:
            print("Warning: CCXT not installed. Install with: pip install ccxt")
            return False
        
        try:
            config = {
                'apiKey': self.api_key,
                'secret': self.api_secret,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot',
                }
            }
            
            self.client = ccxt.binance(config)
            
            # Apply testnet/demo configuration
            if self.testnet:
                if self.use_demo:
                    # Use demo trading (demo-api.binance.com) - recommended for 2025+
                    self.client.enable_demo_trading(True)
                    print("Using Binance Demo Trading (demo-api.binance.com)")
                else:
                    # Use old sandbox/testnet (testnet.binance.vision) - deprecated
                    self.client.set_sandbox_mode(True)
                    print("Using Binance Testnet (testnet.binance.vision)")
            
            # Test connection
            await self.client.load_markets()
            self._initialized = True
            print(f"Binance connector initialized (testnet={self.testnet}, demo={self.use_demo})")
            return True
            
        except Exception as e:
            print(f"Failed to initialize Binance: {e}")
            return False
    
    async def place_order(self, order: TradeOrder) -> OrderResult:
        """Place order on Binance"""
        if not self._initialized:
            await self.initialize()
        
        if not self.client:
            raise RuntimeError("Binance client not initialized")
        
        try:
            # Convert order type
            order_type = order.order_type.value
            side = order.side.value
            
            # Prepare params
            params = {}
            if order.order_type == OrderType.STOP_LOSS and order.stop_price:
                params['stopPrice'] = float(order.stop_price)
            
            # Place order
            if order.order_type == OrderType.MARKET:
                result = await self.client.create_market_order(
                    symbol=order.symbol,
                    side=side,
                    amount=float(order.amount),
                    params=params
                )
            else:
                if not order.price:
                    raise ValueError("Limit orders require price")
                result = await self.client.create_limit_order(
                    symbol=order.symbol,
                    side=side,
                    amount=float(order.amount),
                    price=float(order.price),
                    params=params
                )
            
            # Parse response
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
            raise RuntimeError(f"Binance order failed: {e}")
    
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel order on Binance"""
        if not self.client:
            return False
        
        try:
            await self.client.cancel_order(order_id, symbol)
            return True
        except Exception as e:
            print(f"Failed to cancel Binance order: {e}")
            return False
    
    async def get_order_status(self, order_id: str, symbol: str) -> OrderResult:
        """Get order status from Binance"""
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
            raise RuntimeError(f"Failed to get Binance order status: {e}")
    
    async def get_balance(self, asset: Optional[str] = None) -> List[Balance]:
        """Get Binance account balance"""
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
            
            # Return all non-zero balances
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
            raise RuntimeError(f"Failed to get Binance balance: {e}")
    
    async def get_market_data(self, symbol: str) -> MarketData:
        """Get market data from Binance"""
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
            raise RuntimeError(f"Failed to get Binance market data: {e}")
    
    async def get_supported_pairs(self) -> List[str]:
        """Get supported trading pairs on Binance"""
        if not self.client:
            await self.initialize()
        
        try:
            markets = await self.client.load_markets()
            return list(markets.keys())
        except Exception as e:
            print(f"Failed to get Binance pairs: {e}")
            return []
    
    def format_symbol(self, base: str, quote: str) -> str:
        """Format symbol for Binance (e.g., BTC/USDT)"""
        return f"{base}/{quote}"

    async def fetch_my_trades(
        self, 
        symbol: Optional[str] = None, 
        since: Optional[int] = None,
        limit: int = 100
    ) -> List[dict]:
        """
        Fetch user's trade history from Binance.
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT'). If None, fetches for common pairs.
            since: Unix timestamp in milliseconds to fetch trades from
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
                # Fetch trades for specific symbol
                trades = await self.client.fetch_my_trades(symbol, since=since, limit=limit)
                all_trades.extend(trades)
            else:
                # Get balance to determine which pairs to check
                balance = await self.client.fetch_balance()
                assets = [k for k, v in balance['total'].items() if v > 0 and k != 'USDT']
                
                # Fetch trades for each asset paired with USDT
                for asset in assets[:10]:  # Limit to 10 assets
                    pair = f"{asset}/USDT"
                    try:
                        trades = await self.client.fetch_my_trades(pair, since=since, limit=limit)
                        all_trades.extend(trades)
                    except Exception:
                        # Pair might not exist, skip
                        pass
            
            # Sort by timestamp
            all_trades.sort(key=lambda x: x.get('timestamp', 0))
            return all_trades
            
        except Exception as e:
            raise RuntimeError(f"Failed to fetch trades from Binance: {e}")

    async def fetch_closed_orders(
        self,
        symbol: Optional[str] = None,
        since: Optional[int] = None,
        limit: int = 100
    ) -> List[dict]:
        """
        Fetch user's closed/filled orders from Binance.
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            since: Unix timestamp in milliseconds
            limit: Maximum number of orders
            
        Returns:
            List of order dictionaries
        """
        if not self.client:
            await self.initialize()
        
        if not self.client:
            raise RuntimeError("Client not initialized")
        
        try:
            if symbol:
                return await self.client.fetch_closed_orders(symbol, since=since, limit=limit)
            else:
                # Fetch for common trading pairs
                all_orders = []
                common_pairs = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT']
                
                for pair in common_pairs:
                    try:
                        orders = await self.client.fetch_closed_orders(pair, since=since, limit=limit)
                        all_orders.extend(orders)
                    except Exception:
                        pass
                
                return all_orders
                
        except Exception as e:
            raise RuntimeError(f"Failed to fetch orders from Binance: {e}")
