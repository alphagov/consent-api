from __future__ import annotations

from dataclasses import dataclass, asdict

from flask import json

from consent_api.db import get_db
from consent_api.util import generate_uid


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

    @classmethod
    def get_all(cls) -> list[User]:
        users = []
        with get_db() as db:
            for row in db.execute("SELECT uid, status FROM consent").fetchall():
                user = User(row["uid"])
                user._status = ConsentStatus(**json.loads(row["status"]))
                user._status_cached = True
                users.append(user)
        return users
