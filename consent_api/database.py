"""SQLAlchemy database setup."""

from contextlib import asynccontextmanager

from essentials.json import FriendlyEncoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

from consent_api.config import settings

engine = create_async_engine(
    str(settings.sqlalchemy_database_uri),
    json_serializer=FriendlyEncoder().encode,
    pool_size=20,
    max_overflow=20,
)

async_session = sessionmaker(
    engine,
    class_=AsyncSession,
)


async def db_session():
    """Get a database session."""
    async with async_session() as session:
        yield session
        await session.close()


db_context = asynccontextmanager(db_session)
