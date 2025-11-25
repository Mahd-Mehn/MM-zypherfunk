"""
Multi-Exchange Trading Infrastructure
Supports both CEXes (Binance, Coinbase) and DEXes (Uniswap, Starknet, etc.)
"""

from .base import ExchangeConnector, TradeOrder, OrderType, OrderSide
from .binance_connector import BinanceConnector
from .coinbase_connector import CoinbaseConnector
from .uniswap_connector import UniswapConnector
from .starknet_connector import StarknetConnector
from .orchestrator import TradingOrchestrator

__all__ = [
    'ExchangeConnector',
    'TradeOrder',
    'OrderType',
    'OrderSide',
    'BinanceConnector',
    'CoinbaseConnector',
    'UniswapConnector',
    'StarknetConnector',
    'TradingOrchestrator'
]
