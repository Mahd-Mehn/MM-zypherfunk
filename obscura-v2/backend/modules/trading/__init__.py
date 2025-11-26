"""
Trading Module

Handles all exchange connectivity and trade execution.
Can run as standalone microservice or part of monolith.

Components:
- exchanges/: CCXT-based exchange connectors (100+ exchanges)
- key_storage: Secure API key management via Nillion
- orchestrator: Multi-exchange trading orchestration
- pnl_calculator: PnL and Reputation Score calculation
"""

from .service import app as trading_app, orchestrator, pnl_calculator
from .key_storage import SecureKeyStorage, ExchangeProvider, key_storage
from .pnl_calculator import PnLCalculator, ReputationScore, ClosedTrade, TradeExecution

__all__ = [
    "trading_app",
    "orchestrator",
    "pnl_calculator",
    "SecureKeyStorage",
    "ExchangeProvider",
    "key_storage",
    "PnLCalculator",
    "ReputationScore",
    "ClosedTrade",
    "TradeExecution",
]
