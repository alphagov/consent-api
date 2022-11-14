from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from typing import ClassVar

from flask import json

from consent_api.db import get_db
from consent_api.util import generate_uid


@dataclass
class ConsentStatus:
    essential: bool = True
    settings: bool = False
    usage: bool = False
    campaigns: bool = False

    ACCEPT_ALL: ClassVar["ConsentStatus"]
    REJECT_ALL: ClassVar["ConsentStatus"]

    def __html__(self):
        # Enables flask.json.jsonify
        return str(self)

    def __str__(self):
        return str(asdict(self))


ConsentStatus.ACCEPT_ALL = ConsentStatus(True, True, True, True)
ConsentStatus.REJECT_ALL = ConsentStatus(True, False, False, False)


class User:
    DELETE_BY_UID = "DELETE FROM consent WHERE uid = :uid"
    GET_ALL = "SELECT uid, status FROM consent"
    GET_BY_UID = "SELECT status FROM consent WHERE uid = :uid"
    SET_CONSENT_STATUS = (
        "INSERT INTO consent (uid, status) VALUES (:uid, :status) "
        "ON CONFLICT (uid) DO UPDATE SET status = :status"
    )

    def __init__(self, uid: str | None = None):
        self.uid = uid or generate_uid()
        self._status: ConsentStatus | None = None
        self._status_cached = False

    @property
    def consent_status(self) -> ConsentStatus | None:
        if not self._status_cached:
            with get_db() as db:
                result = db.execute(User.GET_BY_UID, {"uid": self.uid}).fetchone()
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
                User.SET_CONSENT_STATUS,
                {"uid": self.uid, "status": json.dumps(status)},
            )
            self._status = status
            self._status_cached = True

    @classmethod
    def get_all(cls) -> list[User]:
        users = []
        with get_db() as db:
            for row in db.execute(User.GET_ALL).fetchall():
                user = User(row["uid"])
                user._status = ConsentStatus(**json.loads(row["status"]))
                user._status_cached = True
                users.append(user)
        return users
