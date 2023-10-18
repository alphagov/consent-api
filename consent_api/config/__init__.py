"""App configuration."""
import os

from dotenv import load_dotenv

from consent_api.config import development as dev_config
from consent_api.config import production as prod_config

default_config = dev_config if os.environ.get("ENV") == "development" else prod_config


load_dotenv()
env = os.environ

ENV = env.get("ENV")

DEBUG = env.get("DEBUG", True)

SECRET_KEY = env.get("SECRET_KEY", os.urandom(24))

SQLALCHEMY_DATABASE_URI = env.get(
    "DATABASE_URL",
    "postgresql+asyncpg://localhost:5432/consent_api",
)

CONSENT_EXPIRY_DAYS = 7

ENV = env.get("ENV")


CONSENT_API_URL = os.environ.get(
    "CONSENT_API_URL", default_config.DEFAULT_CONSENT_API_URL
)
