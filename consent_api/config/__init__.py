"""App configuration."""
import os
from enum import Enum

from dotenv import load_dotenv

from consent_api.config import development as dev_config
from consent_api.config import production as prod_config


class Env(Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


load_dotenv()
env = os.environ

ENV = env.get("ENV")

default_config = dev_config if os.environ.get("ENV") == Env.DEVELOPMENT else prod_config


DEBUG = env.get("DEBUG", True)

SECRET_KEY = env.get("SECRET_KEY", os.urandom(24))

SQLALCHEMY_DATABASE_URI = env.get(
    "DATABASE_URL",
    "postgresql+asyncpg://localhost:5432/consent_api",
)

CONSENT_EXPIRY_DAYS = 7


CONSENT_API_ORIGIN = {
    Env.TESTING: "http://consent-api",
    Env.DEVELOPMENT: env.get(
        "CONSENT_API_ORIGIN", dev_config.DEFAULT_CONSENT_API_ORIGIN
    ),
    Env.PRODUCTION: env.get(
        "CONSENT_API_ORIGIN", prod_config.DEFAULT_CONSENT_API_ORIGIN
    ),
}.get(Env(ENV), dev_config.DEFAULT_CONSENT_API_ORIGIN)

CONSENT_API_URL = f"{CONSENT_API_ORIGIN}/api/v1/consent/"


OTHER_SERVICE_ORIGIN = {
    Env.TESTING: env.get(
        "OTHER_SERVICE_ORIGIN_DOCKER", dev_config.DEFAULT_OTHER_SERVICE_ORIGIN
    ),
    Env.DEVELOPMENT: env.get(
        "OTHER_SERVICE_ORIGIN_HOST", dev_config.DEFAULT_OTHER_SERVICE_ORIGIN
    ),
    Env.PRODUCTION: prod_config.DEFAULT_OTHER_SERVICE_ORIGIN,
}.get(Env(ENV), dev_config.DEFAULT_OTHER_SERVICE_ORIGIN)
