from __future__ import annotations
import base64
import sqlite3
import uuid
from datetime import datetime, timedelta
from enum import Enum
from urllib.parse import parse_qs, urlparse

from flask import Flask
from flask import g
from flask import jsonify
from flask import make_response
from flask import render_template
from flask import request
from flask.wrappers import Response
from flask_cors import cross_origin


app = Flask(__name__)

ALLOWED_ORIGINS = [
    "https://consent-api.herokuapp.com",
    "https://consent-api-2.herokuapp.com",
]


class ConsentStatus(Enum):
    NO_CONSENT = 0
    CONSENT = 1

    def __html__(self):
        # Enables flask.json.jsonify
        return self.name


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect("consent.db")
        db.row_factory = sqlite3.Row
        init_db(db)
    return db


@app.teardown_appcontext
def close_connection(_):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def init_db(db):
    with db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS consent (
                uid TEXT UNIQUE NOT NULL,
                status INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS consent_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                value TEXT UNIQUE ON CONFLICT IGNORE NOT NULL
            );
            """
        )
        db.executemany(
            "INSERT OR IGNORE INTO consent_status (value, id) VALUES (?, ?)",
            [(status.name, status.value) for status in ConsentStatus],
        )


def generate_uid():
    return base64.urlsafe_b64encode(uuid.uuid4().bytes).decode("utf8").rstrip("=")


class User:
    def __init__(self, uid: str | None = None):
        self.uid = uid or generate_uid()
        self._status: ConsentStatus | None = None
        self._status_cached = False

    @property
    def consent_status(self) -> ConsentStatus | None:
        if not self._status_cached:
            with get_db() as db:
                result = db.execute(
                    "SELECT status FROM consent WHERE uid = :uid",
                    {"uid": self.uid},
                ).fetchone()
                if result:
                    self._status = ConsentStatus(result["status"])
                self._status_cached = True
        return self._status

    @consent_status.setter
    def consent_status(self, status: ConsentStatus) -> None:
        if self._status_cached and status == self._status:
            return

        with get_db() as db:
            db.execute(
                "INSERT INTO consent (uid, status) VALUES (:uid, :status) "
                "ON CONFLICT (uid) DO UPDATE SET status = :status",
                {"uid": self.uid, "status": status.value},
            )
            self._status = status
            self._status_cached = True


def get_uid_from_referrer(referrer: str) -> str | None:
    return parse_qs(urlparse(referrer).query).get("uid", [None])[0]


@app.route("/consent.js")
def consent_js() -> Response:
    user = User(
        request.args.get(
            "uid",
            get_uid_from_referrer(request.referrer) or request.cookies.get("uid"),
        ),
    )
    response = make_response(
        render_template(
            "consent.js",
            api_url="https://consent-api.herokuapp.com/consent",
            uid=user.uid,
            consent_status=user.consent_status.name if user.consent_status else None,
        ),
    )
    response.headers["Content-Type"] = "application/javascript"
    response.set_cookie(
        "uid",
        value=user.uid,
        secure=True,
        httponly=True,
        samesite="None",
        expires=datetime.now() + timedelta(days=7),
    )
    return response


@app.get("/consent/<uid>")
@cross_origin(origins=ALLOWED_ORIGINS)
def get_consent(uid):
    user = User(uid)
    return jsonify(status=user.consent_status)


@app.post("/consent/<uid>")
@cross_origin(origins=ALLOWED_ORIGINS)
def set_consent(uid):
    user = User(uid)
    user.consent_status = ConsentStatus[request.form["status"]]
    return "", 204


@app.route("/")
def home() -> str:
    return render_template("index.html", domain=request.host)
