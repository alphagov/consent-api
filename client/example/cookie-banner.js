/* global GovSingleConsent, Utils */

;(function () {
  function CookieBanner($component) {
    this.$component = $component
  }

  CookieBanner.prototype.init = function () {
    this.cookies_preferences_set =
      Utils.getCookie('cookies_preferences_set') === 'true'
    this.cookies_policy = JSON.parse(Utils.getCookie('cookies_policy', '{}'))

    this.$component.message = this.$component.querySelector(
      '.js-cookie-banner-message'
    )
    this.$component.confirmAccept = this.$component.querySelector(
      '.js-cookie-banner-confirmation-accept'
    )
    this.$component.confirmReject = this.$component.querySelector(
      '.js-cookie-banner-confirmation-reject'
    )

    this.$component.setCookieConsent = this.acceptCookies.bind(this)
    this.$component.showAcceptConfirmation =
      this.showAcceptConfirmation.bind(this)
    this.$component
      .querySelector('[data-accept-cookies]')
      .addEventListener('click', this.$component.setCookieConsent)
    this.$component.rejectCookieConsent = this.rejectCookies.bind(this)
    this.$component.showRejectConfirmation =
      this.showRejectConfirmation.bind(this)
    this.$component
      .querySelector('[data-reject-cookies]')
      .addEventListener('click', this.$component.rejectCookieConsent)

    var hideBannerBtnNodes = this.$component.querySelectorAll(
      '[data-hide-cookie-message]'
    )
    for (var i = 0, length = hideBannerBtnNodes.length; i < length; i++) {
      hideBannerBtnNodes[i].addEventListener(
        'click',
        this.hideBanner.bind(this)
      )
    }

    function updateConsents(responseStatus) {
      this.setCookiesPolicyCookie(responseStatus)
      this.hideBanner()
    }

    function revokeAllConsents(error) {
      if (error) {
        console.error(error)
      }
      this.setCookiesPolicyCookie(GovSingleConsent.REJECT_ALL)
    }

    GovSingleConsent.init(
      updateConsents.bind(this),
      revokeAllConsents.bind(this)
    )

    this.showBanner()
  }

  CookieBanner.prototype.showBanner = function () {
    var noResponse = Utils.isEmpty(this.cookiesPolicy)
    var acceptedAdditionalCookies = Utils.acceptedAdditionalCookies(
      this.cookies_policy
    )

    if (this.cookies_preferences_set) {
      this.hideBanner()
    } else {
      this.$component.hidden = false
      this.$component.confirmAccept.hidden =
        noResponse || !acceptedAdditionalCookies
      this.$component.confirmReject.hidden =
        noResponse || acceptedAdditionalCookies
    }
  }

  CookieBanner.prototype.hideBanner = function () {
    this.$component.hidden = true
  }

  CookieBanner.prototype.acceptCookies = function () {
    this.$component.showAcceptConfirmation()
    this.setCookiesPolicyCookie(GovSingleConsent.ACCEPT_ALL)
    GovSingleConsent.setStatus(GovSingleConsent.ACCEPT_ALL)
  }

  CookieBanner.prototype.setCookiesPolicyCookie = function (cookiesPolicy) {
    Utils.setCookie('cookies_policy', JSON.stringify(cookiesPolicy), {
      days: 365,
    })
    Utils.setCookie('cookies_preferences_set', 'true', { days: 365 })
  }

  CookieBanner.prototype.showAcceptConfirmation = function () {
    this.$component.message.hidden = true
    this.$component.confirmAccept.hidden = false
    this.$component.confirmAccept.focus()
  }

  CookieBanner.prototype.rejectCookies = function () {
    this.$component.showRejectConfirmation()
    this.setCookiesPolicyCookie(GovSingleConsent.REJECT_ALL)
    GovSingleConsent.setStatus(GovSingleConsent.REJECT_ALL)
  }

  CookieBanner.prototype.showRejectConfirmation = function () {
    this.$component.message.hidden = true
    this.$component.confirmReject.hidden = false
    this.$component.confirmReject.focus()
  }

  window.CookieBanner = CookieBanner

  document.addEventListener('DOMContentLoaded', function () {
    var nodes = document.querySelectorAll(
      '[data-module~="govuk-cookie-banner"]'
    )
    for (var i = 0, length = nodes.length; i < length; i++) {
      new CookieBanner(nodes[i]).init()
    }
  })
})()
