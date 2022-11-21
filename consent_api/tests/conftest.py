"""Fixtures for all tests."""
import pytest


@pytest.fixture(autouse=True)
def app():
    """Get the app instance for use by pytest-flask."""
    from consent_api import app

    return app
