"""Cookie banner POM helper classes."""


class CookieBanner:
    """Convenience wrapper for cookie banner."""

    def __init__(self, banner, browser):
        """Get a wrapped banner instance."""
        self.banner = banner
        self.browser = browser

    @property
    def message(self):
        """Get the cookie banner message."""
        return self.find_by_css(".js-cookie-banner-message").first

    def reject_cookies(self):
        """Click the Reject Cookies button in the banner."""
        self.banner.find_by_css("[data-reject-cookies]").first.click()

    def accept_cookies(self):
        """Click the Accept Cookies button in the banner."""
        self.banner.find_by_css("[data-accept-cookies]").first.click()

    def __getattr__(self, name):
        """Pass through attributes to the banner element."""
        try:
            return getattr(self.banner, name)
        except AttributeError:
            raise


class HasCookieBanner:
    """Mixin for pages with the GOV.UK Design System cookie banner."""

    @property
    def cookie_banner(self):
        """
        Return the first cookie banner on the page.

        (Should be the only one!)
        """
        return CookieBanner(
            self.browser.find_by_css(".govuk-cookie-banner", wait_time=1).first,
            self.browser,
        )
