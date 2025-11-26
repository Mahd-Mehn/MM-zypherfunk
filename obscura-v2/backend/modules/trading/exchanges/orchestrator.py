"""
Trading Orchestrator
Manages multi-exchange trading operations with intelligent routing
"""

from typing import Dict, List, Optional, Any
from decimal import Decimal
from datetime import datetime
import asyncio

from .base import (
    ExchangeConnector, TradeOrder, OrderResult, Balance,
    MarketData, OrderType, OrderSide, ExchangeType
)
from .binance_connector import BinanceConnector
from .coinbase_connector import CoinbaseConnector
from .uniswap_connector import UniswapConnector
from .starknet_connector import StarknetConnector


class TradingOrchestrator:
    """
    Orchestrates trading across multiple exchanges (CEX and DEX)
    Features:
    - Smart order routing
    - Best execution price finding
    - Parallel order execution
    - Unified API for all exchanges
    """
    
    def __init__(self):
        self.exchanges: Dict[str, ExchangeConnector] = {}
        self.initialized_exchanges: List[str] = []
    
    async def add_exchange(self, name: str, connector: ExchangeConnector) -> bool:
        """Add an exchange connector"""
        self.exchanges[name] = connector
        success = await connector.initialize()
        if success:
            self.initialized_exchanges.append(name)
        return success
    
    async def initialize_all_exchanges(self, config: Dict[str, Any]) -> Dict[str, bool]:
        """Initialize all configured exchanges"""
        results = {}
        
        # Initialize Binance if configured
        if config.get('binance'):
            binance = BinanceConnector(
                api_key=config['binance'].get('api_key'),
                api_secret=config['binance'].get('api_secret')
            )
            results['binance'] = await self.add_exchange('binance', binance)
        
        # Initialize Coinbase if configured
        if config.get('coinbase'):
            coinbase = CoinbaseConnector(
                api_key=config['coinbase'].get('api_key'),
                api_secret=config['coinbase'].get('api_secret')
            )
            results['coinbase'] = await self.add_exchange('coinbase', coinbase)
        
        # Initialize Uniswap if configured
        if config.get('uniswap'):
            uniswap = UniswapConnector(
                private_key=config['uniswap'].get('private_key'),
                rpc_url=config['uniswap'].get('rpc_url')
            )
            results['uniswap'] = await self.add_exchange('uniswap', uniswap)
        
        # Initialize Starknet if configured
        if config.get('starknet'):
            starknet = StarknetConnector(
                private_key=config['starknet'].get('private_key'),
                account_address=config['starknet'].get('account_address')
            )
            results['starknet'] = await self.add_exchange('starknet', starknet)
        
        return results
    
    async def place_order(self, exchange_name: str, order: TradeOrder) -> OrderResult:
        """Place order on a specific exchange"""
        if exchange_name not in self.exchanges:
            raise ValueError(f"Exchange {exchange_name} not configured")
        
        exchange = self.exchanges[exchange_name]
        return await exchange.place_order(order)
    
    async def place_order_with_fallback(
        self, 
        preferred_exchanges: List[str], 
        order: TradeOrder
    ) -> OrderResult:
        """
        Place order with fallback to alternative exchanges
        Tries exchanges in order until one succeeds
        """
        errors = []
        
        for exchange_name in preferred_exchanges:
            if exchange_name not in self.exchanges:
                errors.append(f"{exchange_name}: not configured")
                continue
            
            try:
                result = await self.place_order(exchange_name, order)
                return result
            except Exception as e:
                errors.append(f"{exchange_name}: {str(e)}")
                continue
        
        raise RuntimeError(f"All exchanges failed. Errors: {errors}")
    
    async def get_best_price(self, symbol: str, side: OrderSide) -> Dict[str, Any]:
        """Find best execution price across all exchanges"""
        prices = {}
        
        tasks = []
        for name, exchange in self.exchanges.items():
            if name in self.initialized_exchanges:
                tasks.append(self._get_price_safe(name, exchange, symbol))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, (name, _) in enumerate(self.exchanges.items()):
            if not isinstance(results[i], Exception) and results[i]:
                prices[name] = results[i]
        
        if not prices:
            raise RuntimeError("No prices available from any exchange")
        
        # Find best price based on side
        if side == OrderSide.BUY:
            # For buying, we want the lowest ask
            best_exchange = min(prices.items(), key=lambda x: x[1].ask)
        else:
            # For selling, we want the highest bid
            best_exchange = max(prices.items(), key=lambda x: x[1].bid)
        
        return {
            'best_exchange': best_exchange[0],
            'best_price': best_exchange[1].ask if side == OrderSide.BUY else best_exchange[1].bid,
            'all_prices': {name: {
                'bid': float(data.bid),
                'ask': float(data.ask),
                'last': float(data.last)
            } for name, data in prices.items()}
        }
    
    async def _get_price_safe(
        self, 
        name: str, 
        exchange: ExchangeConnector, 
        symbol: str
    ) -> Optional[MarketData]:
        """Get price with exception handling"""
        try:
            return await exchange.get_market_data(symbol)
        except Exception as e:
            print(f"Failed to get price from {name}: {e}")
            return None
    
    async def execute_smart_order(
        self, 
        order: TradeOrder, 
        strategy: str = "best_price"
    ) -> OrderResult:
        """
        Execute order with intelligent routing
        
        Strategies:
        - best_price: Route to exchange with best price
        - parallel: Split order across multiple exchanges
        - fallback: Try exchanges in order until success
        """
        if strategy == "best_price":
            # Find best price and route there
            best = await self.get_best_price(order.symbol, order.side)
            return await self.place_order(best['best_exchange'], order)
        
        elif strategy == "fallback":
            # Try CEXes first, then DEXes
            cex_exchanges = [name for name, ex in self.exchanges.items() 
                           if ex.exchange_type == ExchangeType.CEX]
            dex_exchanges = [name for name, ex in self.exchanges.items() 
                           if ex.exchange_type == ExchangeType.DEX]
            
            return await self.place_order_with_fallback(
                cex_exchanges + dex_exchanges, 
                order
            )
        
        elif strategy == "parallel":
            # Split order across multiple exchanges (advanced)
            raise NotImplementedError("Parallel execution not yet implemented")
        
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
    
    async def get_aggregated_balance(self, asset: Optional[str] = None) -> Dict[str, Any]:
        """Get balances across all exchanges"""
        all_balances = {}
        
        for name, exchange in self.exchanges.items():
            if name in self.initialized_exchanges:
                try:
                    balances = await exchange.get_balance(asset)
                    all_balances[name] = [
                        {
                            'asset': b.asset,
                            'free': float(b.free),
                            'locked': float(b.locked),
                            'total': float(b.total)
                        } for b in balances
                    ]
                except Exception as e:
                    print(f"Failed to get balance from {name}: {e}")
                    all_balances[name] = []
        
        # Aggregate totals
        if asset:
            total_free = sum(
                sum(b['free'] for b in balances if b['asset'] == asset)
                for balances in all_balances.values()
            )
            total_locked = sum(
                sum(b['locked'] for b in balances if b['asset'] == asset)
                for balances in all_balances.values()
            )
            
            return {
                'asset': asset,
                'total_free': total_free,
                'total_locked': total_locked,
                'total': total_free + total_locked,
                'by_exchange': all_balances
            }
        
        return {'by_exchange': all_balances}
    
    async def get_all_supported_pairs(self) -> Dict[str, List[str]]:
        """Get all supported pairs from all exchanges"""
        pairs = {}
        
        for name, exchange in self.exchanges.items():
            if name in self.initialized_exchanges:
                try:
                    pairs[name] = await exchange.get_supported_pairs()
                except Exception as e:
                    print(f"Failed to get pairs from {name}: {e}")
                    pairs[name] = []
        
        return pairs
    
    def get_exchange_status(self) -> Dict[str, Any]:
        """Get status of all exchanges"""
        return {
            'total_exchanges': len(self.exchanges),
            'initialized_exchanges': len(self.initialized_exchanges),
            'exchanges': {
                name: {
                    'name': ex.name,
                    'type': ex.exchange_type.value,
                    'initialized': name in self.initialized_exchanges
                }
                for name, ex in self.exchanges.items()
            }
        }
    
    async def replicate_trade(
        self, 
        source_exchange: str, 
        target_exchanges: List[str], 
        order: TradeOrder,
        delay_ms: int = 100
    ) -> List[OrderResult]:
        """
        Replicate a trade from one exchange to multiple others
        Useful for copy-trading implementation
        """
        results = []
        
        # Execute on source first
        source_result = await self.place_order(source_exchange, order)
        results.append(source_result)
        
        # Add small delay for market to adjust
        if delay_ms > 0:
            await asyncio.sleep(delay_ms / 1000)
        
        # Execute on target exchanges in parallel
        tasks = [
            self.place_order(target, order) 
            for target in target_exchanges 
            if target in self.exchanges
        ]
        
        target_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in target_results:
            if not isinstance(result, Exception):
                results.append(result)
        
        return results

    async def fetch_user_trades(
        self,
        exchange_name: Optional[str] = None,
        symbol: Optional[str] = None,
        since: Optional[int] = None,
        limit: int = 100
    ) -> Dict[str, List[dict]]:
        """
        Fetch user's trade history from one or all exchanges.
        
        Args:
            exchange_name: Specific exchange to fetch from (None = all)
            symbol: Trading pair (e.g., 'BTC/USDT')
            since: Unix timestamp in milliseconds
            limit: Maximum trades per exchange/symbol
            
        Returns:
            Dict mapping exchange name to list of trades
        """
        all_trades = {}
        
        if exchange_name:
            # Fetch from specific exchange
            if exchange_name not in self.exchanges:
                raise ValueError(f"Exchange {exchange_name} not configured")
            
            exchange = self.exchanges[exchange_name]
            try:
                trades = await exchange.fetch_my_trades(symbol, since, limit)
                all_trades[exchange_name] = trades
            except NotImplementedError:
                all_trades[exchange_name] = []
            except Exception as e:
                print(f"Failed to fetch trades from {exchange_name}: {e}")
                all_trades[exchange_name] = []
        else:
            # Fetch from all initialized exchanges
            for name, exchange in self.exchanges.items():
                if name in self.initialized_exchanges:
                    try:
                        trades = await exchange.fetch_my_trades(symbol, since, limit)
                        all_trades[name] = trades
                    except NotImplementedError:
                        all_trades[name] = []
                    except Exception as e:
                        print(f"Failed to fetch trades from {name}: {e}")
                        all_trades[name] = []
        
        return all_trades

    def get_initialized_exchanges(self) -> List[str]:
        """Get list of initialized exchange names"""
        return self.initialized_exchanges.copy()
