"""Model classes."""
from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import fields
from datetime import datetime
from datetime import timedelta
from typing import ClassVar

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import DeclarativeMeta

from consent_api import app
from consent_api import db
from consent_api.util import generate_uid


@dataclass
class CookieConsent:
    """CookieConsent represents consent given to 4 categories of cookies."""

    essential: bool = True
    settings: bool = False
    usage: bool = False
    campaigns: bool = False

    # Base datatype for database
    impl = JSON

    # Convenience instances
    ACCEPT_ALL: ClassVar[CookieConsent]
    REJECT_ALL: ClassVar[CookieConsent]

    @property
    def json(self) -> dict[str, bool]:
        """Return a JSON representation."""
        return asdict(self)

    def __html__(self) -> str:
        """Return an HTML representation to enable flask.jsonify."""
        return str(self.json)

    def __str__(self) -> str:
        """Return a string representation."""
        return str(self.json)


CookieConsent.ACCEPT_ALL = CookieConsent(*([True] * len(fields(CookieConsent))))
CookieConsent.REJECT_ALL = CookieConsent()

BaseModel: DeclarativeMeta = db.Model


class Timestamped:
    """Mixin to add created and update timestamps to models."""

    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(
        db.DateTime, default=func.now(), onupdate=func.utc_timestamp()
    )


class UserConsent(Timestamped, BaseModel):
    """
    UserConsent represents a user's consent to cookies.

    A User is represented by a unique ID string.
    """

    uid = db.Column(db.String, primary_key=True)
    consent = db.Column(JSON)

    @property
    def json(self):
        """Return a JSON representation."""
        return {
            "uid": self.uid,
            "status": self.consent,
        }

    def __str__(self):
        """Return a string representation of the consent status."""
        return str(self.json)

    @classmethod
    def get_all(cls) -> list[UserConsent]:
        """List all user consent statuses."""
        return db.session.execute(db.select(UserConsent)).scalars()

    @classmethod
    def bulk_delete(cls, expired=False) -> None:
        """Delete all user consent statuses older than a configured interval."""
        query = db.delete(UserConsent)
        if expired:
            query = query.where(
                UserConsent.updated_at
                < (datetime.now() - timedelta(days=app.config["CONSENT_EXPIRY_DAYS"]))
            )
        db.session.execute(query)
        db.session.commit()

    @classmethod
    def get(cls, uid: str | None = None) -> UserConsent:
        """Get a specified user's consent status."""
        if uid is not None:
            result = db.session.get(UserConsent, uid)
            if result:
                return result
            return UserConsent(uid=uid)
        return UserConsent(uid=generate_uid())

    def update(self, consent: CookieConsent) -> None:
        """Update a specified user's consent status."""
        self.consent = consent.json
        db.session.merge(self)
        db.session.commit()
