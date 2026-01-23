"""Async PostgreSQL Database Support.

Provides async SQLAlchemy 2.0 integration with connection pooling.
Supports both PostgreSQL (production) and SQLite (development).
"""

import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import AsyncAdaptedQueuePool

# SQLAlchemy base
Base = declarative_base()

# Global engine and session factory
_engine = None
_async_session_maker = None


def get_database_url() -> str:
    """Get database URL from environment.

    Priority:
    1. LEXECON_DATABASE_URL (explicit)
    2. DATABASE_URL (Railway/Heroku)
    3. PostgreSQL default (postgresql+asyncpg://lexecon:lexecon@localhost/lexecon)
    4. SQLite fallback (sqlite+aiosqlite:///lexecon.db)
    """
    # Check for explicit database URL
    db_url = os.getenv("LEXECON_DATABASE_URL") or os.getenv("DATABASE_URL")

    if db_url:
        # Convert postgres:// to postgresql+asyncpg:// for async
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return db_url

    # Default PostgreSQL
    pg_host = os.getenv("PGHOST", "localhost")
    pg_port = os.getenv("PGPORT", "5432")
    pg_user = os.getenv("PGUSER", "lexecon")
    pg_password = os.getenv("PGPASSWORD", "lexecon")
    pg_db = os.getenv("PGDATABASE", "lexecon")

    if os.getenv("LEXECON_USE_POSTGRESQL") == "true":
        return f"postgresql+asyncpg://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}"

    # Fallback to SQLite
    data_dir = os.getenv("LEXECON_DATA_DIR", ".")
    return f"sqlite+aiosqlite:///{data_dir}/lexecon.db"


def create_async_engine_with_pool(url: str):
    """Create async engine with connection pooling."""
    pool_size = int(os.getenv("LEXECON_DB_POOL_SIZE", "20"))
    max_overflow = int(os.getenv("LEXECON_DB_MAX_OVERFLOW", "30"))
    pool_timeout = int(os.getenv("LEXECON_DB_POOL_TIMEOUT", "30"))
    pool_recycle = int(os.getenv("LEXECON_DB_POOL_RECYCLE", "3600"))

    # SQLite doesn't support connection pooling well
    if "sqlite" in url:
        return create_async_engine(
            url,
            echo=False,
            connect_args={"check_same_thread": False},
        )

    # PostgreSQL with connection pooling
    return create_async_engine(
        url,
        echo=False,
        poolclass=AsyncAdaptedQueuePool,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=pool_timeout,
        pool_recycle=pool_recycle,
        pool_pre_ping=True,  # Test connections before using
    )


async def init_async_db():
    """Initialize async database (create tables)."""
    global _engine, _async_session_maker

    if _engine is None:
        db_url = get_database_url()
        _engine = create_async_engine_with_pool(db_url)
        _async_session_maker = async_sessionmaker(
            _engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Create tables
        async with _engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)


def get_async_session_maker() -> async_sessionmaker:
    """Get async session maker (initialize if needed)."""
    global _async_session_maker
    if _async_session_maker is None:
        import asyncio
        asyncio.run(init_async_db())
    return _async_session_maker


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session."""
    session_maker = get_async_session_maker()
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# For sync compatibility (current code)
def get_sync_engine():
    """Get synchronous engine for legacy code."""
    from sqlalchemy import create_engine

    db_url = get_database_url()

    # Convert async URL to sync URL
    if "+asyncpg" in db_url:
        sync_url = db_url.replace("+asyncpg", "")
    elif "+aiosqlite" in db_url:
        sync_url = db_url.replace("+aiosqlite", "")
    else:
        sync_url = db_url

    return create_engine(sync_url, echo=False)
