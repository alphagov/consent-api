"""App configuration."""
import os
from enum import Enum

from dotenv import load_dotenv

from consent_api.config import defaults


class Environment(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    TESTING = "testing"
    PRODUCTION = "production"


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


CONSENT_API_ORIGIN = {
    Environment.TESTING: "http://consent-api",
    Environment.DEVELOPMENT: os.getenv(
        "CONSENT_API_ORIGIN", defaults.DEV.DEFAULT_CONSENT_API_ORIGIN
    ),
    Environment.STAGING: os.getenv(
        "CONSENT_API_ORIGIN", defaults.STAGING.DEFAULT_CONSENT_API_ORIGIN
    ),
    Environment.PRODUCTION: os.getenv(
        "CONSENT_API_ORIGIN", defaults.PROD.DEFAULT_CONSENT_API_ORIGIN
    ),
}.get(Environment(ENV), defaults.DEV.DEFAULT_CONSENT_API_ORIGIN)

CONSENT_API_URL = f"{CONSENT_API_ORIGIN}/api/v1/consent/"


OTHER_SERVICE_ORIGIN = {
    Environment.TESTING: os.getenv(
        "OTHER_SERVICE_ORIGIN_DOCKER", defaults.DEV.DEFAULT_OTHER_SERVICE_ORIGIN
    ),
    Environment.DEVELOPMENT: os.getenv(
        "OTHER_SERVICE_ORIGIN_HOST", defaults.DEV.DEFAULT_OTHER_SERVICE_ORIGIN
    ),
    Environment.STAGING: os.getenv(
        "OTHER_SERVICE_ORIGIN_HOST", defaults.STAGING.DEFAULT_OTHER_SERVICE_ORIGIN
    ),
    Environment.PRODUCTION: defaults.PROD.DEFAULT_OTHER_SERVICE_ORIGIN,
}.get(Environment(ENV), defaults.DEV.DEFAULT_OTHER_SERVICE_ORIGIN)
