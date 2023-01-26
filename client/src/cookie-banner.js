/* global Consent, Utils */

(function () {
  function CookieBanner ($module) {
    this.$module = $module
  }

  CookieBanner.prototype.init = function () {
    this.cookies_preferences_set = Utils.getCookie('cookies_preferences_set') === 'true'
    this.cookies_policy = JSON.parse(Utils.getCookie('cookies_policy', '{}'))
    console.log('CookieBanner.init: cookies_policy cookie', this.cookies_policy)

    this.$module.message = this.$module.querySelector('.js-cookie-banner-message')
    this.$module.confirmAccept = this.$module.querySelector('.js-cookie-banner-confirmation-accept')
    this.$module.confirmReject = this.$module.querySelector('.js-cookie-banner-confirmation-reject')

    this.$module.setCookieConsent = this.acceptCookies.bind(this)
    this.$module.showAcceptConfirmation = this.showAcceptConfirmation.bind(this)
    this.$module.querySelector('[data-accept-cookies]').addEventListener('click', this.$module.setCookieConsent)
    this.$module.rejectCookieConsent = this.rejectCookies.bind(this)
    this.$module.showRejectConfirmation = this.showRejectConfirmation.bind(this)
    this.$module.querySelector('[data-reject-cookies]').addEventListener('click', this.$module.rejectCookieConsent)

    const nodes = this.$module.querySelectorAll('[data-hide-cookie-message]')
    for (let i = 0, length = nodes.length; i < length; i++) {
      nodes[i].addEventListener('click', this.hideBanner.bind(this))
    }

    Consent.addEventListener('ConsentStatusLoaded', function (status) {
      console.log('CookieBanner.handleConsentStatusLoaded:', status)
      this.setCookiesPolicyCookie(status)
      this.hideBanner()
    }.bind(this))

    this.showBanner()
  }

  CookieBanner.prototype.showBanner = function () {
    const meta = Utils.acceptedAdditionalCookies(this.cookies_policy)

    if (this.cookies_preferences_set) {
      console.log('CookieBanner.showBanner: cookie set')
      this.hideBanner()
    } else {
      console.log('CookieBanner.showBanner: no cookie set, showing banner')
      this.$module.hidden = false
      this.$module.confirmAccept.hidden = !meta.responded || !meta.acceptedAdditionalCookies
      this.$module.confirmReject.hidden = !meta.responded || meta.acceptedAdditionalCookies

      // XXX this prevents the banner from displaying in future whether or not the user
      // interacts with it - is this what we want?
      Utils.setCookie('cookies_preferences_set', 'true', { days: 365 })
    }
  }

  CookieBanner.prototype.hideBanner = function () {
    console.log('CookieBanner.hideBanner')
    this.$module.hidden = true
  }

  CookieBanner.prototype.acceptCookies = function () {
    console.log('CookieBanner.acceptCookies')
    const acceptAll = Utils.ALL_COOKIES
    this.$module.showAcceptConfirmation()
    this.setCookiesPolicyCookie(acceptAll)
    Consent.setStatus(acceptAll)
  }

  CookieBanner.prototype.setCookiesPolicyCookie = function (cookiesPolicy) {
    console.log('CookieBanner.setCookiesPolicyCookie:', cookiesPolicy)
    Utils.setCookie('cookies_policy', JSON.stringify(cookiesPolicy), { days: 365 })
    Utils.setCookie('cookies_preferences_set', 'true', { days: 365 })
  }

  CookieBanner.prototype.showAcceptConfirmation = function () {
    this.$module.message.hidden = true
    this.$module.confirmAccept.hidden = false
    this.$module.confirmAccept.focus()
  }

  CookieBanner.prototype.rejectCookies = function () {
    console.log('CookieBanner.rejectCookies')
    const rejectAll = Utils.ESSENTIAL_COOKIES
    this.$module.showRejectConfirmation()
    this.setCookiesPolicyCookie(rejectAll)
    Consent.setStatus(rejectAll)
  }

  CookieBanner.prototype.showRejectConfirmation = function () {
    this.$module.message.hidden = true
    this.$module.confirmReject.hidden = false
    this.$module.confirmReject.focus()
  }

  window.CookieBanner = CookieBanner

  document.addEventListener('DOMContentLoaded', function () {
    const nodes = document.querySelectorAll('[data-module~="govuk-cookie-banner"]')
    for (let i = 0, length = nodes.length; i < length; i++) {
      new CookieBanner(nodes[i]).init()
    }
  })
})()
