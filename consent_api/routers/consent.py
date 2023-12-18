"""Consent REST API."""
from typing import Annotated

import fastapi
from fastapi import APIRouter
from fastapi import Request
from fastapi import Response
from fastapi_etag import Etag
from sqlalchemy.engine import ScalarResult
from sqlalchemy.sql import functions
from sqlmodel import col
from sqlmodel import select

from consent_api.database import AsyncSession
from consent_api.database import db_context
from consent_api.database import db_session
from consent_api.models import CookieConsent
from consent_api.models import Origin
from consent_api.models import UserConsent
from consent_api.util import generate_uid

consent = APIRouter()


async def origins_etag(request: Request) -> str:
    """Generate an ETag from the last update to the origins table."""
    async with db_context() as db:
        return str(await db.scalar(select(functions.max(Origin.updated_at))))


async def get_known_origins(db: AsyncSession) -> ScalarResult:
    """Fetch known origins from the database."""
    async with db:
        return await db.scalars(select(col(Origin.origin)))


async def get_user_consent(
    uid: str | None,
    db: AsyncSession,
) -> ScalarResult:
    """Fetch consent status from the database."""
    query = select(UserConsent).order_by(
        col(UserConsent.updated_at).desc(),
    )
    if uid is not None:
        query = query.where(UserConsent.uid == uid)
    async with db:
        return await db.scalars(query)


Consent = Annotated[CookieConsent, fastapi.Depends(CookieConsent.as_form)]


@consent.post("/", status_code=201)
async def create_consent_status(
    consent: Consent,
    db: AsyncSession = fastapi.Depends(db_session),
) -> UserConsent:
    """Create a new user with a generated UID and the specified consent status."""
    user_consent = UserConsent(uid=generate_uid(), consent=consent)
    async with db:
        db.add(user_consent)
        await db.commit()
        await db.refresh(user_consent)
    return user_consent


@consent.get("/{uid}")
async def get_consent_status(
    uid: str,
    response: Response,
    db: AsyncSession = fastapi.Depends(db_session),
) -> UserConsent | None:
    """Fetch a specified user's consent status."""
    status = (await get_user_consent(uid, db)).first()
    if not status:
        response.status_code = 404
    return status


@consent.post("/{uid}")
async def set_consent_status(
    uid: str,
    consent: Consent,
    db: AsyncSession = fastapi.Depends(db_session),
) -> UserConsent | None:
    """Update a specified user's consent status."""
    async with db:
        user_consent = (await get_user_consent(uid, db)).first()
        if user_consent:
            user_consent.consent = consent
            await db.merge(user_consent)
            await db.commit()
            return user_consent
    return None


origins = APIRouter()


@origins.get("/", dependencies=[fastapi.Depends(Etag(origins_etag))])
async def known_origins(db: AsyncSession = fastapi.Depends(db_session)) -> list[str]:
    """Fetch the list of known origins."""
    return list(await get_known_origins(db))


router = APIRouter(prefix="/api/v1")
router.include_router(consent, prefix="/consent")
router.include_router(origins, prefix="/origins")
