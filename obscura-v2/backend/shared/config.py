"""
Centralized Configuration Management

Environment-based configuration for all services.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment"""
    
    # Service identification
    SERVICE_NAME: str = "obscura-v2"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://obscura:obscura@localhost:5432/obscura"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_MAX_CONNECTIONS: int = 10
    
    # API Gateway
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 4
    CORS_ORIGINS: str = "*"
    
    # JWT/Auth
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # Nillion
    NILLION_CLUSTER_ID: str = ""
    NILLION_BOOTNODE: str = ""
    NILLION_USER_KEY: str = ""
    
    # Zcash
    ZCASH_RPC_URL: str = "http://localhost:8232"
    ZCASH_NETWORK: str = "testnet"
    
    # Services - Internal URLs
    TRADING_SERVICE_URL: str = "http://trading:8001"
    SUBSCRIPTIONS_SERVICE_URL: str = "http://subscriptions:8002"
    COPY_TRADING_SERVICE_URL: str = "http://copy-trading:8003"
    ANALYTICS_SERVICE_URL: str = "http://analytics:8004"
    CITADEL_SERVICE_URL: str = "http://citadel:8005"
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    
    # Copy Trading
    MAX_COPY_DELAY_MS: int = 1000
    DEFAULT_SLIPPAGE: float = 0.02
    
    # Binance Trading Environment
    # NOTE: API keys are NOT stored here - they are encrypted via Nillion/Citadel
    # Users submit keys via POST /citadel/secrets/store which encrypts them
    BINANCE_TESTNET: bool = False
    BINANCE_USE_DEMO: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore extra env vars not defined in Settings


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings()
