"""Page Object Models."""


class Page:
    """Page Object Model base class."""

    url: str

    def __init__(self, browser):
        """Instantiate POM."""
        self.browser = browser

    def get(self):
        """Browse to page."""
        self.browser.visit(self.url)
        return self
