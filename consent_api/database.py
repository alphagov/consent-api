"""SQLAlchemy database setup."""

from essentials.json import FriendlyEncoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

from consent_api import config

engine = create_async_engine(
    config.SQLALCHEMY_DATABASE_URI,
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
