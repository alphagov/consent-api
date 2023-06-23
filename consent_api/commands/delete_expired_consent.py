"""CLI Command to delete expired consent statuses from the database."""

import asyncio
from datetime import datetime
from datetime import timedelta

from sqlalchemy.sql.expression import delete
from sqlmodel import col

from consent_api import config
from consent_api.database import engine
from consent_api.models import UserConsent


async def delete_expired_consent():
    """Delete expired consent statuses from the database."""
    async with engine.connect() as conn:
        await conn.execute(
            delete(UserConsent).where(
                col(UserConsent.updated_at)
                < (datetime.now() - timedelta(days=config.CONSENT_EXPIRY_DAYS)),
            )
        )
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(delete_expired_consent())
