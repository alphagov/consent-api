"""App configuration."""

import os

from dotenv import load_dotenv

from consent_api.config import defaults
from consent_api.config.types import Environment
from consent_api.config import defaults


load_dotenv()

ENV = os.getenv("ENV", "development")


assert ENV in [member.value for member in Environment], f"Invalid ENV={ENV}"

print(f"ENV={ENV}")


DEBUG = os.getenv("DEBUG", True)

SECRET_KEY = os.getenv("SECRET_KEY", os.urandom(24))

SQLALCHEMY_DATABASE_URI = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://localhost:5432/consent_api",
)

CONSENT_EXPIRY_DAYS = 7


default_api_origin = defaults.consent_api_origins.get(
    Environment(ENV), defaults.consent_api_origins[Environment.DEVELOPMENT]
)

default_other_service_origin = defaults.other_service_origins.get(
    Environment(ENV), defaults.other_service_origins[Environment.DEVELOPMENT]
)

CONSENT_API_ORIGIN = os.getenv("CONSENT_API_ORIGIN", default_api_origin)
OTHER_SERVICE_ORIGIN = os.getenv("OTHER_SERVICE_ORIGIN", default_other_service_origin)


FLAG_FIXTURES = os.getenv("FLAG_FIXTURES", False) == "True"
