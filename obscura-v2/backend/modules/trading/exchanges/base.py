"""
Base classes and types for exchange integration
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Optional, Any
from decimal import Decimal
from pydantic import BaseModel
from datetime import datetime


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class ExchangeType(str, Enum):
    CEX = "cex"
    DEX = "dex"


class TradeOrder(BaseModel):
    """Unified order model for all exchanges"""
    symbol: str  # e.g., "BTC/USDT" for CEX, "WBTC/USDC" for DEX
    side: OrderSide
    order_type: OrderType
    amount: Decimal
    price: Optional[Decimal] = None  # Required for limit orders
    stop_price: Optional[Decimal] = None  # For stop orders
    slippage: Optional[Decimal] = None  # For DEX trades (e.g., 0.01 = 1%)
    gas_price: Optional[Decimal] = None  # For DEX trades
    deadline: Optional[int] = None  # Unix timestamp for DEX trades


class OrderResult(BaseModel):
    """Result of an order execution"""
    order_id: str
    exchange: str
    exchange_type: ExchangeType
    symbol: str
    side: OrderSide
    amount: Decimal
    filled_amount: Decimal
    average_price: Decimal
    status: str  # "filled", "partial", "pending", "failed"
    tx_hash: Optional[str] = None  # For DEX trades
    timestamp: datetime
    fees: Dict[str, Decimal] = {}
    metadata: Dict[str, Any] = {}


class Balance(BaseModel):
    """Account balance"""
    asset: str
    free: Decimal
    locked: Decimal
    total: Decimal


class MarketData(BaseModel):
    """Market price and depth data"""
    symbol: str
    bid: Decimal
    ask: Decimal
    last: Decimal
    volume_24h: Decimal
    timestamp: datetime


class ExchangeConnector(ABC):
    """Abstract base class for all exchange connectors"""
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.exchange_type: ExchangeType = ExchangeType.CEX
        self.name: str = "BaseExchange"
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize connection to exchange"""
        pass
    
    @abstractmethod
    async def place_order(self, order: TradeOrder) -> OrderResult:
        """Place a trade order"""
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel an existing order"""
        pass
    
    @abstractmethod
    async def get_order_status(self, order_id: str, symbol: str) -> OrderResult:
        """Get status of an order"""
        pass
    
    @abstractmethod
    async def get_balance(self, asset: Optional[str] = None) -> List[Balance]:
        """Get account balance"""
        pass
    
    @abstractmethod
    async def get_market_data(self, symbol: str) -> MarketData:
        """Get current market data"""
        pass
    
    @abstractmethod
    async def get_supported_pairs(self) -> List[str]:
        """Get list of supported trading pairs"""
        pass
    
    def format_symbol(self, base: str, quote: str) -> str:
        """Format symbol for this exchange"""
        return f"{base}/{quote}"
