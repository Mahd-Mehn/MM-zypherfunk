"""
Copy Trading Module

Real-time trade copying from lead traders to followers.
Can run as standalone microservice or part of monolith.

Components:
- monitor: Trade event detection and streaming
- engine: Copy trade execution
- service: HTTP API
"""

from .engine import CopyTradingEngine, copy_engine
from .monitor import TradeMonitor, TradeEvent, TradeEventType, trade_monitor

__all__ = [
    "CopyTradingEngine",
    "copy_engine",
    "TradeMonitor",
    "TradeEvent",
    "TradeEventType",
    "trade_monitor",
]
