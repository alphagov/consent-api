"""Page Object Models for the fake GOV.UK service."""

import os
from functools import cached_property

from consent_api.tests.pom import Page
from consent_api.tests.pom.cookie_banner import HasCookieBanner
from consent_api.tests.pom.cookie_settings import HasCookiesSettingsForm


class Homepage(Page, HasCookieBanner):
    """Page Object Model for the fake GOV.UK homepage."""

    url = os.environ.get("E2E_TEST_GOVUK_URL", "http://localho.st:8080")


class CookiesPage(Page, HasCookiesSettingsForm):
    """Page Object Model for the fake GOV.UK cookies page."""

    url = f"{Homepage.url}/help/cookies"


class FakeGOVUK:
    """Represents the fake GOVUK service."""

    def __init__(self, browser):
        """Get an instance of the service."""
        self.browser = browser

    @cached_property
    def homepage(self):
        """Get the homepage."""
        return Homepage(self.browser)

    @cached_property
    def cookies_page(self):
        """Get the cookies consent management page."""
        return CookiesPage(self.browser)
