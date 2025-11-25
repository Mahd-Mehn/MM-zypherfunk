"""
Redis Cache and Session Management Service

Provides caching, session storage, and pub/sub functionality for Obscura V2.
Used for temporary data, real-time state, and inter-service communication.
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional, Set, TypeVar, Generic
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import asyncio

import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool

logger = logging.getLogger("obscura.redis")

T = TypeVar('T')


class RedisConfig:
    """Redis configuration from environment"""
    
    @staticmethod
    def get_url() -> str:
        return os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    @staticmethod
    def get_password() -> Optional[str]:
        return os.getenv("REDIS_PASSWORD")
    
    @staticmethod
    def get_pool_size() -> int:
        return int(os.getenv("REDIS_POOL_SIZE", "10"))


class RedisService:
    """
    Production Redis service with connection pooling and common operations.
    
    Features:
    - Connection pooling
    - JSON serialization/deserialization
    - TTL management
    - Pub/Sub support
    - Hash operations for complex objects
    - Set operations for unique collections
    - Sorted sets for leaderboards
    """
    
    _instance: Optional['RedisService'] = None
    _pool: Optional[ConnectionPool] = None
    _client: Optional[redis.Redis] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def initialize(self):
        """Initialize Redis connection pool"""
        if self._client is not None:
            return
        
        url = RedisConfig.get_url()
        
        self._pool = ConnectionPool.from_url(
            url,
            max_connections=RedisConfig.get_pool_size(),
            decode_responses=True
        )
        self._client = redis.Redis(connection_pool=self._pool)
        
        # Test connection
        try:
            await self._client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            raise
    
    async def close(self):
        """Close Redis connections"""
        if self._client:
            await self._client.close()
        if self._pool:
            await self._pool.disconnect()
        logger.info("Redis connections closed")
    
    @property
    def client(self) -> redis.Redis:
        """Get Redis client (must call initialize first)"""
        if self._client is None:
            raise RuntimeError("Redis not initialized. Call initialize() first.")
        return self._client
    
    # ========================================================================
    # Basic Key-Value Operations
    # ========================================================================
    
    async def get(self, key: str) -> Optional[str]:
        """Get a string value"""
        return await self.client.get(key)
    
    async def set(
        self, 
        key: str, 
        value: str, 
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """Set a string value with optional TTL"""
        if ttl_seconds:
            return await self.client.setex(key, ttl_seconds, value)
        return await self.client.set(key, value)
    
    async def delete(self, *keys: str) -> int:
        """Delete one or more keys"""
        return await self.client.delete(*keys)
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        return await self.client.exists(key) > 0
    
    async def expire(self, key: str, ttl_seconds: int) -> bool:
        """Set TTL on existing key"""
        return await self.client.expire(key, ttl_seconds)
    
    async def ttl(self, key: str) -> int:
        """Get remaining TTL (-1 if no expiry, -2 if key doesn't exist)"""
        return await self.client.ttl(key)
    
    # ========================================================================
    # JSON Operations
    # ========================================================================
    
    async def get_json(self, key: str) -> Optional[Any]:
        """Get and deserialize JSON"""
        value = await self.get(key)
        if value:
            return json.loads(value)
        return None
    
    async def set_json(
        self, 
        key: str, 
        value: Any, 
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """Serialize and set JSON value"""
        json_str = json.dumps(value, default=str)
        return await self.set(key, json_str, ttl_seconds)
    
    # ========================================================================
    # Hash Operations (for objects)
    # ========================================================================
    
    async def hget(self, key: str, field: str) -> Optional[str]:
        """Get a hash field"""
        return await self.client.hget(key, field)
    
    async def hset(self, key: str, field: str, value: str) -> int:
        """Set a hash field"""
        return await self.client.hset(key, field, value)
    
    async def hgetall(self, key: str) -> Dict[str, str]:
        """Get all hash fields"""
        return await self.client.hgetall(key)
    
    async def hmset(self, key: str, mapping: Dict[str, str]) -> bool:
        """Set multiple hash fields"""
        return await self.client.hset(key, mapping=mapping)
    
    async def hdel(self, key: str, *fields: str) -> int:
        """Delete hash fields"""
        return await self.client.hdel(key, *fields)
    
    async def hexists(self, key: str, field: str) -> bool:
        """Check if hash field exists"""
        return await self.client.hexists(key, field)
    
    async def hset_json(self, key: str, field: str, value: Any) -> int:
        """Set hash field with JSON value"""
        return await self.hset(key, field, json.dumps(value, default=str))
    
    async def hget_json(self, key: str, field: str) -> Optional[Any]:
        """Get hash field and deserialize JSON"""
        value = await self.hget(key, field)
        if value:
            return json.loads(value)
        return None
    
    async def hgetall_json(self, key: str) -> Dict[str, Any]:
        """Get all hash fields with JSON deserialization"""
        data = await self.hgetall(key)
        return {k: json.loads(v) for k, v in data.items()}
    
    # ========================================================================
    # Set Operations (for unique collections)
    # ========================================================================
    
    async def sadd(self, key: str, *members: str) -> int:
        """Add members to set"""
        return await self.client.sadd(key, *members)
    
    async def srem(self, key: str, *members: str) -> int:
        """Remove members from set"""
        return await self.client.srem(key, *members)
    
    async def smembers(self, key: str) -> Set[str]:
        """Get all set members"""
        return await self.client.smembers(key)
    
    async def sismember(self, key: str, member: str) -> bool:
        """Check if member is in set"""
        return await self.client.sismember(key, member)
    
    async def scard(self, key: str) -> int:
        """Get set cardinality (size)"""
        return await self.client.scard(key)
    
    # ========================================================================
    # Sorted Set Operations (for leaderboards, time-series)
    # ========================================================================
    
    async def zadd(self, key: str, mapping: Dict[str, float]) -> int:
        """Add members to sorted set with scores"""
        return await self.client.zadd(key, mapping)
    
    async def zrem(self, key: str, *members: str) -> int:
        """Remove members from sorted set"""
        return await self.client.zrem(key, *members)
    
    async def zscore(self, key: str, member: str) -> Optional[float]:
        """Get member's score"""
        return await self.client.zscore(key, member)
    
    async def zrank(self, key: str, member: str) -> Optional[int]:
        """Get member's rank (0-based, ascending)"""
        return await self.client.zrank(key, member)
    
    async def zrevrank(self, key: str, member: str) -> Optional[int]:
        """Get member's rank (0-based, descending)"""
        return await self.client.zrevrank(key, member)
    
    async def zrange(
        self, 
        key: str, 
        start: int = 0, 
        stop: int = -1,
        withscores: bool = False
    ) -> List:
        """Get range of members by rank (ascending)"""
        return await self.client.zrange(key, start, stop, withscores=withscores)
    
    async def zrevrange(
        self, 
        key: str, 
        start: int = 0, 
        stop: int = -1,
        withscores: bool = False
    ) -> List:
        """Get range of members by rank (descending)"""
        return await self.client.zrevrange(key, start, stop, withscores=withscores)
    
    async def zincrby(self, key: str, amount: float, member: str) -> float:
        """Increment member's score"""
        return await self.client.zincrby(key, amount, member)
    
    # ========================================================================
    # List Operations (for queues, recent items)
    # ========================================================================
    
    async def lpush(self, key: str, *values: str) -> int:
        """Push to left of list"""
        return await self.client.lpush(key, *values)
    
    async def rpush(self, key: str, *values: str) -> int:
        """Push to right of list"""
        return await self.client.rpush(key, *values)
    
    async def lpop(self, key: str) -> Optional[str]:
        """Pop from left of list"""
        return await self.client.lpop(key)
    
    async def rpop(self, key: str) -> Optional[str]:
        """Pop from right of list"""
        return await self.client.rpop(key)
    
    async def lrange(self, key: str, start: int, stop: int) -> List[str]:
        """Get range of list elements"""
        return await self.client.lrange(key, start, stop)
    
    async def llen(self, key: str) -> int:
        """Get list length"""
        return await self.client.llen(key)
    
    async def ltrim(self, key: str, start: int, stop: int) -> bool:
        """Trim list to specified range"""
        return await self.client.ltrim(key, start, stop)
    
    # ========================================================================
    # Pub/Sub Operations
    # ========================================================================
    
    async def publish(self, channel: str, message: str) -> int:
        """Publish message to channel"""
        return await self.client.publish(channel, message)
    
    async def publish_json(self, channel: str, data: Any) -> int:
        """Publish JSON message to channel"""
        return await self.publish(channel, json.dumps(data, default=str))
    
    def pubsub(self):
        """Get pubsub instance for subscribing"""
        return self.client.pubsub()
    
    # ========================================================================
    # Atomic Operations
    # ========================================================================
    
    async def incr(self, key: str) -> int:
        """Increment integer value"""
        return await self.client.incr(key)
    
    async def incrby(self, key: str, amount: int) -> int:
        """Increment by amount"""
        return await self.client.incrby(key, amount)
    
    async def decr(self, key: str) -> int:
        """Decrement integer value"""
        return await self.client.decr(key)
    
    async def decrby(self, key: str, amount: int) -> int:
        """Decrement by amount"""
        return await self.client.decrby(key, amount)
    
    # ========================================================================
    # Utility Methods
    # ========================================================================
    
    async def keys(self, pattern: str) -> List[str]:
        """Get keys matching pattern (use sparingly in production)"""
        return await self.client.keys(pattern)
    
    async def scan(
        self, 
        cursor: int = 0, 
        match: Optional[str] = None, 
        count: int = 100
    ) -> tuple:
        """Scan keys incrementally"""
        return await self.client.scan(cursor=cursor, match=match, count=count)
    
    async def flushdb(self):
        """Flush current database (use with caution!)"""
        return await self.client.flushdb()


# Global singleton instance
redis_service = RedisService()


# ============================================================================
# Cache Key Builders
# ============================================================================

class CacheKeys:
    """Standardized cache key builders"""
    
    # User-related
    @staticmethod
    def user_session(user_id: str) -> str:
        return f"session:{user_id}"
    
    @staticmethod
    def user_profile(user_id: str) -> str:
        return f"profile:{user_id}"
    
    # Subscription-related
    @staticmethod
    def subscription_plans() -> str:
        return "plans:all"
    
    @staticmethod
    def trader_plan(trader_id: str, plan_id: str) -> str:
        return f"plans:trader:{trader_id}:{plan_id}"
    
    @staticmethod
    def user_subscriptions(user_id: str) -> str:
        return f"subscriptions:user:{user_id}"
    
    @staticmethod
    def subscription(sub_id: str) -> str:
        return f"subscriptions:{sub_id}"
    
    @staticmethod
    def payments(subscription_id: str) -> str:
        return f"payments:{subscription_id}"
    
    # Trading-related
    @staticmethod
    def trader_positions(trader_id: str) -> str:
        return f"positions:{trader_id}"
    
    @staticmethod
    def trader_trades(trader_id: str) -> str:
        return f"trades:{trader_id}"
    
    @staticmethod
    def trade(trade_id: str) -> str:
        return f"trade:{trade_id}"
    
    @staticmethod
    def open_positions(trader_id: str) -> str:
        return f"positions:open:{trader_id}"
    
    # Analytics-related
    @staticmethod
    def trader_metrics(trader_id: str) -> str:
        return f"metrics:{trader_id}"
    
    @staticmethod
    def leaderboard(period: str = "all") -> str:
        return f"leaderboard:{period}"
    
    @staticmethod
    def capital_history(trader_id: str) -> str:
        return f"capital:{trader_id}"
    
    # Monitoring-related
    @staticmethod
    def monitored_traders() -> str:
        return "monitoring:traders"
    
    @staticmethod
    def trader_followers(trader_id: str) -> str:
        return f"followers:{trader_id}"
    
    @staticmethod
    def recent_orders(trader_id: str) -> str:
        return f"orders:recent:{trader_id}"
    
    # Copy trading-related
    @staticmethod
    def copy_settings(follower_id: str) -> str:
        return f"copy:settings:{follower_id}"
    
    @staticmethod
    def copy_history(follower_id: str) -> str:
        return f"copy:history:{follower_id}"
    
    @staticmethod
    def follower_credentials(follower_id: str) -> str:
        return f"credentials:follower:{follower_id}"
    
    # Key storage-related
    @staticmethod
    def user_credentials(user_id: str) -> str:
        return f"credentials:user:{user_id}"
    
    @staticmethod
    def credential_metadata(credential_id: str) -> str:
        return f"credential:{credential_id}"
    
    # Rate limiting
    @staticmethod
    def rate_limit(user_id: str, endpoint: str) -> str:
        return f"ratelimit:{user_id}:{endpoint}"
    
    # Pub/Sub channels
    @staticmethod
    def trade_events_channel(trader_id: str) -> str:
        return f"events:trades:{trader_id}"
    
    @staticmethod
    def price_updates_channel(symbol: str) -> str:
        return f"events:prices:{symbol}"


# TTL constants (in seconds)
class CacheTTL:
    """Standard cache TTL values"""
    SHORT = 60  # 1 minute
    MEDIUM = 300  # 5 minutes
    LONG = 3600  # 1 hour
    DAY = 86400  # 24 hours
    WEEK = 604800  # 7 days
    
    # Specific TTLs
    SESSION = 86400  # 24 hours
    METRICS = 300  # 5 minutes (analytics cache)
    POSITIONS = 60  # 1 minute (real-time positions)
    LEADERBOARD = 600  # 10 minutes
    RATE_LIMIT = 60  # 1 minute window
