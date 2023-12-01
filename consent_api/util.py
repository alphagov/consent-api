"""Utility functions."""
import base64
import uuid

from sqlalchemy.dialects.postgresql import insert

from consent_api import config
from consent_api.database import db_context
from consent_api.models import Origin


def generate_uid():
    """
    Generate a random 22 character identifier string.

    This is an encoded UUID4, so should have no personally identifying information.
    """
    return base64.urlsafe_b64encode(uuid.uuid4().bytes).decode("utf8").rstrip("=")


async def register_origins_for_e2e_testing():
    if config.ENV in [
        config.Environment.DEVELOPMENT.value,
        config.Environment.TESTING.value,
    ]:
        test_origins = [
            "http://consent-api",
            "http://dummy-service-1",
            "http://dummy-service-2",
        ]
        async with db_context() as db:
            for origin in test_origins:
                async with db.begin():
                    await db.execute(
                        insert(Origin).values(origin=origin).on_conflict_do_nothing()
                    )
                    print("Registered origin:", origin)
