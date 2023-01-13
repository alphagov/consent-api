"""Cookies page POM helper classes."""

from consent_api.models import CookieConsent


class HasCookiesSettingsForm:
    """Mixin for pages following the GOV.UK Design System Cookies page pattern."""

    @property
    def settings(self):
        """Get the settings form."""
        return self.browser.find_by_css("[data-module=cookie-settings]").first

    def get_settings(self):
        """Get form state as a CookieConsent object."""
        checked_radios = self.settings.find_by_css("[type=radio]:checked")
        return CookieConsent(
            **{radio["name"][8:]: radio["value"] == "on" for radio in checked_radios}
        )

    def accept(self, categories):
        """Grant consent to specified categories of cookies."""
        for category in categories:
            self.settings.find_by_css(
                f"[name=cookies-{category}][value=on]",
            ).first.check()
        self.settings.find_by_css("[type=submit]").first.click()

    def reject(self, categories):
        """Deny consent to specified categories of cookies."""
        for category in categories:
            self.settings.find_by_css(
                f"[name=cookies-{category}][value=off]",
            ).first.check()
        self.settings.find_by_css("[type=submit]").first.click()
