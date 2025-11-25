"""
Shared Module - Cross-cutting concerns for all services

Contains:
- database: SQLAlchemy models and connection management
- services: Redis, messaging, and common utilities
- config: Configuration management
- utils: Common utilities
"""

from .config import settings
from .database import get_async_session, init_db, Base
from .services import RedisService

__all__ = [
    "settings",
    "get_async_session",
    "init_db", 
    "Base",
    "RedisService",
]
