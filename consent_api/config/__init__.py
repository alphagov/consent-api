"""App configuration."""
import os
from enum import Enum

from dotenv import load_dotenv

from consent_api.config import development as dev_config
from consent_api.config import production as prod_config


class Environment(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    TESTING = "testing"
    PRODUCTION = "production"


load_dotenv()

ENV = os.getenv("ENV", "development")


assert ENV in [member.value for member in Environment], f"Invalid ENV={ENV}"

print(f"ENV={ENV}")


default_config = {
    Environment.DEVELOPMENT: dev_config,
    Environment.STAGING: dev_config,
    Environment.TESTING: dev_config,
    Environment.PRODUCTION: prod_config,
}[Environment(ENV)]


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
        "CONSENT_API_ORIGIN", dev_config.DEFAULT_CONSENT_API_ORIGIN
    ),
    Environment.PRODUCTION: os.getenv(
        "CONSENT_API_ORIGIN", prod_config.DEFAULT_CONSENT_API_ORIGIN
    ),
}.get(Environment(ENV), dev_config.DEFAULT_CONSENT_API_ORIGIN)

CONSENT_API_URL = f"{CONSENT_API_ORIGIN}/api/v1/consent/"


OTHER_SERVICE_ORIGIN = {
    Environment.TESTING: os.getenv(
        "OTHER_SERVICE_ORIGIN_DOCKER", dev_config.DEFAULT_OTHER_SERVICE_ORIGIN
    ),
    Environment.DEVELOPMENT: os.getenv(
        "OTHER_SERVICE_ORIGIN_HOST", dev_config.DEFAULT_OTHER_SERVICE_ORIGIN
    ),
    Environment.PRODUCTION: prod_config.DEFAULT_OTHER_SERVICE_ORIGIN,
}.get(Environment(ENV), dev_config.DEFAULT_OTHER_SERVICE_ORIGIN)
