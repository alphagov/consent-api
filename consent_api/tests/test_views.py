"""Tests of view functions."""

import pytest

from consent_api.models import CookieConsent
from consent_api.models import UserConsent
from consent_api.routers.consent import get_user_consent
from consent_api.util import generate_uid

pytestmark = [pytest.mark.integration]


def test_index_page(client):
    """Check the index page loads."""
    assert client.get("/").status_code == 200


def consent_api_url(uid) -> str:
    """Build api endpoint path for UID."""
    return f"/api/v1/consent/{uid}"


def test_get_consent_not_found(client):
    """Test getting consent status for a user with no consent status."""
    uid = "test-uid"
    response = client.get(consent_api_url(uid))
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_set_consent(client, db_session):
    """Test setting a new user's consent status."""
    response = client.post(
        consent_api_url(""),
        data=CookieConsent.ACCEPT_ALL.dict(),
    )
    assert response.status_code == 201
    response_json = response.json()
    assert len(response_json["uid"]) == 22
    assert response_json["status"] == CookieConsent.ACCEPT_ALL.dict()

    uc = (await get_user_consent(response_json["uid"], db_session)).first()
    assert uc.consent == CookieConsent.ACCEPT_ALL.dict()


@pytest.mark.asyncio
async def test_get_consent(client, db_session):
    """Test getting consent status for a user with an existing status record."""
    existing = UserConsent(
        uid=generate_uid(),
        consent=CookieConsent.ACCEPT_ALL,
    )
    db_session.add(existing)
    await db_session.commit()
    await db_session.refresh(existing)

    response = client.get(consent_api_url(existing.uid))
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["uid"] == existing.uid
    assert response_json["status"] == existing.consent


@pytest.mark.asyncio
async def test_update_consent(client, db_session):
    """Test updating an existing user's consent status."""
    existing = UserConsent(
        uid=generate_uid(),
        consent=CookieConsent.ACCEPT_ALL,
    )
    db_session.add(existing)
    await db_session.commit()
    await db_session.refresh(existing)

    response = client.post(
        consent_api_url(existing.uid),
        data=CookieConsent.REJECT_ALL.dict(),
    )
    assert response.status_code == 200
    print(f"{response.json()=}")
    response_json = response.json()
    assert response_json["uid"] == existing.uid
    assert response_json["status"] == CookieConsent.REJECT_ALL.dict()

    uc = (await get_user_consent(existing.uid, db_session)).first()
    assert uc.consent == CookieConsent.REJECT_ALL.dict()
