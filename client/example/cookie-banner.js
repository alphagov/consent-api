/* global GovSingleConsent */

;(function () {
  function CookieBanner($component) {
    this.$component = $component
  }

  CookieBanner.prototype.init = function () {
    this.$component.hidden = true

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

    function onConsentsUpdated(consents, consentsPreferencesSet, error) {
      if (consentsPreferencesSet) {
        this.hideBanner()
      } else {
        this.showBanner()
      }
      if (error) {
        console.error(error)
      }
    }

    this.singleConsent = new GovSingleConsent(onConsentsUpdated.bind(this))
  }

  CookieBanner.prototype.showBanner = function () {
    var acceptedAdditionalCookies =
      GovSingleConsent.hasConsentedToUsage() ||
      GovSingleConsent.hasConsentedToCampaigns() ||
      GovSingleConsent.hasConsentedToSettings()

    this.$component.hidden = false
    this.$component.confirmAccept.hidden =
      !GovSingleConsent.isConsentPreferencesSet() || !acceptedAdditionalCookies
    this.$component.confirmReject.hidden =
      !GovSingleConsent.isConsentPreferencesSet() || acceptedAdditionalCookies
  }

  CookieBanner.prototype.hideBanner = function () {
    this.$component.hidden = true
  }

  CookieBanner.prototype.acceptCookies = function () {
    this.$component.showAcceptConfirmation()
    this.singleConsent.setConsents(GovSingleConsent.ACCEPT_ALL)
  }

  CookieBanner.prototype.showAcceptConfirmation = function () {
    this.$component.message.hidden = true
    this.$component.confirmAccept.hidden = false
    this.$component.confirmAccept.focus()
  }

  CookieBanner.prototype.rejectCookies = function () {
    this.$component.showRejectConfirmation()
    this.singleConsent.setConsents(GovSingleConsent.REJECT_ALL)
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
