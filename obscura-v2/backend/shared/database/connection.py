"""
Database connection and session management for Obscura V2
Supports both synchronous and asynchronous operations
"""

import os
from typing import AsyncGenerator, Generator
from contextlib import contextmanager, asynccontextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import QueuePool, NullPool


# Base class for all models
Base = declarative_base()


def get_database_url(async_mode: bool = False) -> str:
    """
    Get database URL from environment variables
    
    Supports:
    - PostgreSQL (recommended for production)
    - SQLite (for development/testing)
    
    Args:
        async_mode: If True, returns async-compatible URL
        
    Returns:
        Database connection URL
    """
    # Check for explicit DATABASE_URL
    database_url = os.getenv("DATABASE_URL")
    
    if database_url:
        # Handle Heroku-style postgres:// URLs
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        
        if async_mode:
            # Convert to async URL
            if database_url.startswith("postgresql://"):
                database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
            elif database_url.startswith("sqlite://"):
                database_url = database_url.replace("sqlite://", "sqlite+aiosqlite://", 1)
        
        return database_url
    
    # Build URL from components
    db_type = os.getenv("DB_TYPE", "postgresql")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "obscura")
    db_user = os.getenv("DB_USER", "obscura")
    db_password = os.getenv("DB_PASSWORD", "")
    
    if db_type == "sqlite":
        db_path = os.getenv("SQLITE_PATH", "./obscura.db")
        driver = "+aiosqlite" if async_mode else ""
        return f"sqlite{driver}:///{db_path}"
    else:
        driver = "+asyncpg" if async_mode else ""
        return f"postgresql{driver}://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


# Synchronous engine and session
_sync_engine = None
_SessionLocal = None


def get_engine():
    """Get or create synchronous database engine"""
    global _sync_engine
    
    if _sync_engine is None:
        database_url = get_database_url(async_mode=False)
        
        # Configure pool based on database type
        if "sqlite" in database_url:
            _sync_engine = create_engine(
                database_url,
                connect_args={"check_same_thread": False},
                echo=os.getenv("DB_ECHO", "false").lower() == "true"
            )
        else:
            _sync_engine = create_engine(
                database_url,
                poolclass=QueuePool,
                pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
                max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=os.getenv("DB_ECHO", "false").lower() == "true"
            )
    
    return _sync_engine


def get_session_factory():
    """Get session factory for synchronous operations"""
    global _SessionLocal
    
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=get_engine()
        )
    
    return _SessionLocal


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Get a database session with automatic cleanup"""
    SessionLocal = get_session_factory()
    session = SessionLocal()
    
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# Asynchronous engine and session
_async_engine = None
AsyncSessionLocal = None


def get_async_engine():
    """Get or create asynchronous database engine"""
    global _async_engine
    
    if _async_engine is None:
        database_url = get_database_url(async_mode=True)
        
        if "sqlite" in database_url:
            _async_engine = create_async_engine(
                database_url,
                echo=os.getenv("DB_ECHO", "false").lower() == "true"
            )
        else:
            # Note: Don't specify poolclass for async engine - SQLAlchemy will use AsyncAdaptedQueuePool
            _async_engine = create_async_engine(
                database_url,
                pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
                max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=os.getenv("DB_ECHO", "false").lower() == "true"
            )
    
    return _async_engine


def get_async_session_factory():
    """Get async session factory"""
    global AsyncSessionLocal
    
    if AsyncSessionLocal is None:
        AsyncSessionLocal = async_sessionmaker(
            bind=get_async_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
        )
    
    return AsyncSessionLocal


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get an async database session with automatic cleanup"""
    factory = get_async_session_factory()
    session = factory()
    
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def init_db():
    """Initialize database tables"""
    from . import models  # Import models to register them
    
    engine = get_async_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def init_db_sync():
    """Initialize database tables (synchronous)"""
    from . import models  # Import models to register them
    
    engine = get_engine()
    Base.metadata.create_all(bind=engine)


# FastAPI dependency
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database sessions"""
    async with get_async_session() as session:
        yield session


# Connection event listeners for debugging
@event.listens_for(get_engine(), "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable foreign keys for SQLite"""
    if "sqlite" in get_database_url():
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
