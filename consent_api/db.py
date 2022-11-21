"""Database functions."""
import sqlite3

from flask import g

from consent_api import app


def get_db():
    """Get a database connection."""
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect("consent.db")
        db.row_factory = sqlite3.Row
        init_db(db)
    return db


@app.teardown_appcontext
def close_connection(_):
    """Close the database connection."""
    if (db := getattr(g, "_database", None)) is not None:
        db.close()


def init_db(db):
    """Ensure the database schema is initialized."""
    with db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS consent (
                uid TEXT UNIQUE NOT NULL,
                status TEXT NOT NULL
            );
            """,
        )
