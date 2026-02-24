"""Async SQLAlchemy engine, session factory, and FastAPI dependency."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

# Create async engine; echo=False in production
engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)

# Session factory – sessions do not expire on commit so attributes remain
# accessible after the transaction ends
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a database session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
