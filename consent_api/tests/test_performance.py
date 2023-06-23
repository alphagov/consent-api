"""Load tests."""

from locust import HttpUser
from locust import task

from consent_api.models import CookieConsent

accept_cookies = CookieConsent.ACCEPT_ALL.dict()


class NewUser(HttpUser):
    """Test a new user accepting cookies."""

    @task
    def give_consent(self):
        """Accept all cookies."""
        self.client.post(
            "/api/v1/consent/",
            data=accept_cookies,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
