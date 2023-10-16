"""Page Object Models for dummy service."""

from functools import cached_property

from consent_api.tests.pom import Page
from consent_api.tests.pom.cookie_banner import HasCookieBanner
from consent_api.tests.pom.cookie_settings import HasCookiesSettingsForm


class Homepage(Page, HasCookieBanner):
    """Page Object Model for the dummy service homepage."""

    def __init__(self, url, browser):
        """Get an instance of the home page."""
        self.url = f"{url}/dummy-service"
        self.browser = browser


class CookiesPage(Page, HasCookiesSettingsForm):
    """Page Object Model for the dummy service cookies page."""

    def __init__(self, url, browser):
        """Get an instance of the cookies page."""
        self.url = f"{url}/dummy-service/cookies"
        self.browser = browser


class StartPage(Page, HasCookieBanner):
    """Start page for other dummy service."""

    def __init__(self, url, browser):
        """Get an instance of the start page."""
        self.url = f"{url}/dummy-service/start-page"
        self.browser = browser

    @property
    def start_button(self):
        """Get the start button."""
        return self.browser.find_by_css(".button-start").first


class DummyService:
    """Represents a dummy service."""

    def __init__(self, url: str, browser) -> None:
        """Get an instance of the service."""
        self.url = url
        self.browser = browser

    @cached_property
    def homepage(self):
        """Get the homepage."""
        return Homepage(self.url, self.browser)

    @cached_property
    def cookies_page(self):
        """Get the cookies consent management page."""
        return CookiesPage(self.url, self.browser)

    @cached_property
    def start_page(self):
        """Get the start page."""
        return StartPage(self.url, self.browser)
