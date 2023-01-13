"""Page Object Models for Hexagrams as a Service."""

import os

from consent_api.tests.pom import Page
from consent_api.tests.pom.cookie_banner import HasCookieBanner
from consent_api.tests.pom.cookie_settings import HasCookiesSettingsForm
from consent_api.tests.pom.fake_govuk import Homepage as GovukHomepage


class StartPage(Page, HasCookieBanner):
    """Fake GOV.UK start page for HaaS."""

    url = f"{GovukHomepage.url}/start/haas"

    @property
    def start_button(self):
        """Get the start button."""
        return self.browser.find_by_css(".govuk-button--start").first


class Homepage(Page, HasCookieBanner):
    """HaaS homepage."""

    url = os.environ.get("E2E_TEST_HAAS_URL", "http://localho.st:8081")


class CookiesPage(Page, HasCookiesSettingsForm):
    """Page Object Model for the HaaS cookies page."""

    url = f"{Homepage.url}/cookies"


class HaaS:
    """Represents the HaaS service."""

    def __init__(self, browser):
        """Get an instance of the service."""
        self.browser = browser

    @property
    def start_page(self):
        """Get the start page."""
        return StartPage(self.browser)

    @property
    def homepage(self):
        """Get the homepage."""
        return Homepage(self.browser)

    @property
    def cookies_page(self):
        """Get the cookies management page."""
        return CookiesPage(self.browser)
