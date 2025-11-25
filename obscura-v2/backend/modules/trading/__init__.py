"""
Trading Module

Handles all exchange connectivity and trade execution.
Can run as standalone microservice or part of monolith.

Components:
- exchanges/: CCXT-based exchange connectors (100+ exchanges)
- key_storage: Secure API key management via Nillion
- orchestrator: Multi-exchange trading orchestration
"""

from .service import TradingService
from .key_storage import SecureKeyStorage, ExchangeProvider, key_storage

__all__ = [
    "TradingService",
    "SecureKeyStorage",
    "ExchangeProvider",
    "key_storage",
]
