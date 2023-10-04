"""End to end tests."""

import json
import os

import pytest

from consent_api.models import CookieConsent

pytestmark = [pytest.mark.end_to_end]


def test_single_service(browser, dummy_service, consent_api):
    """Test Consent API integration with dummy service."""
    service = dummy_service(os.getenv("E2E_TEST_DUMMY_SERVICE_1_URL"))

    service.homepage.get()
    browser.driver.delete_all_cookies()

    # with no consent status recorded, we are shown a cookie banner
    homepage = service.homepage.get()
    cookie_banner = homepage.cookie_banner
    assert cookie_banner.visible

    # rejecting cookies dismisses the cookie banner message (the banner is still visible
    # with a confirmation message)
    cookie_banner.reject_cookies()
    assert not cookie_banner.message.visible

    # consent status is stored in a cookie
    policy = browser.cookies.all()["cookies_policy"]
    assert CookieConsent(**json.loads(policy)) == CookieConsent.REJECT_ALL

    # we have been assigned a UID
    browser.wait_for(lambda _: "gov_singleconsent_uid" in browser.cookies.all())
    uid = browser.cookies.all()["gov_singleconsent_uid"]

    # consent status is also recorded in the API associated with the current UID
    assert consent_api.get_consent(uid) == CookieConsent.REJECT_ALL

    # the cookies management page form reflects the consent status
    cookies_page = service.cookies_page.get()
    assert cookies_page.get_settings() == CookieConsent.REJECT_ALL

    # we can modify the consent status via the settings form
    cookies_page.accept(["usage"])
    assert cookies_page.get_settings() == CookieConsent(usage=True)

    # the consent status is updated in the API
    browser.wait_for(
        lambda _: consent_api.get_consent(uid) == CookieConsent(usage=True)
    )

    # now that we have a recorded consent status, the cookie banner is hidden
    homepage = service.homepage.get()
    assert not homepage.cookie_banner.visible


def test_connected_services(browser, dummy_service, consent_api):
    """Test sharing consent across services."""

    urls = [
        os.getenv("E2E_TEST_DUMMY_SERVICE_1_URL"),
        os.getenv("E2E_TEST_DUMMY_SERVICE_2_URL"),
    ]
    services = [dummy_service(url) for url in urls]

    for service in services:
        homepage = service.homepage.get()
        browser.driver.delete_all_cookies()
        homepage.cookie_banner.accept_cookies()
        browser.driver.delete_all_cookies()

    service1, service2 = services

    start_page = service1.start_page.get()
    cookie_banner = start_page.cookie_banner
    assert cookie_banner.visible

    cookie_banner.accept_cookies()
    assert not cookie_banner.message.visible

    policy = browser.cookies.all()["cookies_policy"]
    assert CookieConsent(**json.loads(policy)) == CookieConsent.ACCEPT_ALL

    browser.wait_for(lambda _: "gov_singleconsent_uid" in browser.cookies.all())
    uid = browser.cookies.all()["gov_singleconsent_uid"]
    assert consent_api.get_consent(uid) == CookieConsent.ACCEPT_ALL

    # browse to a different domain/origin
    start_page.start_button.click()

    # consent status has been shared via API, so cookie banner is hidden
    homepage = service2.homepage
    assert not homepage.cookie_banner.visible

    # assert the UID has been carried over
    assert browser.cookies.all()["gov_singleconsent_uid"] == uid
    policy = browser.cookies.all()["cookies_policy"]
    assert CookieConsent(**json.loads(policy)) == CookieConsent.ACCEPT_ALL

    # the cookies management page form reflects the consent status
    cookies_page = service2.cookies_page.get()
    assert cookies_page.get_settings() == CookieConsent.ACCEPT_ALL

    # we can modify the consent status vis the settings form
    cookies_page.reject(["campaigns"])
    rejected_campaigns = CookieConsent(usage=True, settings=True)
    assert cookies_page.get_settings() == rejected_campaigns

    # the consent status is updated in the API
    browser.wait_for(lambda _: consent_api.get_consent(uid) == rejected_campaigns)

    # we can go back to the other domain and see consent status is shared
    service1_cookies_page = service1.cookies_page.get()
    assert service1_cookies_page.get_settings() == CookieConsent(
        usage=True, settings=True
    )

    # TODO follow another cross-origin link which is not Single Consent enabled
    # and show that no UID was passed
