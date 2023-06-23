"""Fixtures for all tests."""

import json
import os

import httpx
import pytest
from fastapi.testclient import TestClient
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from consent_api import app
from consent_api.database import db_session as _db_session
from consent_api.models import CookieConsent
from consent_api.tests.api import ConsentAPI
from consent_api.tests.pom import fake_govuk
from consent_api.tests.pom import haas as haas_

TEST_DATABASE_URI = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(name="db_session")
async def db_session_fixture():
    """Get database session fixture."""

    def custom_json_serializer(o):
        if isinstance(o, CookieConsent):
            return json.dumps(o.dict())
        return json.dumps(o)

    engine = create_async_engine(
        TEST_DATABASE_URI,
        future=True,
        connect_args={"check_same_thread": False},
        json_serializer=custom_json_serializer,
    )
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    async_session = sessionmaker(engine, class_=AsyncSession)
    session = async_session()

    yield session

    await session.close()


@pytest.fixture(name="app")
def app_fixture(db_session):
    """Get app fixture."""
    app.dependency_overrides[_db_session] = lambda: db_session
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
def client(app):
    """Get test client fixture."""
    client = TestClient(app)
    yield client


@pytest.fixture(scope="session")
def splinter_driver_kwargs(splinter_webdriver, splinter_driver_kwargs):
    """Use chrome with remote webdriver."""
    kwargs = {}
    if splinter_webdriver == "remote":
        kwargs.update(
            {
                "browser": "chrome",
                "options": Options(),
            }
        )
        version = os.getenv("SPLINTER_REMOTE_BROWSER_VERSION", None)
        if version:
            capabilities = kwargs.get("desired_capabilities", {})
            capabilities.update(
                {
                    "browserName": "chrome",
                    "version": version,
                }
            )
            kwargs.update({"desired_capabilities": capabilities})
    return kwargs


def wait_for(self, callback, timeout=10):
    """Wait until the callback returns True or the timeout is reached."""
    WebDriverWait(self.driver, timeout).until(callback)


@pytest.fixture
def browser(browser):
    """Monkeypatch browser instance to add a wait_for convenience method."""
    browser.wait_for = wait_for.__get__(browser)
    return browser


def get_response_ok(url):
    """Return True if a GET request to the URL responds successfully."""
    try:
        return 200 <= httpx.get(url).status_code < 400
    except httpx.ConnectError:
        return False


@pytest.fixture
def server_ready():
    """Return a function to assert a web server is responsive."""
    return get_response_ok


@pytest.fixture
def govuk(browser, server_ready):
    """Return fake GOV.UK homepage object model instance."""
    url = fake_govuk.Homepage.url
    assert server_ready(url), f"Fake GOV.UK homepage not ready at {url}"
    yield fake_govuk.FakeGOVUK(browser)


@pytest.fixture
def consent_api(server_ready):
    """Return consent API client."""
    api = ConsentAPI()
    assert server_ready(api.url), f"Consent API not ready at {api.url}"
    yield api


@pytest.fixture
def haas(browser, server_ready):
    """Return HaaS service."""
    url = haas_.Homepage.url
    assert server_ready(url), f"HaaS not ready at {url}"
    yield haas_.HaaS(browser)
