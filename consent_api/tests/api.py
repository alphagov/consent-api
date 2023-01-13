"""Test client for the Consent API."""

import os

from consent_api.models import CookieConsent


class ConsentAPI:
    """A running ConsentAPI server instance."""

    def __init__(self, client):
        """Instantiate client."""
        self.client = client
        self.url = os.environ.get("E2E_TEST_CONSENT_API_URL", "http://localho.st:8000")

    def get_consent(self, uid):
        """Retrieve the consent status for the given UID, if it exists."""
        obj = self.client.get(f"{self.url}/consent/{uid}").json
        if obj and obj["status"]:
            return CookieConsent(**obj["status"])
        return None
