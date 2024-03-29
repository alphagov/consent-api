"""Test client for the Consent API."""

import os

import httpx

from consent_api.models import CookieConsent


class ConsentAPI:
    """A running ConsentAPI server instance."""

    def __init__(self):
        """Instantiate client."""
        self.url = os.environ.get("E2E_TEST_CONSENT_API_URL", "http://localho.st:8000")

    def get_consent(self, uid):
        """Retrieve the consent status for the given UID, if it exists."""
        obj = httpx.get(f"{self.url}/api/v1/consent/{uid}").json()
        if obj and obj["status"]:
            return CookieConsent(**obj["status"])
        return None
