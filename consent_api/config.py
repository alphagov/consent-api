"""App configuration."""
import os

from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    secret_key: bytes = os.urandom(24)
    sqlalchemy_database_uri: str = Field(
        alias="DATABASE_URL",
        default="postgresql+asyncpg://localhost:5432/consent_api",
    )
    consent_expiry_days: int = 7
    consent_api_origin: str | None = None
    other_service_origin: str | None = None
    flag_fixtures: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class Production(Settings):
    ...


class Staging(Settings):
    consent_api_origin: str = "https://gds-single-consent-staging.app"


class Testing(Settings):
    consent_api_origin: str = "http://consent-api"
    other_service_origin: str = "http://dummy-service-1"


class Development(Settings):
    ...


def get_settings():
    env = os.getenv("ENV", "development")
    try:
        return {subclass.__name__: subclass for subclass in Settings.__subclasses__()}[
            env.title()
        ]()
    except KeyError as err:
        raise ValueError(f"Invalid ENV={env}") from err


settings = get_settings()

print(f"Environment: {settings.__class__.__name__}")
