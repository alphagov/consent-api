"""Consent REST API."""

from typing import Annotated
from typing import Optional

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Response
from sqlalchemy.engine import ScalarResult
from sqlmodel import col
from sqlmodel import select

from consent_api.database import AsyncSession
from consent_api.database import db_session
from consent_api.models import CookieConsent
from consent_api.models import UserConsent
from consent_api.util import generate_uid

router = APIRouter(
    prefix="/api/v1/consent",
)
get = router.get
post = router.post


async def get_user_consent(
    uid: Optional[str],
    db: AsyncSession = Depends(db_session),
) -> ScalarResult:
    """Fetch consent status from the database."""
    query = select(UserConsent).order_by(
        col(UserConsent.updated_at).desc(),
    )
    if uid is not None:
        query = query.where(UserConsent.uid == uid)
    async with db:
        return await db.scalars(query)


@get("/")
async def get_all_consent_statuses(
    db: AsyncSession = Depends(db_session),
) -> list[UserConsent]:
    """Get all consent statuses."""
    return list(await get_user_consent(None, db))


Consent = Annotated[CookieConsent, Depends(CookieConsent.as_form)]


@post("/", status_code=201)
async def create_consent_status(
    response: Response,
    consent: Consent,
    db: AsyncSession = Depends(db_session),
) -> UserConsent:
    """Create a new user with a generated UID and the specified consent status."""
    user_consent = UserConsent(uid=generate_uid(), consent=consent)
    async with db:
        db.add(user_consent)
        await db.commit()
        await db.refresh(user_consent)
    return user_consent


@get("/{uid}")
async def get_consent_status(
    uid: str,
    response: Response,
    db: AsyncSession = Depends(db_session),
) -> Optional[UserConsent]:
    """Fetch a specified user's consent status."""
    status = (await get_user_consent(uid, db)).first()
    if not status:
        response.status_code = 404
    return status


@post("/{uid}")
async def set_consent_status(
    uid: str,
    consent: Consent,
    db: AsyncSession = Depends(db_session),
) -> Optional[UserConsent]:
    """Update a specified user's consent status."""
    async with db:
        user_consent = (await get_user_consent(uid, db)).first()
        if user_consent:
            user_consent.consent = consent
            await db.merge(user_consent)
            await db.commit()
            return user_consent
    return None
