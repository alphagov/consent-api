"""Model classes."""

from __future__ import annotations

import datetime
import json
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import fields
from typing import ClassVar

from fastapi import Form
from sqlalchemy import Column
from sqlalchemy import func
from sqlmodel import JSON
from sqlmodel import Field
from sqlmodel import SQLModel


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

    def __post_init__(self) -> None:
        """Force fields to be bools because FromForm binds strings."""
        for field in fields(self):
            val = getattr(self, field.name)
            if isinstance(val, str):
                setattr(self, field.name, val.lower() == "true")

    def dict(self) -> dict[str, bool]:
        """Return a dict representation."""
        return asdict(self)

    @classmethod
    def parse_json(cls, data: str) -> CookieConsent:
        """Convert a JSON object into a CookieConsent object."""
        return CookieConsent(**json.loads(data))

    @classmethod
    def as_form(
        cls,
        status: str | None = Form(default=None),
        essential: bool | None = Form(default=None),
        settings: bool | None = Form(default=None),
        usage: bool | None = Form(default=None),
        campaigns: bool | None = Form(default=None),
    ) -> CookieConsent:
        """Get an instance from the form data in the request."""
        if status is not None:
            # remain compatible with older clients which send a JSON string
            return cls(**json.loads(status))
        return cls(
            True,  # Cannot reject essential cookies
            settings or False,
            usage or False,
            campaigns or False,
        )


CookieConsent.ACCEPT_ALL = CookieConsent(*([True] * len(fields(CookieConsent))))
CookieConsent.REJECT_ALL = CookieConsent()


class Timestamped(SQLModel):
    """Mixin to add created and update timestamps to models."""

    created_at: datetime.datetime | None = Field(
        sa_column_kwargs={"server_default": func.now()},
    )
    updated_at: datetime.datetime | None = Field(
        sa_column_kwargs={
            "server_default": func.now(),
            "onupdate": func.now(),
        },
    )


class UserConsent(Timestamped, SQLModel, table=True):
    """
    UserConsent represents a user's consent to cookies.

    A User is represented by a unique ID string.
    """

    __tablename__: str = "user_consent"  # type: ignore

    uid: str = Field(primary_key=True)
    consent: CookieConsent = Field(sa_column=Column(JSON))

    def dict(self, **kwargs):
        """Return a dict representation."""
        return {
            "uid": self.uid,
            "status": self.consent,
        }


class Origin(Timestamped, SQLModel, table=True):
    """
    Origin represents a service origin (scheme, domain name, port number).

    The list of known origins is sent to the client to enable automatic decoration of
    links.
    """

    __tablename__: str = "origin"  # type: ignore

    origin: str = Field(primary_key=True)
