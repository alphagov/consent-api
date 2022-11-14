import pytest


@pytest.fixture(autouse=True)
def app():
    from consent_api import app

    return app
