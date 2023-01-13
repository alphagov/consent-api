"""End to end tests."""

import json

import pytest

from consent_api.models import CookieConsent

pytestmark = [pytest.mark.end_to_end]


def test_single_service(browser, govuk, consent_api):
    """Test Consent API integration with fake GOVUK homepage."""
    browser.cookies.delete_all()

    # with no consent status recorded, we are shown a cookie banner
    homepage = govuk.homepage.get()
    cookie_banner = homepage.cookie_banner
    assert cookie_banner.visible

    # we have been assigned a UID, but no consent status is recorded yet
    uid = browser.cookies.all()["uid"]
    assert consent_api.get_consent(uid) is None

    # rejecting cookies dismisses the cookie banner message (the banner is still visible
    # with a confirmation message)
    cookie_banner.reject_cookies()
    assert not cookie_banner.message.visible

    # consent status is stored in a cookie
    policy = browser.cookies.all()["cookies_policy"]
    assert CookieConsent(**json.loads(policy)) == CookieConsent.REJECT_ALL

    # consent status is also recorded in the API associated with the current UID
    assert consent_api.get_consent(uid) == CookieConsent.REJECT_ALL

    # the cookies management page form reflects the consent status
    cookies_page = govuk.cookies_page.get()
    assert cookies_page.get_settings() == CookieConsent.REJECT_ALL

    # we can modify the consent status via the settings form
    cookies_page.accept(["usage"])
    assert cookies_page.get_settings() == CookieConsent(usage=True)

    # the consent status is updated in the API
    assert consent_api.get_consent(uid) == CookieConsent(usage=True)

    # now that we have a recorded consent status, the cookie banner is hidden
    homepage = govuk.homepage.get()
    assert not homepage.cookie_banner.visible


def test_connected_services(browser, govuk, haas, consent_api):
    """Test sharing consent across services."""
    browser.cookies.delete_all()

    start_page = haas.start_page.get()
    cookie_banner = start_page.cookie_banner
    assert cookie_banner.visible

    uid = browser.cookies.all()["uid"]
    assert consent_api.get_consent(uid) is None

    cookie_banner.accept_cookies()
    assert not cookie_banner.message.visible

    policy = browser.cookies.all()["cookies_policy"]
    assert CookieConsent(**json.loads(policy)) == CookieConsent.ACCEPT_ALL

    assert consent_api.get_consent(uid) == CookieConsent.ACCEPT_ALL

    # browse to a different domain/origin
    start_page.start_button.click()

    # consent status has been shared via API, so cookie banner is hidden
    homepage = haas.homepage
    assert not homepage.cookie_banner.visible

    # assert the UID has been carried over
    assert browser.cookies.all()["uid"] == uid
    policy = browser.cookies.all()["cookies_policy"]
    assert CookieConsent(**json.loads(policy)) == CookieConsent.ACCEPT_ALL

    # the cookies management page form reflects the consent status
    cookies_page = haas.cookies_page.get()
    assert cookies_page.get_settings() == CookieConsent.ACCEPT_ALL

    # we can modify the consent status vis the settings form
    cookies_page.reject(["campaigns"])
    assert cookies_page.get_settings() == CookieConsent(usage=True, settings=True)

    # the consent status is updated in the API
    assert consent_api.get_consent(uid) == CookieConsent(usage=True, settings=True)

    # we can go back to the other domain and see consent status is shared
    govuk_cookies_page = govuk.cookies_page.get()
    assert govuk_cookies_page.get_settings() == CookieConsent(usage=True, settings=True)
