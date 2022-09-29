from __future__ import annotations
import base64
import sqlite3
import uuid
from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlparse
from dataclasses import asdict, dataclass

from flask import Flask
from flask import g
from flask import json, jsonify
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


@dataclass
class ConsentStatus:
    essential: bool = True
    settings: bool = False
    usage: bool = False
    campaigns: bool = False

    def __html__(self):
        # Enables flask.json.jsonify
        return str(self)

    def __str__(self):
        return str(asdict(self))


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
                status TEXT NOT NULL
            );
            """
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
                    self._status = ConsentStatus(**json.loads(result["status"]))
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
                {"uid": self.uid, "status": json.dumps(asdict(status))},
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
            consent_status=json.dumps(asdict(user.consent_status))
            if user.consent_status
            else None,
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


@app.get("/consent", defaults={"uid": None})
@app.get("/consent/<uid>")
@cross_origin(origins="*")
def get_consent(uid):
    user = User(uid)
    return jsonify(uid=user.uid, status=user.consent_status)


@app.post("/consent/<uid>")
@cross_origin(origins="*")
def set_consent(uid):
    user = User(uid)
    user.consent_status = ConsentStatus(**json.loads(request.form["status"]))
    return "", 204


@app.route("/")
def home() -> str:
    return render_template("index.html", domain=request.host)
