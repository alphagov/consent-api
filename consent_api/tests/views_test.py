import sqlite3
from contextlib import contextmanager
from unittest.mock import patch

import pytest
from flask import json
from flask import url_for

from consent_api.db import init_db
from consent_api.models import ConsentStatus
from consent_api.models import User


@pytest.fixture
def db():
    with patch("consent_api.models.get_db") as get_db:
        db = sqlite3.connect(":memory:")
        db.row_factory = sqlite3.Row
        init_db(db)
        get_db.return_value = db
        yield db
        db.close()


def test_index_page(client):
    assert client.get(url_for("home")).status_code == 200


def test_get_consent_no_uid(client, db):
    response = client.get(url_for("get_consent"))
    assert response.status_code == 200
    assert len(response.json["uid"]) == 22
    assert response.json["status"] is None


def test_get_consent_with_uid(client, db):
    uid = "test-uid"
    response = client.get(url_for("get_consent", uid=uid))
    assert response.status_code == 200
    assert response.json["uid"] == uid
    assert response.json["status"] is None


@pytest.fixture
def existing_consent_record(db):
    @contextmanager
    def _make_record(uid, status):
        db.execute(
            User.SET_CONSENT_STATUS,
            {
                "uid": uid,
                "status": json.dumps(status),
            },
        )
        yield None
        db.execute(User.DELETE_BY_UID, {"uid": uid})

    yield _make_record


def test_get_consent_with_existing_record(existing_consent_record, client):
    uid = "test-uid"
    with existing_consent_record(uid, ConsentStatus.ACCEPT_ALL):
        response = client.get(url_for("get_consent", uid=uid))
        assert response.status_code == 200
        assert response.json["uid"] == uid
        assert all(category for category in response.json["status"].values())


@pytest.mark.parametrize(
    "status",
    [
        ConsentStatus.REJECT_ALL,
        ConsentStatus.ACCEPT_ALL,
    ],
)
def test_set_consent(client, db, status):
    uid = "test-uid"
    url = url_for("set_consent", uid=uid)
    response = client.post(url, data={"status": json.dumps(status)})
    assert response.status_code == 204
    assert User(uid).consent_status == status
