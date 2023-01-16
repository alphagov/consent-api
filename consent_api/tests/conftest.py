"""Fixtures for all tests."""

import pytest
import requests
import sqlalchemy
from selenium.webdriver.chrome.options import Options

from consent_api.tests.api import ConsentAPI
from consent_api.tests.pom import fake_govuk
from consent_api.tests.pom import haas as haas_

TEST_DATABASE_URI = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def app():
    """Get the app instance for use by pytest-flask."""
    from consent_api import app  # noqa

    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = TEST_DATABASE_URI

    ctx = app.app_context()
    ctx.push()

    yield app

    ctx.pop()


@pytest.fixture(scope="session")
def db(app):
    """Create a test database and drop it when tests are done."""
    from consent_api import db as _db

    yield _db


@pytest.fixture
def db_session(db, request):
    """Create a new database session for a test."""
    connection = db.engine.connect()
    transaction = connection.begin()

    session_factory = sqlalchemy.orm.sessionmaker(bind=connection)
    db.session = sqlalchemy.orm.scoped_session(session_factory)

    yield db.session

    transaction.rollback()
    connection.close()
    db.session.remove()


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
    return kwargs


@pytest.fixture
def server_ready():
    """Return a function to assert a web server is responsive."""

    def check(url):
        try:
            return 200 <= requests.get(url).status_code < 400
        except requests.exceptions.ConnectionError:
            return False

    return check


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
