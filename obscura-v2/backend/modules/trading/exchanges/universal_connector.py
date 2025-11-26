"""
Universal CCXT Exchange Connector

Supports all 100+ exchanges available in CCXT including DEXes.
Provides unified interface for trading across any CCXT-supported platform.
"""

import ccxt.async_support as ccxt
import asyncio
import logging
from typing import Optional, Dict, Any, List
from decimal import Decimal
from datetime import datetime

from .base import (
    ExchangeConnector,
    TradeOrder,
    OrderResult,
    Balance,
    MarketData,
    OrderType,
    OrderSide,
    ExchangeType
)

logger = logging.getLogger("obscura.universal_connector")


# Comprehensive list of supported exchanges
SUPPORTED_CEX_EXCHANGES = [
    'binance', 'binanceus', 'binanceusdm', 'binancecoinm',
    'coinbase', 'coinbaseprime', 'coinbaseadvanced',
    'kraken', 'krakenfutures',
    'okx', 'okex',
    'bybit', 'bybitfutures',
    'huobi', 'huobipro', 'huobijp',
    'kucoin', 'kucoinfutures',
    'bitfinex', 'bitfinex2',
    'bitstamp',
    'gemini',
    'bittrex',
    'poloniex',
    'crypto.com', 'cryptocom',
    'gate', 'gateio',
    'mexc', 'mexc3',
    'bitget',
    'bitmex',
    'deribit',
    'phemex',
    'woo', 'woofi', 'woofipro',
    'bitmart',
    'ascendex',
    'lbank',
    'bitrue',
    'bingx',
    'pionex',
    'xt',
    'coinex',
    'btcturk',
    'cex',
    'exmo',
    'independentreserve',
    'whitebit'
]

SUPPORTED_DEX_EXCHANGES = [
    'pancakeswap',
    'sushiswap', 
    'uniswap',
    'uniswapv3',
    'quickswap',
    'spookyswap',
    'spiritswap',
    'traderjoe',
    'raydium',
    'orca',
    'serum',
    'jupiter',
    '1inch',
    '0x',
    'paraswap',
    'kyberswap',
    'balancer',
    'curve',
    'velodrome',
    'aerodrome',
    'camelot',
    'gmx',
    'dydx',
    'vertex'
]


class UniversalConnector(ExchangeConnector):
    """
    Universal connector supporting all CCXT exchanges (CEX and DEX).
    
    Automatically detects exchange type and capabilities.
    Handles exchange-specific quirks and rate limits.
    """
    
    def __init__(self, exchange_id: str, config: Dict[str, Any]):
        """
        Initialize universal connector for any CCXT exchange.
        
        Args:
            exchange_id: CCXT exchange identifier (e.g., 'binance', 'okx')
            config: Configuration dictionary with credentials and settings
        """
        self.exchange_id = exchange_id.lower()
        self.config = config
        self.exchange: Optional[Any] = None
        self.is_dex = exchange_id.lower() in SUPPORTED_DEX_EXCHANGES
        self._markets_loaded = False
        self._rate_limit_delay = 0.1  # Default 100ms between requests
        
        logger.info(f"Initializing UniversalConnector for {exchange_id}")

    async def initialize(self) -> bool:
        """Initialize connection to the exchange"""
        try:
            # Get CCXT exchange class dynamically
            if not hasattr(ccxt, self.exchange_id):
                logger.error(f"Exchange {self.exchange_id} not supported by CCXT")
                return False
            
            exchange_class = getattr(ccxt, self.exchange_id)
            
            # Build configuration
            ccxt_config = {
                'enableRateLimit': True,
                'rateLimit': self.config.get('rate_limit', 100),
            }
            
            # Add API credentials if provided
            if 'api_key' in self.config:
                ccxt_config['apiKey'] = self.config['api_key']
            if 'api_secret' in self.config:
                ccxt_config['secret'] = self.config['api_secret']
            if 'password' in self.config:
                ccxt_config['password'] = self.config['password']
            if 'uid' in self.config:
                ccxt_config['uid'] = self.config['uid']
                
            # Testnet support
            if self.config.get('testnet', False):
                ccxt_config['options'] = {'defaultType': 'test'}
                
            # Proxy support
            if 'proxy' in self.config:
                ccxt_config['proxies'] = self.config['proxy']
                
            # Create exchange instance
            self.exchange = exchange_class(ccxt_config)
            
            # Load markets
            await self.exchange.load_markets()
            self._markets_loaded = True
            
            # Get rate limit info
            if hasattr(self.exchange, 'rateLimit'):
                self._rate_limit_delay = self.exchange.rateLimit / 1000.0
            
            logger.info(
                f"✓ {self.exchange_id} initialized "
                f"({'DEX' if self.is_dex else 'CEX'}, "
                f"{len(self.exchange.markets)} markets)"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize {self.exchange_id}: {e}")
            return False

    async def place_order(self, order: TradeOrder) -> OrderResult:
        """Place an order on the exchange"""
        if not self.exchange:
            raise RuntimeError(f"{self.exchange_id} not initialized")
        
        try:
            # Validate symbol exists
            if order.symbol not in self.exchange.markets:
                raise ValueError(f"Symbol {order.symbol} not available on {self.exchange_id}")
            
            # Build order parameters
            side = 'buy' if order.side == OrderSide.BUY else 'sell'
            amount = float(order.amount)
            
            # Map order type to CCXT
            if order.order_type == OrderType.MARKET:
                ccxt_result = await self.exchange.create_market_order(
                    order.symbol,
                    side,
                    amount
                )
            elif order.order_type == OrderType.LIMIT:
                if not order.price:
                    raise ValueError("Limit order requires price")
                ccxt_result = await self.exchange.create_limit_order(
                    order.symbol,
                    side,
                    amount,
                    float(order.price)
                )
            elif order.order_type == OrderType.STOP_LOSS:
                if not order.stop_price:
                    raise ValueError("Stop loss order requires stop_price")
                ccxt_result = await self.exchange.create_order(
                    order.symbol,
                    'stop_loss',
                    side,
                    amount,
                    params={'stopPrice': float(order.stop_price)}
                )
            else:
                raise ValueError(f"Unsupported order type: {order.order_type}")
            
            # Parse result
            return OrderResult(
                order_id=ccxt_result['id'],
                exchange=self.exchange_id,
                exchange_type=ExchangeType.DEX if self.is_dex else ExchangeType.CEX,
                symbol=order.symbol,
                side=order.side,
                order_type=order.order_type,
                status=self._parse_status(ccxt_result['status']),
                filled_amount=Decimal(str(ccxt_result.get('filled', 0))),
                remaining_amount=Decimal(str(ccxt_result.get('remaining', amount))),
                average_price=Decimal(str(ccxt_result.get('average', 0))) if ccxt_result.get('average') else None,
                fees=self._parse_fees(ccxt_result),
                timestamp=datetime.fromtimestamp(ccxt_result['timestamp'] / 1000)
            )
            
        except Exception as e:
            logger.error(f"Order placement failed on {self.exchange_id}: {e}")
            raise

    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel an existing order"""
        if not self.exchange:
            return False
        
        try:
            await self.exchange.cancel_order(order_id, symbol)
            logger.info(f"Cancelled order {order_id} on {self.exchange_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel order on {self.exchange_id}: {e}")
            return False

    async def get_order_status(self, order_id: str, symbol: str) -> Optional[OrderResult]:
        """Get status of an order"""
        if not self.exchange:
            return None
        
        try:
            order = await self.exchange.fetch_order(order_id, symbol)
            
            return OrderResult(
                order_id=order['id'],
                exchange=self.exchange_id,
                exchange_type=ExchangeType.DEX if self.is_dex else ExchangeType.CEX,
                symbol=order['symbol'],
                side=OrderSide.BUY if order['side'] == 'buy' else OrderSide.SELL,
                order_type=self._parse_order_type(order['type']),
                status=self._parse_status(order['status']),
                filled_amount=Decimal(str(order.get('filled', 0))),
                remaining_amount=Decimal(str(order.get('remaining', 0))),
                average_price=Decimal(str(order.get('average', 0))) if order.get('average') else None,
                fees=self._parse_fees(order),
                timestamp=datetime.fromtimestamp(order['timestamp'] / 1000)
            )
        except Exception as e:
            logger.error(f"Failed to get order status on {self.exchange_id}: {e}")
            return None

    async def get_balance(self, asset: Optional[str] = None) -> List[Balance]:
        """Get account balance"""
        if not self.exchange:
            return []
        
        try:
            balance = await self.exchange.fetch_balance()
            
            if asset:
                # Return specific asset
                if asset in balance:
                    return [Balance(
                        asset=asset,
                        free=Decimal(str(balance[asset].get('free', 0))),
                        locked=Decimal(str(balance[asset].get('used', 0))),
                        total=Decimal(str(balance[asset].get('total', 0)))
                    )]
                return []
            
            # Return all assets with non-zero balance
            balances = []
            for currency, data in balance.items():
                if currency not in ['free', 'used', 'total', 'info']:
                    total = Decimal(str(data.get('total', 0)))
                    if total > 0:
                        balances.append(Balance(
                            asset=currency,
                            free=Decimal(str(data.get('free', 0))),
                            locked=Decimal(str(data.get('used', 0))),
                            total=total
                        ))
            
            return balances
            
        except Exception as e:
            logger.error(f"Failed to get balance on {self.exchange_id}: {e}")
            return []

    async def get_market_data(self, symbol: str) -> Optional[MarketData]:
        """Get market data for a symbol"""
        if not self.exchange:
            return None
        
        try:
            ticker = await self.exchange.fetch_ticker(symbol)
            
            return MarketData(
                symbol=symbol,
                exchange=self.exchange_id,
                bid=Decimal(str(ticker.get('bid', 0))) if ticker.get('bid') else None,
                ask=Decimal(str(ticker.get('ask', 0))) if ticker.get('ask') else None,
                last=Decimal(str(ticker.get('last', 0))) if ticker.get('last') else None,
                volume_24h=Decimal(str(ticker.get('quoteVolume', 0))) if ticker.get('quoteVolume') else None,
                timestamp=datetime.fromtimestamp(ticker['timestamp'] / 1000) if ticker.get('timestamp') else datetime.now()
            )
        except Exception as e:
            logger.error(f"Failed to get market data on {self.exchange_id}: {e}")
            return None

    async def get_trading_pairs(self) -> List[str]:
        """Get all available trading pairs"""
        if not self.exchange or not self._markets_loaded:
            return []
        
        return list(self.exchange.markets.keys())

    async def close(self):
        """Close exchange connection"""
        if self.exchange:
            await self.exchange.close()
            logger.info(f"Closed connection to {self.exchange_id}")

    def _parse_status(self, status: str) -> str:
        """Parse CCXT order status to our format"""
        status_map = {
            'open': 'open',
            'closed': 'filled',
            'canceled': 'canceled',
            'cancelled': 'canceled',
            'expired': 'expired',
            'rejected': 'rejected',
            'partially_filled': 'partially_filled'
        }
        return status_map.get(status.lower(), 'unknown')

    def _parse_order_type(self, order_type: str) -> OrderType:
        """Parse CCXT order type to our enum"""
        type_map = {
            'market': OrderType.MARKET,
            'limit': OrderType.LIMIT,
            'stop': OrderType.STOP_LOSS,
            'stop_loss': OrderType.STOP_LOSS,
            'stop_market': OrderType.STOP_LOSS
        }
        return type_map.get(order_type.lower(), OrderType.MARKET)

    def _parse_fees(self, order: Dict[str, Any]) -> Dict[str, Decimal]:
        """Parse fee information from order"""
        fees = {}
        if 'fee' in order and order['fee']:
            fee_info = order['fee']
            if 'cost' in fee_info:
                fees['trading_fee'] = Decimal(str(fee_info['cost']))
            if 'currency' in fee_info:
                fees['fee_currency'] = fee_info['currency']
        return fees

    def get_exchange_info(self) -> Dict[str, Any]:
        """Get exchange capabilities and info"""
        if not self.exchange:
            return {}
        
        return {
            'id': self.exchange_id,
            'name': self.exchange.name if hasattr(self.exchange, 'name') else self.exchange_id,
            'type': 'DEX' if self.is_dex else 'CEX',
            'has': self.exchange.has if hasattr(self.exchange, 'has') else {},
            'rate_limit': self._rate_limit_delay,
            'markets_count': len(self.exchange.markets) if self._markets_loaded else 0,
            'countries': self.exchange.countries if hasattr(self.exchange, 'countries') else [],
            'urls': self.exchange.urls if hasattr(self.exchange, 'urls') else {}
        }

    async def fetch_my_trades(
        self, 
        symbol: Optional[str] = None, 
        since: Optional[int] = None,
        limit: int = 100
    ) -> List[dict]:
        """
        Fetch user's trade history from the exchange.
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT'). If None, fetches for common pairs.
            since: Unix timestamp in milliseconds to fetch trades from
            limit: Maximum number of trades per symbol
            
        Returns:
            List of trade dictionaries in CCXT format
        """
        if not self.exchange:
            raise RuntimeError(f"{self.exchange_id} not initialized")
        
        # Check if exchange supports fetchMyTrades
        if not self.exchange.has.get('fetchMyTrades'):
            logger.warning(f"{self.exchange_id} does not support fetchMyTrades")
            return []
        
        all_trades = []
        
        try:
            if symbol:
                # Fetch trades for specific symbol
                trades = await self.exchange.fetch_my_trades(symbol, since=since, limit=limit)
                all_trades.extend(trades)
            else:
                # Get balance to determine which pairs to check
                try:
                    balance = await self.exchange.fetch_balance()
                    assets = [k for k, v in balance.get('total', {}).items() 
                             if isinstance(v, (int, float)) and v > 0 and k not in ['USDT', 'USDC', 'USD', 'EUR']]
                    
                    # Fetch trades for each asset paired with USDT/USD
                    quote_currencies = ['USDT', 'USDC', 'USD', 'EUR', 'BTC']
                    for asset in assets[:10]:  # Limit to 10 assets
                        for quote in quote_currencies:
                            pair = f"{asset}/{quote}"
                            if pair in self.exchange.markets:
                                try:
                                    trades = await self.exchange.fetch_my_trades(pair, since=since, limit=limit)
                                    all_trades.extend(trades)
                                except Exception:
                                    pass  # Pair might not exist or no trades
                                break  # Found a valid quote currency
                except Exception as e:
                    logger.warning(f"Could not determine assets from balance: {e}")
                    # Fallback to common pairs
                    common_pairs = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT']
                    for pair in common_pairs:
                        if pair in self.exchange.markets:
                            try:
                                trades = await self.exchange.fetch_my_trades(pair, since=since, limit=limit)
                                all_trades.extend(trades)
                            except Exception:
                                pass
            
            # Sort by timestamp
            all_trades.sort(key=lambda x: x.get('timestamp', 0))
            return all_trades
            
        except Exception as e:
            logger.error(f"Failed to fetch trades from {self.exchange_id}: {e}")
            raise RuntimeError(f"Failed to fetch trades: {e}")

    async def get_supported_pairs(self) -> List[str]:
        """Get list of supported trading pairs"""
        return await self.get_trading_pairs()


async def create_connector(exchange_id: str, config: Dict[str, Any]) -> UniversalConnector:
    """
    Factory function to create and initialize a universal connector.
    
    Args:
        exchange_id: CCXT exchange identifier
        config: Configuration with credentials
        
    Returns:
        Initialized connector
    """
    connector = UniversalConnector(exchange_id, config)
    await connector.initialize()
    return connector


def list_supported_exchanges() -> Dict[str, List[str]]:
    """Get list of all supported exchanges"""
    return {
        'cex': SUPPORTED_CEX_EXCHANGES,
        'dex': SUPPORTED_DEX_EXCHANGES,
        'total': len(SUPPORTED_CEX_EXCHANGES) + len(SUPPORTED_DEX_EXCHANGES)
    }
