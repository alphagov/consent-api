/* global Consent, Utils */

;(function () {
  function CookieBanner($module) {
    this.$module = $module
  }

  CookieBanner.prototype.init = function () {
    this.cookies_preferences_set =
      Utils.getCookie('cookies_preferences_set') === 'true'
    this.cookies_policy = JSON.parse(Utils.getCookie('cookies_policy', '{}'))

    this.$module.message = this.$module.querySelector(
      '.js-cookie-banner-message'
    )
    this.$module.confirmAccept = this.$module.querySelector(
      '.js-cookie-banner-confirmation-accept'
    )
    this.$module.confirmReject = this.$module.querySelector(
      '.js-cookie-banner-confirmation-reject'
    )

    this.$module.setCookieConsent = this.acceptCookies.bind(this)
    this.$module.showAcceptConfirmation = this.showAcceptConfirmation.bind(this)
    this.$module
      .querySelector('[data-accept-cookies]')
      .addEventListener('click', this.$module.setCookieConsent)
    this.$module.rejectCookieConsent = this.rejectCookies.bind(this)
    this.$module.showRejectConfirmation = this.showRejectConfirmation.bind(this)
    this.$module
      .querySelector('[data-reject-cookies]')
      .addEventListener('click', this.$module.rejectCookieConsent)

    var nodes = this.$module.querySelectorAll('[data-hide-cookie-message]')
    for (var i = 0, length = nodes.length; i < length; i++) {
      nodes[i].addEventListener('click', this.hideBanner.bind(this))
    }

    Consent.onStatusLoaded(
      function (status) {
        this.setCookiesPolicyCookie(status)
        this.hideBanner()
      }.bind(this)
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
      this.$module.hidden = false
      this.$module.confirmAccept.hidden =
        noResponse || !acceptedAdditionalCookies
      this.$module.confirmReject.hidden =
        noResponse || acceptedAdditionalCookies
    }
  }

  CookieBanner.prototype.hideBanner = function () {
    this.$module.hidden = true
  }

  CookieBanner.prototype.acceptCookies = function () {
    this.$module.showAcceptConfirmation()
    this.setCookiesPolicyCookie(Consent.ACCEPT_ALL)
    Consent.setStatus(Consent.ACCEPT_ALL)
  }

  CookieBanner.prototype.setCookiesPolicyCookie = function (cookiesPolicy) {
    Utils.setCookie('cookies_policy', JSON.stringify(cookiesPolicy), {
      days: 365,
    })
    Utils.setCookie('cookies_preferences_set', 'true', { days: 365 })
  }

  CookieBanner.prototype.showAcceptConfirmation = function () {
    this.$module.message.hidden = true
    this.$module.confirmAccept.hidden = false
    this.$module.confirmAccept.focus()
  }

  CookieBanner.prototype.rejectCookies = function () {
    this.$module.showRejectConfirmation()
    this.setCookiesPolicyCookie(Consent.REJECT_ALL)
    Consent.setStatus(Consent.REJECT_ALL)
  }

  CookieBanner.prototype.showRejectConfirmation = function () {
    this.$module.message.hidden = true
    this.$module.confirmReject.hidden = false
    this.$module.confirmReject.focus()
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
