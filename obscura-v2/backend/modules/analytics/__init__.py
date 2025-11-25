"""
Analytics Module

Trading performance analytics, metrics, and leaderboards.
Can run as standalone microservice or part of monolith.

Components:
- engine: Core analytics calculations
- service: HTTP API
"""

from .engine import AnalyticsEngine, analytics_engine

__all__ = [
    "AnalyticsEngine",
    "analytics_engine",
]
