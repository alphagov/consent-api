"""Fixtures for all tests."""

import pytest
import sqlalchemy

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
