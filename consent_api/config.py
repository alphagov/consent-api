"""Flask app configuration."""
import os

from dotenv import load_dotenv

load_dotenv()
env = os.environ

DEBUG = env.get("DEBUG", True)

SECRET_KEY = env.get("SECRET_KEY", os.urandom(24))

SQLALCHEMY_DATABASE_URI = env.get(
    "DATABASE_URL",
    "postgresql://localhost:5432/consent_api",
)

CONSENT_EXPIRY_DAYS = 7
