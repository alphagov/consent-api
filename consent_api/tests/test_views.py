"""Tests of view functions."""
import pytest
from flask import json
from flask import url_for

from consent_api.models import CookieConsent
from consent_api.models import UserConsent
from consent_api.models import generate_uid

pytestmark = [pytest.mark.integration]


def test_index_page(client, db_session):
    """Check the index page loads."""
    assert client.get(url_for("home")).status_code == 200


def test_get_consent_no_uid(client):
    """Test getting consent status with a null user ID."""
    response = client.get(url_for("get_consent"))
    assert response.status_code == 200
    assert len(response.json["uid"]) == 22
    assert response.json["status"] is None


def test_get_consent_with_uid(client, db_session):
    """Test getting consent status for a user with no consent status."""
    uid = "test-uid"
    response = client.get(url_for("get_consent", uid=uid))
    assert response.status_code == 200
    assert response.json["uid"] == uid
    assert response.json["status"] is None


def test_get_consent_with_existing_record(client, db_session):
    """Test getting consent status for a user with an existing status record."""
    existing = UserConsent(uid=generate_uid(), consent=CookieConsent.ACCEPT_ALL.json)
    db_session.add(existing)
    db_session.commit()
    response = client.get(url_for("get_consent", uid=existing.uid))
    assert response.status_code == 200
    assert response.json["uid"] == existing.uid
    assert response.json["status"] == existing.consent


@pytest.mark.parametrize(
    "status",
    [
        CookieConsent.REJECT_ALL.json,
        CookieConsent.ACCEPT_ALL.json,
    ],
)
def test_set_consent(client, db_session, status):
    """Test setting a user's consent status multiple times."""
    uid = "test-uid"
    response = client.post(
        url_for("set_consent", uid=uid),
        data={"status": json.dumps(status)},
    )
    assert response.status_code == 204
    assert UserConsent.get(uid).consent == status
