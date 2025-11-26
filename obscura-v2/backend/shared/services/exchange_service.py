"""
CCXT Exchange Service

Dynamically discovers and provides information about all 100+ exchanges
supported by CCXT, including both CEX and DEX platforms.
"""

import ccxt
import ccxt.async_support as ccxt_async
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

from shared.services import redis_service, CacheKeys, CacheTTL

logger = logging.getLogger("obscura.exchange_service")


@dataclass
class ExchangeInfo:
    """Information about a supported exchange"""
    id: str
    name: str
    display_name: str
    exchange_type: str  # cex or dex
    countries: List[str]
    logo_url: Optional[str]
    api_docs_url: Optional[str]
    
    # Capabilities
    has_fetch_my_trades: bool
    has_fetch_orders: bool
    has_fetch_balance: bool
    has_create_order: bool
    has_cancel_order: bool
    has_websocket: bool
    has_fetch_ohlcv: bool
    has_fetch_ticker: bool
    
    # Rate limits
    rate_limit: int
    
    # Requirements
    requires_api_key: bool
    requires_secret: bool
    requires_password: bool  # passphrase
    requires_uid: bool
    
    # Status
    is_active: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# Known DEX exchanges in CCXT
DEX_EXCHANGES = {
    'uniswap', 'uniswapv2', 'uniswapv3',
    'pancakeswap',
    'sushiswap',
    'quickswap',
    '1inch',
    'paraswap',
    'kyberswap', 'kybernetwork',
    'balancer',
    'curve', 'curvefinance',
    'bancor',
    'dydx',
    'gmx',
    'jupiter',
    'raydium',
    'orca',
    'serum',
    'vertex',
    'traderjoe',
    'spookyswap',
    'spiritswap',
    'velodrome',
    'aerodrome',
    'camelot',
    'woofi',
}


def get_all_ccxt_exchanges() -> List[str]:
    """Get list of all CCXT exchange IDs"""
    return ccxt.exchanges


def get_exchange_info(exchange_id: str) -> Optional[ExchangeInfo]:
    """Get detailed information about a specific exchange"""
    if exchange_id not in ccxt.exchanges:
        return None
    
    try:
        # Create exchange instance (no credentials needed for info)
        exchange_class = getattr(ccxt, exchange_id)
        exchange = exchange_class()
        
        # Determine exchange type
        exchange_type = "dex" if exchange_id in DEX_EXCHANGES else "cex"
        
        # Extract capabilities
        has_caps = exchange.has or {}
        
        # Build display name
        display_name = exchange.name if hasattr(exchange, 'name') else exchange_id.title()
        
        # Get logo URL (CCXT provides these)
        logo_url = None
        if hasattr(exchange, 'urls') and isinstance(exchange.urls, dict):
            logo_url = exchange.urls.get('logo')
        
        # Get API docs URL
        api_docs_url = None
        if hasattr(exchange, 'urls') and isinstance(exchange.urls, dict):
            api_docs_url = exchange.urls.get('doc')
            if isinstance(api_docs_url, list):
                api_docs_url = api_docs_url[0] if api_docs_url else None
        
        # Get countries
        countries = []
        if hasattr(exchange, 'countries'):
            countries = exchange.countries if isinstance(exchange.countries, list) else [exchange.countries]
        
        # Get rate limit
        rate_limit = exchange.rateLimit if hasattr(exchange, 'rateLimit') else 1000
        
        # Check credential requirements
        required_credentials = exchange.requiredCredentials if hasattr(exchange, 'requiredCredentials') else {}
        
        return ExchangeInfo(
            id=exchange_id,
            name=exchange.id,
            display_name=display_name,
            exchange_type=exchange_type,
            countries=countries,
            logo_url=logo_url,
            api_docs_url=api_docs_url,
            has_fetch_my_trades=bool(has_caps.get('fetchMyTrades')),
            has_fetch_orders=bool(has_caps.get('fetchOrders') or has_caps.get('fetchOpenOrders')),
            has_fetch_balance=bool(has_caps.get('fetchBalance')),
            has_create_order=bool(has_caps.get('createOrder')),
            has_cancel_order=bool(has_caps.get('cancelOrder')),
            has_websocket=bool(has_caps.get('ws')),
            has_fetch_ohlcv=bool(has_caps.get('fetchOHLCV')),
            has_fetch_ticker=bool(has_caps.get('fetchTicker')),
            rate_limit=rate_limit,
            requires_api_key=required_credentials.get('apiKey', True),
            requires_secret=required_credentials.get('secret', True),
            requires_password=required_credentials.get('password', False),
            requires_uid=required_credentials.get('uid', False),
            is_active=True,
        )
    except Exception as e:
        logger.warning(f"Failed to get info for {exchange_id}: {e}")
        return None


class ExchangeService:
    """Service for managing exchange information and connections"""
    
    # Cache TTL for exchange list (1 hour)
    CACHE_TTL = 3600
    
    def __init__(self):
        self._exchanges_cache: Optional[Dict[str, ExchangeInfo]] = None
        self._cache_time: Optional[datetime] = None
    
    async def get_all_exchanges(self, force_refresh: bool = False) -> Dict[str, ExchangeInfo]:
        """Get all supported exchanges with caching"""
        # Check Redis cache first
        cache_key = CacheKeys.supported_exchanges()
        
        if not force_refresh:
            cached = await redis_service.get_json(cache_key)
            if cached:
                return {k: ExchangeInfo(**v) for k, v in cached.items()}
        
        # Build exchange info
        exchanges = {}
        for exchange_id in get_all_ccxt_exchanges():
            info = get_exchange_info(exchange_id)
            if info:
                exchanges[exchange_id] = info
        
        # Cache in Redis
        cache_data = {k: v.to_dict() for k, v in exchanges.items()}
        await redis_service.set_json(cache_key, cache_data, ttl_seconds=self.CACHE_TTL)
        
        logger.info(f"Loaded {len(exchanges)} exchanges from CCXT")
        return exchanges
    
    async def get_exchange(self, exchange_id: str) -> Optional[ExchangeInfo]:
        """Get info for a specific exchange"""
        cache_key = CacheKeys.exchange_details(exchange_id)
        
        # Check cache
        cached = await redis_service.get_json(cache_key)
        if cached:
            return ExchangeInfo(**cached)
        
        # Get fresh info
        info = get_exchange_info(exchange_id)
        if info:
            await redis_service.set_json(cache_key, info.to_dict(), ttl_seconds=self.CACHE_TTL)
        
        return info
    
    async def get_exchanges_by_type(self, exchange_type: str) -> List[ExchangeInfo]:
        """Get exchanges filtered by type (cex or dex)"""
        exchanges = await self.get_all_exchanges()
        return [ex for ex in exchanges.values() if ex.exchange_type == exchange_type]
    
    async def get_exchanges_with_capability(self, capability: str) -> List[ExchangeInfo]:
        """Get exchanges that have a specific capability"""
        exchanges = await self.get_all_exchanges()
        
        capability_map = {
            'fetchMyTrades': 'has_fetch_my_trades',
            'fetchOrders': 'has_fetch_orders',
            'fetchBalance': 'has_fetch_balance',
            'createOrder': 'has_create_order',
            'cancelOrder': 'has_cancel_order',
            'websocket': 'has_websocket',
            'fetchOHLCV': 'has_fetch_ohlcv',
            'fetchTicker': 'has_fetch_ticker',
        }
        
        attr = capability_map.get(capability, capability)
        return [ex for ex in exchanges.values() if getattr(ex, attr, False)]
    
    async def search_exchanges(self, query: str) -> List[ExchangeInfo]:
        """Search exchanges by name or ID"""
        exchanges = await self.get_all_exchanges()
        query_lower = query.lower()
        
        return [
            ex for ex in exchanges.values()
            if query_lower in ex.id.lower() or query_lower in ex.display_name.lower()
        ]
    
    async def get_summary(self) -> Dict[str, Any]:
        """Get summary of supported exchanges"""
        exchanges = await self.get_all_exchanges()
        
        cex_count = sum(1 for ex in exchanges.values() if ex.exchange_type == 'cex')
        dex_count = sum(1 for ex in exchanges.values() if ex.exchange_type == 'dex')
        with_trades = sum(1 for ex in exchanges.values() if ex.has_fetch_my_trades)
        with_websocket = sum(1 for ex in exchanges.values() if ex.has_websocket)
        
        return {
            'total': len(exchanges),
            'cex_count': cex_count,
            'dex_count': dex_count,
            'with_fetch_my_trades': with_trades,
            'with_websocket': with_websocket,
            'exchange_ids': list(exchanges.keys()),
        }
    
    def get_setup_instructions(self, exchange_id: str) -> List[str]:
        """Get setup instructions for an exchange"""
        # Common instructions template
        common = [
            f"Log in to your {exchange_id.title()} account",
            "Navigate to API Management or API Keys section",
            "Create a new API key",
            "Copy the API Key and Secret securely",
            "Store the credentials in Obscura",
        ]
        
        # Exchange-specific additions
        specific_instructions = {
            'binance': [
                "Enable 'Enable Reading' and 'Enable Spot & Margin Trading'",
                "Consider adding your server IP to the whitelist for security",
            ],
            'coinbase': [
                "Select 'view' and 'trade' permissions",
                "For Advanced Trade API, use OAuth or API keys",
            ],
            'kraken': [
                "Select 'Query Funds', 'Query Orders & Trades' permissions",
                "For trading, also enable 'Create & Modify Orders'",
            ],
            'okx': [
                "Create a passphrase (REQUIRED for OKX)",
                "Enable 'Trade' permission",
            ],
            'kucoin': [
                "Create a passphrase (REQUIRED for KuCoin)",
                "Enable 'General' and 'Trade' permissions",
            ],
            'bybit': [
                "Enable 'Read' and 'Trade' permissions",
                "Set IP restrictions for enhanced security",
            ],
        }
        
        instructions = common.copy()
        if exchange_id.lower() in specific_instructions:
            # Insert specific instructions before the last common instruction
            instructions = common[:-1] + specific_instructions[exchange_id.lower()] + [common[-1]]
        
        return instructions


# Singleton instance
exchange_service = ExchangeService()


# Helper functions for backward compatibility
def list_supported_exchanges() -> Dict[str, Any]:
    """Get list of all supported exchanges (sync version for quick access)"""
    all_exchanges = get_all_ccxt_exchanges()
    
    cex = [ex for ex in all_exchanges if ex not in DEX_EXCHANGES]
    dex = [ex for ex in all_exchanges if ex in DEX_EXCHANGES]
    
    return {
        'cex': cex,
        'dex': dex,
        'total': len(all_exchanges),
        'all': all_exchanges,
    }


async def get_exchange_details(exchange_id: str) -> Optional[Dict[str, Any]]:
    """Get exchange details as dictionary"""
    info = await exchange_service.get_exchange(exchange_id)
    return info.to_dict() if info else None
