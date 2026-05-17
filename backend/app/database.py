"""Async SQLAlchemy engine, session factory, and FastAPI dependency.

Usage in route handlers:
    from app.database import get_db
    from sqlalchemy.ext.asyncio import AsyncSession

    @router.get("/example")
    async def example(db: AsyncSession = Depends(get_db)):
        result = await db.execute(select(User))
        ...
"""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

# ── Engine ─────────────────────────────────────────────────────────────────────
# Railway gives "postgresql://" — rewrite to asyncpg driver for SQLAlchemy async.
_db_url = settings.DATABASE_URL
if _db_url.startswith("postgres://"):
    _db_url = _db_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif _db_url.startswith("postgresql://") and "+asyncpg" not in _db_url:
    _db_url = _db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(
    _db_url,
    echo=settings.DB_ECHO_SQL,
    pool_size=settings.DB_POOL_SIZE,       # base persistent connections (default: 5)
    max_overflow=settings.DB_MAX_OVERFLOW, # burst connections above pool_size (default: 10)
    pool_timeout=30,                        # seconds to wait for a connection before raising
    # Recycle connections every 30 min to avoid stale connections from TCP keepalive issues
    pool_recycle=1800,
    # Validate connections before handing them out from the pool (catches dropped conns)
    pool_pre_ping=True,
)

# ── Session factory ────────────────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    autoflush=False,
)


# ── FastAPI dependency ─────────────────────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session and guarantee it is closed after the request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# Annotated shorthand — use this in route signatures for cleaner code:
#   async def my_route(db: DB) -> ...:
DB = Annotated[AsyncSession, Depends(get_db)]
